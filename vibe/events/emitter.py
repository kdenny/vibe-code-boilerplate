"""The run-telemetry emitter: start, terminate, reconcile.

:class:`RunTelemetry` is the one object the CLI and (future) Python runner use
to record a run's lifecycle. It guarantees the schema invariant — **exactly one
start and exactly one completion per run** — across three different ways a run
can end:

1. The run finishes and explicitly calls :meth:`complete` (the happy path, and
   what the shell/CLI loop does).
2. The hosting Python process is killed with ``SIGTERM``/``SIGINT`` or exits —
   :meth:`session` registers signal + ``atexit`` handlers that record a terminal
   outcome on the way down (best-effort, for graceful kills).
3. The process dies hard (``SIGKILL``, OOM, power loss) and *nothing* runs —
   the durable ``running`` record is left orphaned, and a later
   :meth:`reconcile` sweep synthesizes the missing completion.

(1) and (3) are the durable backstops; (2) is the best-effort fast path. The
combination is why a failed run is never lost.
"""

from __future__ import annotations

import atexit
import logging
import os
import signal
import socket
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from vibe.events import store
from vibe.events.schema import (
    EventKind,
    Outcome,
    RunEvent,
    new_run_id,
    utc_now,
    utc_now_iso,
)
from vibe.events.sinks import EventSink, LinearSink, LogSink
from vibe.events.store import RunRecord
from vibe.trackers import TrackerBase

logger = logging.getLogger("vibe.events")

# When a running record declares no timeout of its own, reconcile treats it as
# crashed/stuck after this many seconds with no terminal and no live process.
DEFAULT_RECONCILE_DEADLINE_SECONDS = 2 * 60 * 60  # 2h, > the 90-min autopilot hold


