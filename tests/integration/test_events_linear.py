"""Integration seam: events emitter -> real LinearTracker -> Linear comment.

This exercises the actual compose path VIBE-146 depends on — a run's failure
becomes a comment on its ticket — running the *real* collaborators (the
emitter, ``LinearSink``, and ``LinearTracker``) and mocking only the true
boundary: the network (``requests.post``). No vibe module is stubbed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

from vibe.events.emitter import RunTelemetry
from vibe.events.schema import Outcome
from vibe.events.sinks import LinearSink, LogSink
from vibe.trackers.linear import LinearTracker

ISSUE_UUID = "00000000-0000-0000-0000-000000000146"


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:  # network boundary: always 200 here
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


def _fake_post(url: str, headers: dict, json: dict, timeout: int) -> _FakeResponse:
    """Stand in for Linear's GraphQL endpoint over HTTP.

    Routes by operation: an issue lookup returns a minimal issue; a
    ``commentCreate`` mutation records the body and returns success.
    """
    query = json.get("query", "")
    if "commentCreate" in query:
        body = json["variables"]["input"]["body"]
        _fake_post.created_comments.append((json["variables"]["input"]["issueId"], body))
        return _FakeResponse(
            {"data": {"commentCreate": {"success": True, "comment": {"id": "c1"}}}}
        )
    # Otherwise it's the GetIssue query backing comment_ticket's lookup.
    return _FakeResponse(
        {
            "data": {
                "issue": {
                    "id": ISSUE_UUID,
                    "identifier": "VIBE-146",
                    "title": "Telemetry",
                    "description": "",
                    "state": {"id": "s1", "name": "In Progress"},
                    "team": {"id": "t1"},
                    "labels": {"nodes": []},
                    "url": "https://linear.app/x/issue/VIBE-146",
                    "priority": 2,
                    "assignee": None,
                    "project": None,
                    "parent": None,
                    "relations": {"nodes": []},
                    "inverseRelations": {"nodes": []},
                }
            }
        }
    )


def _telemetry_with_real_linear(base_path: Path) -> RunTelemetry:
    tracker = LinearTracker(api_key="test-key", team_id="t1")
    return RunTelemetry(sinks=[LogSink(), LinearSink(tracker)], base_path=base_path)


def test_failed_run_posts_failure_comment_to_its_ticket(tmp_path: Path) -> None:
    _fake_post.created_comments = []  # type: ignore[attr-defined]
    telemetry = _telemetry_with_real_linear(tmp_path)

    with patch("vibe.trackers.linear.requests.post", side_effect=_fake_post):
        record = telemetry.start(ticket="VIBE-146", pr_url="https://pr/1")
        telemetry.complete(run_id=record.run_id, outcome=Outcome.FAILURE, reason="CI red")

    # Start + completion each produced a comment on the run's issue (by UUID).
    comments = _fake_post.created_comments  # type: ignore[attr-defined]
    assert [issue_id for issue_id, _ in comments] == [ISSUE_UUID, ISSUE_UUID]
    failure_body = comments[-1][1]
    assert "failed" in failure_body.lower()
    assert "CI red" in failure_body


def test_crash_recovery_makes_failure_visible_in_linear(tmp_path: Path, monkeypatch) -> None:
    """A reconcile-recovered crash still reaches Linear as a failure comment."""
    _fake_post.created_comments = []  # type: ignore[attr-defined]
    telemetry = _telemetry_with_real_linear(tmp_path)
    monkeypatch.setattr("vibe.events.emitter._pid_alive", lambda _pid: False)

    with patch("vibe.trackers.linear.requests.post", side_effect=_fake_post):
        # Start a run, then never complete it — the process "crashes".
        telemetry.start(ticket="VIBE-146")
        _fake_post.created_comments.clear()  # drop the start comment; focus on recovery
        repaired = telemetry.reconcile()

    assert len(repaired) == 1 and repaired[0].outcome == "failure"
    # The synthesized failure was posted to the ticket — visible without Axiom.
    assert any("failed" in body.lower() for _, body in _fake_post.created_comments)  # type: ignore[attr-defined]
