"""Unit tests for the RunTelemetry emitter.

The emitter is the contract holder: exactly one start + one completion per run,
durable through crashes and timeouts. These tests pin that behavior with a
fake sink (the sink interface is the I/O boundary) and an injected ``now`` for
the reconcile clock.
"""

from __future__ import annotations

import os
import socket
from datetime import timedelta
from pathlib import Path

import pytest

from vibe.events import store
from vibe.events.emitter import RunTelemetry
from vibe.events.schema import EventKind, Outcome, RunEvent, utc_now
from vibe.events.sinks import EventSink


class FakeSink(EventSink):
    """Records every event; can be told to raise to test sink isolation."""

    def __init__(self, name: str = "fake", raise_on_emit: bool = False) -> None:
        self._name = name
        self.events: list[RunEvent] = []
        self._raise = raise_on_emit

    @property
    def name(self) -> str:
        return self._name

    def emit(self, event: RunEvent) -> None:
        if self._raise:
            raise RuntimeError("sink boom")
        self.events.append(event)


def _telemetry(tmp_path: Path, *sinks: EventSink) -> tuple[RunTelemetry, FakeSink]:
    sink = FakeSink()
    all_sinks = list(sinks) or [sink]
    return RunTelemetry(sinks=all_sinks, base_path=tmp_path), sink


class TestStart:
    def test_writes_running_record_and_emits_start(self, tmp_path: Path) -> None:
        telemetry, sink = _telemetry(tmp_path)
        record = telemetry.start(ticket="VIBE-146", pr_url="https://pr/1", engine="claude")

        on_disk = store.load_record(record.run_id, tmp_path)
        assert on_disk is not None
        assert on_disk.state == store.STATE_RUNNING
        assert [e.kind for e in sink.events] == [EventKind.START]
        assert sink.events[0].ticket == "VIBE-146"

    def test_sets_current_run_by_default(self, tmp_path: Path) -> None:
        telemetry, _ = _telemetry(tmp_path)
        record = telemetry.start(ticket="VIBE-146")
        assert store.get_current_run(tmp_path) == record.run_id

    def test_no_current_flag_skips_pointer(self, tmp_path: Path) -> None:
        telemetry, _ = _telemetry(tmp_path)
        telemetry.start(ticket="VIBE-146", set_current=False)
        assert store.get_current_run(tmp_path) is None


class TestComplete:
    def test_marks_terminal_and_emits_completion(self, tmp_path: Path) -> None:
        telemetry, sink = _telemetry(tmp_path)
        record = telemetry.start(ticket="VIBE-146")
        telemetry.complete(run_id=record.run_id, outcome=Outcome.SUCCESS)

        on_disk = store.load_record(record.run_id, tmp_path)
        assert on_disk is not None and on_disk.is_terminal
        assert on_disk.outcome == "success"
        assert [e.kind for e in sink.events] == [EventKind.START, EventKind.COMPLETION]
        assert sink.events[-1].duration_seconds is not None

    def test_is_idempotent_preserving_first_outcome(self, tmp_path: Path) -> None:
        telemetry, sink = _telemetry(tmp_path)
        record = telemetry.start(ticket="VIBE-146")
        telemetry.complete(run_id=record.run_id, outcome=Outcome.FAILURE, reason="boom")
        telemetry.complete(run_id=record.run_id, outcome=Outcome.SUCCESS)  # must be a no-op

        on_disk = store.load_record(record.run_id, tmp_path)
        assert on_disk is not None and on_disk.outcome == "failure"
        completions = [e for e in sink.events if e.kind is EventKind.COMPLETION]
        assert len(completions) == 1  # exactly one terminal event, ever

    def test_uses_current_run_when_id_omitted(self, tmp_path: Path) -> None:
        telemetry, _ = _telemetry(tmp_path)
        telemetry.start(ticket="VIBE-146")
        telemetry.complete(outcome=Outcome.SUCCESS)
        # Pointer cleared once the run it named terminated.
        assert store.get_current_run(tmp_path) is None

    def test_unknown_run_raises(self, tmp_path: Path) -> None:
        telemetry, _ = _telemetry(tmp_path)
        with pytest.raises(KeyError):
            telemetry.complete(run_id="missing", outcome=Outcome.SUCCESS)

    def test_no_run_and_no_current_raises(self, tmp_path: Path) -> None:
        telemetry, _ = _telemetry(tmp_path)
        with pytest.raises(ValueError, match="no current run"):
            telemetry.complete(outcome=Outcome.SUCCESS)


class TestSinkIsolation:
    def test_failing_sink_does_not_break_others_or_the_run(self, tmp_path: Path) -> None:
        good = FakeSink("good")
        bad = FakeSink("bad", raise_on_emit=True)
        telemetry = RunTelemetry(sinks=[bad, good], base_path=tmp_path)

        record = telemetry.start(ticket="VIBE-146")  # must not raise
        # The good sink still received the event, and the record persisted.
        assert good.events[0].run_id == record.run_id
        assert store.load_record(record.run_id, tmp_path) is not None