class RunTelemetry:
    """Records run lifecycle events to durable storage and out to sinks."""

    def __init__(
        self,
        sinks: Sequence[EventSink] | None = None,
        base_path: Path | None = None,
    ) -> None:
        # A LogSink is always present so a run is never recorded *nowhere*.
        self._sinks: list[EventSink] = list(sinks) if sinks is not None else [LogSink()]
        self._base_path = base_path

    # -- emission ---------------------------------------------------------

    def start(
        self,
        *,
        ticket: str | None,
        pr_url: str | None = None,
        engine: str | None = None,
        run_id: str | None = None,
        timeout_seconds: float | None = None,
        set_current: bool = True,
    ) -> RunRecord:
        """Begin a run: write the durable record, then emit the start event."""
        run_id = run_id or new_run_id()
        record = store.make_running_record(
            run_id=run_id,
            ticket=ticket,
            pr_url=pr_url,
            engine=engine,
            host=socket.gethostname(),
            pid=os.getpid(),
            timeout_seconds=timeout_seconds,
        )
        # Write-ahead: the record exists on disk *before* we try any sink, so a
        # crash during emission still leaves a recoverable running record.
        store.write_record(record, self._base_path)
        if set_current:
            store.set_current_run(run_id, self._base_path)

        event = RunEvent(
            run_id=run_id,
            kind=EventKind.START,
            timestamp=record.started_at,
            ticket=ticket,
            pr_url=pr_url,
            engine=engine,
            host=record.host,
            pid=record.pid,
        )
        self._record_and_dispatch(record, event)
        return record

    def complete(
        self,
        *,
        outcome: Outcome,
        run_id: str | None = None,
        reason: str | None = None,
    ) -> RunRecord:
        """Terminate a run with *outcome*. Idempotent: a second call is a no-op.

        This idempotency is what enforces "exactly one completion event" when
        the explicit path, a signal handler, and ``atexit`` could all fire for
        the same run.
        """
        run_id = self._resolve_run_id(run_id)
        record = store.load_record(run_id, self._base_path)
        if record is None:
            raise KeyError(f"no run record for run_id {run_id!r}")
        if record.is_terminal:
            # Already finished — preserve the original terminal outcome.
            logger.debug("run %s already terminal (%s); ignoring", run_id, record.outcome)
            return record

        ended_at = utc_now_iso()
        record.state = store.STATE_TERMINAL
        record.outcome = outcome.value
        record.reason = reason
        record.ended_at = ended_at

        event = RunEvent(
            run_id=run_id,
            kind=EventKind.COMPLETION,
            timestamp=ended_at,
            ticket=record.ticket,
            pr_url=record.pr_url,
            engine=record.engine,
            outcome=outcome,
            reason=reason,
            host=record.host,
            pid=record.pid,
            duration_seconds=_elapsed_seconds(record.started_at, ended_at),
        )
        self._record_and_dispatch(record, event)
        store.clear_current_run(run_id, self._base_path)
        return record

    def heartbeat(self, run_id: str | None = None) -> None:
        """Refresh a running record's liveness timestamp (no event emitted)."""
        run_id = self._resolve_run_id(run_id)
        record = store.load_record(run_id, self._base_path)
        if record is None or record.is_terminal:
            return
        record.heartbeat_at = utc_now_iso()
        store.write_record(record, self._base_path)

    # -- recovery ---------------------------------------------------------

    def reconcile(
        self,
        *,
        deadline_seconds: float | None = None,
        now: datetime | None = None,
    ) -> list[RunRecord]:
        """Synthesize terminal outcomes for orphaned ``running`` records.

        This is the backstop for hard kills: a run that crashed left a record
        stuck in ``running``. For each such record we decide — process gone, or
        ceiling exceeded — and emit the missing completion so the failure
        becomes visible. Returns the records it repaired.
        """
        now = now or utc_now()
        repaired: list[RunRecord] = []
        for record in store.iter_records(self._base_path):
            if record.is_terminal:
                continue
            verdict = self._stale_verdict(record, now, deadline_seconds)
            if verdict is None:
                continue
            outcome, reason = verdict
            repaired.append(self.complete(run_id=record.run_id, outcome=outcome, reason=reason))
        return repaired

    def _stale_verdict(
        self,
        record: RunRecord,
        now: datetime,
        deadline_seconds: float | None,
    ) -> tuple[Outcome, str] | None:
        """Classify a ``running`` record as crashed, timed-out, or still alive."""
        # Definitive evidence first: a dead PID on this host means a crash,
        # regardless of any clock-based deadline.
        if record.host == socket.gethostname() and record.pid and not _pid_alive(record.pid):
            return Outcome.FAILURE, "process is gone — no terminal outcome was recorded (crash)"

        deadline = record.timeout_seconds or deadline_seconds or DEFAULT_RECONCILE_DEADLINE_SECONDS
        age = _elapsed_seconds(record.started_at, now.isoformat())
        if age is not None and age > deadline:
            return (
                Outcome.TIMEOUT,
                f"exceeded the {deadline:.0f}s ceiling with no terminal outcome",
            )
        return None

    # -- session (long-lived Python host) ---------------------------------

    @contextmanager
    def session(
        self,
        *,
        ticket: str | None,
        pr_url: str | None = None,
        engine: str | None = None,
        timeout_seconds: float | None = None,
    ) -> Iterator[RunRecord]:
        """Wrap a run in a Python process, terminating it on exit *or* signal.

        On normal block exit → ``success``. On a raised ``TimeoutError`` →
        ``timeout``. On any other exception → ``failure``. On ``SIGTERM``/
        ``SIGINT`` or interpreter exit → ``failure`` via best-effort handlers.

        Note: signal handlers can only be installed from the main thread; in a
        worker thread the handler registration is skipped and the durable
        record + :meth:`reconcile` remain the safety net.
        """
        record = self.start(
            ticket=ticket, pr_url=pr_url, engine=engine, timeout_seconds=timeout_seconds
        )
        run_id = record.run_id
        finalized = {"done": False}

        def _finalize(outcome: Outcome, reason: str | None) -> None:
            if finalized["done"]:
                return
            finalized["done"] = True
            self.complete(run_id=run_id, outcome=outcome, reason=reason)

        previous_handlers: dict[int, object] = {}

        def _on_signal(signum: int, _frame: object) -> None:
            name = signal.Signals(signum).name
            _finalize(Outcome.FAILURE, f"terminated by signal {name}")
            # Restore and re-raise so the process dies as it normally would.
            signal.signal(signum, previous_handlers.get(signum, signal.SIG_DFL))  # type: ignore[arg-type]
            os.kill(os.getpid(), signum)

        installed_signals = _install_signal_handlers(_on_signal, previous_handlers)
        atexit.register(_finalize, Outcome.FAILURE, "process exited without a terminal outcome")
        try:
            yield record
            _finalize(Outcome.SUCCESS, None)
        except TimeoutError as exc:
            _finalize(Outcome.TIMEOUT, str(exc) or "timed out")
            raise
        except BaseException as exc:
            _finalize(Outcome.FAILURE, f"{type(exc).__name__}: {exc}")
            raise
        finally:
            atexit.unregister(_finalize)
            for signum in installed_signals:
                signal.signal(signum, previous_handlers.get(signum, signal.SIG_DFL))  # type: ignore[arg-type]

    # -- internals --------------------------------------------------------

    def _record_and_dispatch(self, record: RunRecord, event: RunEvent) -> None:
        """Append the event to the record, persist, then fan out to sinks."""
        record.append_event(event)
        store.write_record(record, self._base_path)
        for sink in self._sinks:
            try:
                sink.emit(event)
            except Exception as exc:  # noqa: BLE001 - one sink must not break others
                # Loud, never silent: telemetry delivery failed, but the run and
                # the durable record are intact. Surface it; don't propagate.
                logger.warning("event sink %r failed for run %s: %s", sink.name, record.run_id, exc)

    def _resolve_run_id(self, run_id: str | None) -> str:
        if run_id:
            return run_id
        current = store.get_current_run(self._base_path)
        if current is None:
            raise ValueError("no run_id given and no current run is recorded")
        return current


