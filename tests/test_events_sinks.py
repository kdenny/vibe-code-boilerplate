"""Unit tests for telemetry sinks (the event delivery boundary)."""

from __future__ import annotations

import json
import logging

from vibe.events.schema import EventKind, Outcome, RunEvent, utc_now_iso
from vibe.events.sinks import LinearSink, LogSink, format_comment
from vibe.trackers.base import TrackerBase


class _StubTracker(TrackerBase):
    """Minimal tracker capturing comment calls (the sink's collaborator)."""

    def __init__(self) -> None:
        self.comments: list[tuple[str, str]] = []

    @property
    def name(self) -> str:
        return "stub"

    def authenticate(self, **kwargs: object) -> bool:
        return True

    def get_ticket(self, ticket_id: str):  # type: ignore[override]
        return None

    def list_tickets(self, *args: object, **kwargs: object):  # type: ignore[override]
        return []

    def create_ticket(self, *args: object, **kwargs: object):  # type: ignore[override]
        raise NotImplementedError

    def update_ticket(self, *args: object, **kwargs: object):  # type: ignore[override]
        raise NotImplementedError

    def validate_config(self) -> tuple[bool, list[str]]:
        return True, []

    def comment_ticket(self, ticket_id: str, body: str) -> None:
        self.comments.append((ticket_id, body))


def _start(ticket: str | None = "VIBE-146") -> RunEvent:
    return RunEvent(run_id="r1", kind=EventKind.START, timestamp=utc_now_iso(), ticket=ticket)


def _completion(outcome: Outcome, ticket: str | None = "VIBE-146", **kw: object) -> RunEvent:
    return RunEvent(
        run_id="r1",
        kind=EventKind.COMPLETION,
        timestamp=utc_now_iso(),
        ticket=ticket,
        outcome=outcome,
        **kw,  # type: ignore[arg-type]
    )


class TestLogSink:
    def test_emits_structured_json_line(self, caplog) -> None:
        sink = LogSink(level=logging.INFO)
        with caplog.at_level(logging.INFO, logger="vibe.events"):
            sink.emit(_completion(Outcome.SUCCESS))
        # The logged message carries a parseable JSON payload of the event.
        record = caplog.records[-1]
        payload = json.loads(record.getMessage().split("vibe.run_event ", 1)[1])
        assert payload["outcome"] == "success"
        assert payload["run_id"] == "r1"


class TestLinearSink:
    def test_comments_on_the_run_ticket(self) -> None:
        tracker = _StubTracker()
        LinearSink(tracker).emit(_completion(Outcome.FAILURE, reason="CI red"))
        assert len(tracker.comments) == 1
        ticket_id, body = tracker.comments[0]
        assert ticket_id == "VIBE-146"
        assert "failed" in body.lower()

    def test_skips_events_without_a_ticket(self) -> None:
        tracker = _StubTracker()
        LinearSink(tracker).emit(_completion(Outcome.SUCCESS, ticket=None))
        assert tracker.comments == []


class TestFormatComment:
    def test_start_comment_mentions_started(self) -> None:
        body = format_comment(_start())
        assert "started" in body.lower()
        assert "r1" in body

    def test_failure_comment_includes_reason(self) -> None:
        body = format_comment(_completion(Outcome.FAILURE, reason="conflict"))
        assert "conflict" in body

    def test_timeout_comment_reads_as_timeout(self) -> None:
        body = format_comment(_completion(Outcome.TIMEOUT))
        assert "timed out" in body.lower()
