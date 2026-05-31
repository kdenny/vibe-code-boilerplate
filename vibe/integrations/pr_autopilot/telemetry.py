"""Structured PR Autopilot run telemetry.

The future engine can wrap each run in :class:`PRAutopilotRunTelemetry` to emit a
start event and exactly one terminal outcome event. Terminal failures are
designed to be posted back to Linear so humans can debug without a secondary
observability system.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import Any, Literal, Protocol, TypeVar
from uuid import uuid4

from vibe.trackers.base import TrackerBase

DEFAULT_TELEMETRY_LOG_PATH = Path(".vibe") / "pr-autopilot-telemetry.jsonl"
SCHEMA_VERSION = "pr-autopilot.telemetry.v1"

TelemetryEventName = Literal[
    "pr_autopilot.run.started",
    "pr_autopilot.run.completed",
    "pr_autopilot.run.failed",
    "pr_autopilot.run.timed_out",
]
TelemetryOutcome = Literal["started", "success", "failure", "timeout"]
JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
RunCallableResult = TypeVar("RunCallableResult")


@dataclass(frozen=True)
class PRAutopilotTelemetryEvent:
    """Serializable telemetry emitted for one PR Autopilot run transition."""

    run_id: str
    event: TelemetryEventName
    outcome: TelemetryOutcome
    terminal: bool
    timestamp: str
    ticket_id: str | None = None
    pr_url: str | None = None
    branch: str | None = None
    phase: str | None = None
    message: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    duration_ms: int | None = None
    error_type: str | None = None
    error_message: str | None = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, JsonValue]:
        """Return the stable JSON shape used by sinks and future reporting."""

        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "event": self.event,
            "outcome": self.outcome,
            "terminal": self.terminal,
            "timestamp": self.timestamp,
            "ticket_id": self.ticket_id,
            "pr_url": self.pr_url,
            "branch": self.branch,
            "phase": self.phase,
            "message": self.message,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_ms": self.duration_ms,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "metadata": dict(self.metadata),
        }

    def to_json(self) -> str:
        """Render the event as deterministic JSON for logs and comments."""

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


class PRAutopilotTelemetrySink(Protocol):
    """Destination for PR Autopilot telemetry events."""

    def emit(self, event: PRAutopilotTelemetryEvent) -> None:
        """Persist or forward *event*."""


@dataclass
class JsonlTelemetrySink:
    """Append every telemetry event to a local JSONL file."""

    path: Path = DEFAULT_TELEMETRY_LOG_PATH

    def emit(self, event: PRAutopilotTelemetryEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(event.to_json() + "\n")


@dataclass
class LinearTelemetrySink:
    """Post terminal PR Autopilot failures to the associated Linear issue."""

    tracker: TrackerBase
    ticket_id: str
    include_successes: bool = False

    def emit(self, event: PRAutopilotTelemetryEvent) -> None:
        if not event.terminal:
            return
        if event.outcome == "success" and not self.include_successes:
            return
        self.tracker.comment_ticket(self.ticket_id, format_linear_telemetry_comment(event))


@dataclass
class CompositeTelemetrySink:
    """Fan out telemetry while keeping secondary sinks from blocking primary ones."""

    sinks: Sequence[PRAutopilotTelemetrySink]
    raise_on_error: bool = False
    errors: list[Exception] = field(default_factory=list)

    def emit(self, event: PRAutopilotTelemetryEvent) -> None:
        for sink in self.sinks:
            try:
                sink.emit(event)
            except Exception as exc:  # noqa: PERF203 - each sink must be isolated.
                self.errors.append(exc)
                if self.raise_on_error:
                    raise


class PRAutopilotRunTelemetry:
    """Emit a start event and one terminal event for a PR Autopilot run.

    Definitions:
    - success: the wrapped run exits normally, or ``complete()`` is called.
    - failure: the run raises or ``fail()`` is called before a terminal event.
    - timeout: ``timeout()`` is called, or a timeout exception escapes the run.
    - completion: any terminal outcome event; exactly one is emitted per run.
    """

    def __init__(
        self,
        sink: PRAutopilotTelemetrySink,
        *,
        run_id: str | None = None,
        ticket_id: str | None = None,
        pr_url: str | None = None,
        branch: str | None = None,
        phase: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        now: Callable[[], datetime] | None = None,
        monotonic_clock: Callable[[], float] | None = None,
    ) -> None:
        self._sink = sink
        self.run_id = run_id or str(uuid4())
        self.ticket_id = ticket_id
        self.pr_url = pr_url
        self.branch = branch
        self.phase = phase
        self.metadata = _json_safe_mapping(metadata or {})
        self._now = now or (lambda: datetime.now(UTC))
        self._monotonic = monotonic_clock or monotonic
        self._started_at: datetime | None = None
        self._started_monotonic: float | None = None
        self._start_event: PRAutopilotTelemetryEvent | None = None
        self._terminal_event: PRAutopilotTelemetryEvent | None = None

    @property
    def start_event(self) -> PRAutopilotTelemetryEvent | None:
        return self._start_event

    @property
    def terminal_event(self) -> PRAutopilotTelemetryEvent | None:
        return self._terminal_event

    def __enter__(self) -> PRAutopilotRunTelemetry:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object,
    ) -> Literal[False]:
        if self._terminal_event is None:
            if exc is None:
                self.complete()
            elif _is_timeout(exc):
                self.timeout(error=exc)
            else:
                self.fail(error=exc)
        return False

    def start(
        self, *, message: str | None = None, phase: str | None = None
    ) -> PRAutopilotTelemetryEvent:
        """Emit the run start event once."""

        if self._start_event is not None:
            return self._start_event

        self._started_at = self._now()
        self._started_monotonic = self._monotonic()
        self._start_event = self._event(
            event="pr_autopilot.run.started",
            outcome="started",
            terminal=False,
            timestamp=self._started_at,
            phase=phase,
            message=message,
        )
        self._sink.emit(self._start_event)
        return self._start_event

    def complete(
        self,
        *,
        message: str | None = None,
        phase: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> PRAutopilotTelemetryEvent:
        """Emit the successful terminal outcome if one has not already been emitted."""

        return self._terminal(
            event="pr_autopilot.run.completed",
            outcome="success",
            message=message,
            phase=phase,
            metadata=metadata,
        )

    def fail(
        self,
        *,
        error: BaseException | None = None,
        message: str | None = None,
        phase: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> PRAutopilotTelemetryEvent:
        """Emit the failed terminal outcome if one has not already been emitted."""

        return self._terminal(
            event="pr_autopilot.run.failed",
            outcome="failure",
            error=error,
            message=message,
            phase=phase,
            metadata=metadata,
        )

    def timeout(
        self,
        *,
        error: BaseException | None = None,
        message: str | None = None,
        phase: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> PRAutopilotTelemetryEvent:
        """Emit the timeout terminal outcome if one has not already been emitted."""

        return self._terminal(
            event="pr_autopilot.run.timed_out",
            outcome="timeout",
            error=error,
            message=message,
            phase=phase,
            metadata=metadata,
        )

    def _terminal(
        self,
        *,
        event: TelemetryEventName,
        outcome: Literal["success", "failure", "timeout"],
        error: BaseException | None = None,
        message: str | None = None,
        phase: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> PRAutopilotTelemetryEvent:
        if self._terminal_event is not None:
            return self._terminal_event
        self.start()

        ended_at = self._now()
        duration_ms = None
        if self._started_monotonic is not None:
            duration_ms = max(0, round((self._monotonic() - self._started_monotonic) * 1000))

        error_type, error_message = _error_fields(error)
        merged_metadata: MutableMapping[str, JsonValue] = dict(self.metadata)
        if metadata:
            merged_metadata.update(_json_safe_mapping(metadata))

        self._terminal_event = self._event(
            event=event,
            outcome=outcome,
            terminal=True,
            timestamp=ended_at,
            ended_at=ended_at,
            duration_ms=duration_ms,
            error_type=error_type,
            error_message=error_message,
            phase=phase,
            message=message,
            metadata=merged_metadata,
        )
        self._sink.emit(self._terminal_event)
        return self._terminal_event

    def _event(
        self,
        *,
        event: TelemetryEventName,
        outcome: TelemetryOutcome,
        terminal: bool,
        timestamp: datetime,
        ended_at: datetime | None = None,
        duration_ms: int | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
        phase: str | None = None,
        message: str | None = None,
        metadata: Mapping[str, JsonValue] | None = None,
    ) -> PRAutopilotTelemetryEvent:
        started_at = self._started_at.isoformat() if self._started_at else None
        return PRAutopilotTelemetryEvent(
            run_id=self.run_id,
            event=event,
            outcome=outcome,
            terminal=terminal,
            timestamp=timestamp.isoformat(),
            ticket_id=self.ticket_id,
            pr_url=self.pr_url,
            branch=self.branch,
            phase=phase or self.phase,
            message=message,
            started_at=started_at,
            ended_at=ended_at.isoformat() if ended_at else None,
            duration_ms=duration_ms,
            error_type=error_type,
            error_message=error_message,
            metadata=metadata or self.metadata,
        )


def run_with_pr_autopilot_telemetry(
    run: Callable[[], RunCallableResult],
    sink: PRAutopilotTelemetrySink,
    **context: Any,
) -> RunCallableResult:
    """Run a callable inside the telemetry guard and return its result."""

    with PRAutopilotRunTelemetry(sink, **context):
        return run()


def format_linear_telemetry_comment(event: PRAutopilotTelemetryEvent) -> str:
    """Format a terminal event as a Linear-readable incident note."""

    status = {
        "success": "completed",
        "failure": "failed",
        "timeout": "timed out",
        "started": "started",
    }[event.outcome]
    lines = [
        f"### PR Autopilot run {status}",
        "",
        f"- run_id: `{event.run_id}`",
        f"- outcome: `{event.outcome}`",
        f"- event: `{event.event}`",
        f"- terminal: `{str(event.terminal).lower()}`",
    ]
    if event.phase:
        lines.append(f"- phase: `{event.phase}`")
    if event.duration_ms is not None:
        lines.append(f"- duration_ms: `{event.duration_ms}`")
    if event.pr_url:
        lines.append(f"- pr_url: {event.pr_url}")
    if event.branch:
        lines.append(f"- branch: `{event.branch}`")
    if event.error_type or event.error_message:
        lines.append(f"- error: `{event.error_type or 'Error'}`: {event.error_message or ''}")
    if event.message:
        lines.append(f"- message: {event.message}")
    lines.extend(["", "```json", json.dumps(event.to_dict(), indent=2, sort_keys=True), "```"])
    return "\n".join(lines)


def _is_timeout(error: BaseException) -> bool:
    return isinstance(error, TimeoutError | subprocess.TimeoutExpired)


def _error_fields(error: BaseException | None) -> tuple[str | None, str | None]:
    if error is None:
        return None, None
    return type(error).__name__, str(error)


def _json_safe_mapping(metadata: Mapping[str, Any]) -> dict[str, JsonValue]:
    return {str(key): _json_safe(value) for key, value in metadata.items()}


def _json_safe(value: Any) -> JsonValue:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_json_safe(item) for item in value]
    return str(value)