def _install_signal_handlers(handler: object, previous: dict[int, object]) -> list[int]:
    """Install *handler* for SIGTERM/SIGINT, remembering prior handlers.

    Returns the signals successfully installed. Outside the main thread Python
    raises ``ValueError``; we degrade to the reconcile backstop instead.
    """
    installed: list[int] = []
    for signum in (signal.SIGTERM, signal.SIGINT):
        try:
            previous[signum] = signal.signal(signum, handler)  # type: ignore[arg-type]
            installed.append(signum)
        except (ValueError, OSError):
            continue
    return installed


def _pid_alive(pid: int) -> bool:
    """True if *pid* names a live process on this host."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Exists but owned by another user — still alive.
        return True
    return True


def _elapsed_seconds(start_iso: str, end_iso: str) -> float | None:
    """Whole seconds between two ISO-8601 timestamps, or ``None`` if unparseable."""
    try:
        start = datetime.fromisoformat(start_iso)
        end = datetime.fromisoformat(end_iso)
    except ValueError:
        return None
    return (end - start).total_seconds()


def default_telemetry(base_path: Path | None = None) -> RunTelemetry:
    """Build a telemetry emitter wired to the LogSink and, if available, Linear.

    The LinearSink is added only when a Linear tracker can be constructed from
    config/env — so the module runs in isolation (LogSink only) with no Linear
    credentials, and lights up Linear-visible failures automatically when they
    exist.
    """
    sinks: list[EventSink] = [LogSink()]
    tracker = _build_linear_tracker()
    if tracker is not None:
        sinks.append(LinearSink(tracker))
    return RunTelemetry(sinks=sinks, base_path=base_path)


def _build_linear_tracker() -> TrackerBase | None:
    """Best-effort Linear tracker from config or ``LINEAR_*`` env, else ``None``.

    Linear is the only supported tracker during the revamp, so the events
    module depends just on its public surface rather than the CLI's broader
    tracker factory.
    """
    try:
        from vibe.config import load_config
        from vibe.trackers import LinearTracker
    except Exception:  # noqa: BLE001 - telemetry never blocks on tracker wiring
        return None

    team_id: str | None = None
    try:
        config = load_config()
        tracker_cfg = config.get("tracker", {})
        if tracker_cfg.get("type") not in (None, "linear"):
            return None
        team_id = tracker_cfg.get("config", {}).get("team_id")
    except Exception:  # noqa: BLE001 - missing/invalid config is fine; fall through to env
        team_id = None

    team_id = team_id or os.environ.get("LINEAR_TEAM_ID")
    if not os.environ.get("LINEAR_API_KEY"):
        return None
    try:
        return LinearTracker(team_id=team_id)
    except Exception:  # noqa: BLE001 - never let tracker construction break a run
        return None