def _age_running_record(
    telemetry: RunTelemetry,
    tmp_path: Path,
    *,
    run_id: str,
    age_seconds: float,
    pid: int,
    host: str,
    timeout_seconds: float | None,
) -> None:
    """Plant a running record that started ``age_seconds`` ago (crash simulation)."""
    started = (utc_now() - timedelta(seconds=age_seconds)).isoformat()
    record = store.RunRecord(
        run_id=run_id,
        state=store.STATE_RUNNING,
        started_at=started,
        ticket="VIBE-146",
        host=host,
        pid=pid,
        timeout_seconds=timeout_seconds,
    )
    store.write_record(record, tmp_path)


class TestReconcile:
    def test_dead_process_becomes_failure(self, tmp_path: Path, monkeypatch) -> None:
        telemetry, sink = _telemetry(tmp_path)
        _age_running_record(
            telemetry,
            tmp_path,
            run_id="crashed",
            age_seconds=10,
            pid=999_999,
            host=socket.gethostname(),
            timeout_seconds=None,
        )
        monkeypatch.setattr("vibe.events.emitter._pid_alive", lambda _pid: False)

        repaired = telemetry.reconcile()
        assert [r.run_id for r in repaired] == ["crashed"]
        assert repaired[0].outcome == "failure"
        assert "crash" in (repaired[0].reason or "")

    def test_exceeded_ceiling_becomes_timeout(self, tmp_path: Path) -> None:
        telemetry, _ = _telemetry(tmp_path)
        # Live pid (this process) so the crash branch is skipped; aged past its
        # declared timeout so it classifies as a timeout.
        _age_running_record(
            telemetry,
            tmp_path,
            run_id="slow",
            age_seconds=600,
            pid=os.getpid(),
            host=socket.gethostname(),
            timeout_seconds=300,
        )
        repaired = telemetry.reconcile()
        assert [r.run_id for r in repaired] == ["slow"]
        assert repaired[0].outcome == "timeout"

    def test_healthy_running_record_untouched(self, tmp_path: Path) -> None:
        telemetry, _ = _telemetry(tmp_path)
        telemetry.start(ticket="VIBE-146", timeout_seconds=3600)  # fresh, live, in-window
        assert telemetry.reconcile() == []

    def test_terminal_records_are_ignored(self, tmp_path: Path) -> None:
        telemetry, _ = _telemetry(tmp_path)
        record = telemetry.start(ticket="VIBE-146")
        telemetry.complete(run_id=record.run_id, outcome=Outcome.SUCCESS)
        assert telemetry.reconcile() == []

    def test_other_host_pid_not_treated_as_crash(self, tmp_path: Path) -> None:
        # A pid on a *different* host can't be liveness-checked here; only the
        # timeout ceiling applies. Below the ceiling -> left alone.
        telemetry, _ = _telemetry(tmp_path)
        _age_running_record(
            telemetry,
            tmp_path,
            run_id="remote",
            age_seconds=10,
            pid=999_999,
            host="some-other-host",
            timeout_seconds=300,
        )
        assert telemetry.reconcile() == []


class TestSession:
    def test_success_path_emits_success(self, tmp_path: Path) -> None:
        telemetry, sink = _telemetry(tmp_path)
        with telemetry.session(ticket="VIBE-146") as record:
            run_id = record.run_id
        on_disk = store.load_record(run_id, tmp_path)
        assert on_disk is not None and on_disk.outcome == "success"

    def test_exception_path_emits_failure_and_reraises(self, tmp_path: Path) -> None:
        telemetry, _ = _telemetry(tmp_path)
        with pytest.raises(RuntimeError, match="kaboom"):
            with telemetry.session(ticket="VIBE-146") as record:
                run_id = record.run_id
                raise RuntimeError("kaboom")
        on_disk = store.load_record(run_id, tmp_path)
        assert on_disk is not None
        assert on_disk.outcome == "failure"
        assert "kaboom" in (on_disk.reason or "")

    def test_timeout_error_maps_to_timeout_outcome(self, tmp_path: Path) -> None:
        telemetry, _ = _telemetry(tmp_path)
        with pytest.raises(TimeoutError):
            with telemetry.session(ticket="VIBE-146") as record:
                run_id = record.run_id
                raise TimeoutError("held 90m")
        on_disk = store.load_record(run_id, tmp_path)
        assert on_disk is not None and on_disk.outcome == "timeout"

    def test_session_emits_exactly_one_terminal(self, tmp_path: Path) -> None:
        telemetry, sink = _telemetry(tmp_path)
        with telemetry.session(ticket="VIBE-146"):
            pass
        completions = [e for e in sink.events if e.kind is EventKind.COMPLETION]
        assert len(completions) == 1
