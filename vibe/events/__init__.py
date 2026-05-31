"""Run-lifecycle telemetry for PR Autopilot (start / completion, crash-safe).

This package emits a ``start`` event and exactly one terminal ``completion``
event per run, persists a durable write-ahead record so failures survive
crashes and timeouts, and surfaces failures on the run's Linear ticket. It is
the foundational event-emission seam underneath usage reporting (VIBE-131) and
readiness checks (VIBE-142).

See :mod:`vibe.events.schema` for the event/outcome definitions and the
single-start/single-completion invariant.
"""

from vibe.events.emitter import RunTelemetry, default_telemetry
from vibe.events.schema import EventKind, Outcome, RunEvent, new_run_id
from vibe.events.sinks import EventSink, LinearSink, LogSink
from vibe.events.store import RunRecord

__all__ = [
    "EventKind",
    "Outcome",
    "RunEvent",
    "RunRecord",
    "EventSink",
    "LogSink",
    "LinearSink",
    "RunTelemetry",
    "default_telemetry",
    "new_run_id",
]
