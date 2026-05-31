"""Tests for PR Autopilot run telemetry."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from vibe.integrations.pr_autopilot import (
    CompositeTelemetrySink,
    JsonlTelemetrySink,
    LinearTelemetrySink,
    PRAutopilotRunTelemetry,
    PRAutopilotTelemetryEvent,
    format_linear_telemetry_comment,
    run_with_pr_autopilot_telemetry,
)


def test_context_manager_emits_start_and_success_terminal_event() -> None:
    sink = _RecordingSink()

    with PRAutopilotRunTelemetry(
        sink,
        run_id="run-1",
        ticket_id="VIBE-146",
        pr_url="https://github.com/example/repo/pull/1",
        branch="cursor/vibe-146",
        phase="watch",
        metadata={"attempt": 1},
        now=_clock(),
        monotonic_clock=_monotonic(10.0, 10.25),
    ):
        pass

    assert [event.event for event in sink.events] == [
        "pr_autopilot.run.started",
        "pr_autopilot.run.completed",
    ]
    terminal_events = [event for event in sink.events if event.terminal]
    assert len(terminal_events) == 1
    terminal = terminal_events[0]
    assert terminal.outcome == "success"
    assert terminal.duration_ms == 250
    assert terminal.to_dict()["metadata"] == {"attempt": 1}


def test_crash_reraises_and_emits_linear_visible_failure() -> None:
    recording_sink = _RecordingSink()
    tracker = _FakeTracker()
    sink = CompositeTelemetrySink(
        [recording_sink, LinearTelemetrySink(tracker=tracker, ticket_id="VIBE-146")]
    )

    with pytest.raises(RuntimeError, match="boom"):
        with PRAutopilotRunTelemetry(
            sink,
            run_id="run-crash",
            ticket_id="VIBE-146",
            phase="ci",
            now=_clock(),
            monotonic_clock=_monotonic(20.0, 20.5),
        ):
            raise RuntimeError("boom")

    assert [event.outcome for event in recording_sink.events] == ["started", "failure"]
    failure = recording_sink.events[-1]
    assert failure.error_type == "RuntimeError"
    assert failure.error_message == "boom"
    assert tracker.comments == [("VIBE-146", format_linear_telemetry_comment(failure))]
    assert "PR Autopilot run failed" in tracker.comments[0][1]
    assert '"outcome": "failure"' in tracker.comments[0][1]


def test_timeout_exception_emits_timeout_terminal_event() -> None:
    sink = _RecordingSink()

    with pytest.raises(TimeoutError, match="budget exhausted"):
        with PRAutopilotRunTelemetry(
            sink,
            run_id="run-timeout",
            now=_clock(),
            monotonic_clock=_monotonic(30.0, 90.0),
        ):
            raise TimeoutError("budget exhausted")

    assert [event.event for event in sink.events] == [
        "pr_autopilot.run.started",
        "pr_autopilot.run.timed_out",
    ]
    timeout = sink.events[-1]
    assert timeout.terminal is True
    assert timeout.outcome == "timeout"
    assert timeout.error_type == "TimeoutError"
    assert timeout.duration_ms == 60000


def test_explicit_terminal_event_prevents_duplicate_on_later_exception() -> None:
    sink = _RecordingSink()

    with pytest.raises(RuntimeError, match="later crash"):
        with PRAutopilotRunTelemetry(sink, run_id="run-once", now=_clock()) as telemetry:
            emitted = telemetry.fail(message="ci failed", metadata={"check": "ruff"})
            raise RuntimeError("later crash")

    terminal_events = [event for event in sink.events if event.terminal]
    assert terminal_events == [emitted]
    assert [event.outcome for event in sink.events] == ["started", "failure"]
    assert terminal_events[0].message == "ci failed"
    assert terminal_events[0].metadata["check"] == "ruff"


def test_jsonl_sink_persists_structured_events(tmp_path: Path) -> None:
    sink = JsonlTelemetrySink(tmp_path / "telemetry.jsonl")

    with PRAutopilotRunTelemetry(sink, run_id="run-jsonl", now=_clock()):
        pass

    rows = [
        json.loads(line)
        for line in (tmp_path / "telemetry.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [row["event"] for row in rows] == [
        "pr_autopilot.run.started",
        "pr_autopilot.run.completed",
    ]
    assert rows[0]["schema_version"] == "pr-autopilot.telemetry.v1"
    assert rows[1]["terminal"] is True


def test_linear_sink_only_comments_terminal_failures_by_default() -> None:
    tracker = _FakeTracker()
    sink = LinearTelemetrySink(tracker=tracker, ticket_id="VIBE-146")
    started = PRAutopilotTelemetryEvent(
        run_id="run-linear",
        event="pr_autopilot.run.started",
        outcome="started",
        terminal=False,
        timestamp="2026-05-31T00:00:00+00:00",
    )
    completed = PRAutopilotTelemetryEvent(
        run_id="run-linear",
        event="pr_autopilot.run.completed",
        outcome="success",
        terminal=True,
        timestamp="2026-05-31T00:01:00+00:00",
    )
    failed = PRAutopilotTelemetryEvent(
        run_id="run-linear",
        event="pr_autopilot.run.failed",
        outcome="failure",
        terminal=True,
        timestamp="2026-05-31T00:02:00+00:00",
        error_type="ValueError",
        error_message="bad state",
    )

    sink.emit(started)
    sink.emit(completed)
    sink.emit(failed)

    assert len(tracker.comments) == 1
    assert tracker.comments[0][0] == "VIBE-146"
    assert "bad state" in tracker.comments[0][1]


def test_run_with_pr_autopilot_telemetry_returns_callable_result() -> None:
    sink = _RecordingSink()

    result = run_with_pr_autopilot_telemetry(lambda: "done", sink, run_id="run-helper")

    assert result == "done"
    assert [event.outcome for event in sink.events] == ["started", "success"]


class _RecordingSink:
    def __init__(self) -> None:
        self.events: list[PRAutopilotTelemetryEvent] = []

    def emit(self, event: PRAutopilotTelemetryEvent) -> None:
        self.events.append(event)


class _FakeTracker:
    def __init__(self) -> None:
        self.comments: list[tuple[str, str]] = []

    def comment_ticket(self, ticket_id: str, body: str) -> None:
        self.comments.append((ticket_id, body))


def _clock() -> Any:
    start = datetime(2026, 5, 31, 2, 5, tzinfo=UTC)
    ticks = iter(start + timedelta(seconds=offset) for offset in range(20))
    return lambda: next(ticks)


def _monotonic(*values: float) -> Any:
    ticks = iter(values)
    return lambda: next(ticks)
