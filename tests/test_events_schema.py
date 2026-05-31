"""Unit tests for the run-telemetry event schema."""

from __future__ import annotations

import pytest

from vibe.events.schema import (
    EventKind,
    Outcome,
    RunEvent,
    new_run_id,
    utc_now_iso,
)


class TestOutcome:
    def test_success_is_not_failure(self) -> None:
        assert Outcome.SUCCESS.is_failure is False

    @pytest.mark.parametrize("outcome", [Outcome.FAILURE, Outcome.TIMEOUT])
    def test_non_success_outcomes_are_failures(self, outcome: Outcome) -> None:
        assert outcome.is_failure is True


class TestRunId:
    def test_is_filename_safe_and_sortable(self) -> None:
        run_id = new_run_id()
        # No characters that would be awkward in a filename.
        assert "/" not in run_id and ":" not in run_id
        # Timestamp prefix then an 8-char hex suffix.
        stamp, _, suffix = run_id.partition("-")
        assert stamp.endswith("Z")
        assert len(suffix) == 8

    def test_ids_are_unique(self) -> None:
        assert new_run_id() != new_run_id()


class TestRunEventInvariants:
    def test_completion_requires_outcome(self) -> None:
        with pytest.raises(ValueError, match="completion events require an outcome"):
            RunEvent(run_id="r1", kind=EventKind.COMPLETION, timestamp=utc_now_iso())

    def test_start_rejects_outcome(self) -> None:
        with pytest.raises(ValueError, match="must not carry an outcome"):
            RunEvent(
                run_id="r1",
                kind=EventKind.START,
                timestamp=utc_now_iso(),
                outcome=Outcome.SUCCESS,
            )

    def test_start_event_is_not_terminal(self) -> None:
        event = RunEvent(run_id="r1", kind=EventKind.START, timestamp=utc_now_iso())
        assert event.is_terminal is False

    def test_completion_event_is_terminal(self) -> None:
        event = RunEvent(
            run_id="r1",
            kind=EventKind.COMPLETION,
            timestamp=utc_now_iso(),
            outcome=Outcome.FAILURE,
        )
        assert event.is_terminal is True


class TestSerialization:
    def test_round_trip_preserves_fields(self) -> None:
        original = RunEvent(
            run_id="r1",
            kind=EventKind.COMPLETION,
            timestamp="2026-05-30T14:00:00+00:00",
            ticket="VIBE-146",
            pr_url="https://example/pr/1",
            engine="claude",
            outcome=Outcome.TIMEOUT,
            reason="held too long",
            host="runner-1",
            pid=4242,
            duration_seconds=90.0,
            metadata={"attempts": 3},
        )
        restored = RunEvent.from_dict(original.to_dict())
        assert restored == original

    def test_to_dict_flattens_enums_to_values(self) -> None:
        event = RunEvent(
            run_id="r1",
            kind=EventKind.COMPLETION,
            timestamp=utc_now_iso(),
            outcome=Outcome.SUCCESS,
        )
        data = event.to_dict()
        assert data["kind"] == "completion"
        assert data["outcome"] == "success"
