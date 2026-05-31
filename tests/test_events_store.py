"""Unit tests for the durable run-record store."""

from __future__ import annotations

from pathlib import Path

import pytest

from vibe.events import store
from vibe.events.schema import EventKind, Outcome, RunEvent, utc_now_iso
from vibe.events.store import RunRecord


def _record(run_id: str = "r1") -> RunRecord:
    return store.make_running_record(
        run_id=run_id,
        ticket="VIBE-146",
        pr_url=None,
        engine="claude",
        host="runner-1",
        pid=4242,
        timeout_seconds=300.0,
    )


class TestRecordRoundTrip:
    def test_write_then_load(self, tmp_path: Path) -> None:
        record = _record()
        store.write_record(record, tmp_path)
        loaded = store.load_record("r1", tmp_path)
        assert loaded is not None
        assert loaded.to_dict() == record.to_dict()

    def test_load_missing_returns_none(self, tmp_path: Path) -> None:
        assert store.load_record("nope", tmp_path) is None

    def test_records_are_one_file_per_run(self, tmp_path: Path) -> None:
        store.write_record(_record("r1"), tmp_path)
        store.write_record(_record("r2"), tmp_path)
        ids = {r.run_id for r in store.iter_records(tmp_path)}
        assert ids == {"r1", "r2"}

    def test_event_appends_to_record(self, tmp_path: Path) -> None:
        record = _record()
        record.append_event(RunEvent(run_id="r1", kind=EventKind.START, timestamp=utc_now_iso()))
        store.write_record(record, tmp_path)
        loaded = store.load_record("r1", tmp_path)
        assert loaded is not None
        assert loaded.events[0]["kind"] == "start"


class TestIterResilience:
    def test_corrupt_record_is_skipped(self, tmp_path: Path) -> None:
        store.write_record(_record("good"), tmp_path)
        bad = store.record_path("bad", tmp_path)
        bad.write_text("{not valid json")
        ids = {r.run_id for r in store.iter_records(tmp_path)}
        # The corrupt sibling must not mask the good record or raise.
        assert ids == {"good"}

    def test_empty_dir_returns_no_records(self, tmp_path: Path) -> None:
        assert store.iter_records(tmp_path) == []


class TestCurrentRunPointer:
    def test_set_get_clear(self, tmp_path: Path) -> None:
        store.set_current_run("r1", tmp_path)
        assert store.get_current_run(tmp_path) == "r1"
        store.clear_current_run("r1", tmp_path)
        assert store.get_current_run(tmp_path) is None

    def test_get_when_unset_is_none(self, tmp_path: Path) -> None:
        assert store.get_current_run(tmp_path) is None

    def test_clear_only_when_id_matches(self, tmp_path: Path) -> None:
        # A finished run must not clobber a newer current run.
        store.set_current_run("r2", tmp_path)
        store.clear_current_run("r1", tmp_path)  # stale run id
        assert store.get_current_run(tmp_path) == "r2"

    def test_unconditional_clear(self, tmp_path: Path) -> None:
        store.set_current_run("r2", tmp_path)
        store.clear_current_run(base_path=tmp_path)
        assert store.get_current_run(tmp_path) is None


class TestFromDictTolerance:
    def test_ignores_unknown_keys(self) -> None:
        # Forward-compatibility: a record written by a newer version with extra
        # fields still loads on an older reader.
        record = RunRecord.from_dict(
            {
                "run_id": "r1",
                "state": store.STATE_RUNNING,
                "started_at": utc_now_iso(),
                "future_field": "ignored",
            }
        )
        assert record.run_id == "r1"


@pytest.mark.parametrize("outcome", [o.value for o in Outcome])
def test_make_running_record_starts_non_terminal(outcome: str) -> None:
    # The record is always created RUNNING regardless of any later outcome.
    record = _record()
    assert record.state == store.STATE_RUNNING
    assert record.is_terminal is False
    assert record.outcome is None
