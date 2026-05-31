"""Durable, write-ahead run records for crash-surviving telemetry.

The hard requirement from VIBE-146 is that a failure stays visible *even when
the run crashes or times out*. A ``finally`` block cannot deliver that: a
``SIGKILL``, an OOM, or a yanked power cord never runs cleanup code.

So this module is **write-ahead**. The moment a run starts we durably persist a
record with ``state == "running"`` and ``outcome == None``. The completion
event later *updates* that record to a terminal state. The consequence: an
orphaned ``running`` record *is itself* the signal that a run died without
finishing — :func:`vibe.events.emitter.RunTelemetry.reconcile` sweeps for those
and synthesizes the missing terminal outcome.

Records live one-file-per-run under ``.vibe/telemetry/runs/<run_id>.json`` so
concurrent runs never contend on a single file, and a half-written record can
never corrupt a sibling. Writes go through :func:`atomic_write_json` (temp file
+ ``os.replace``), so even a crash mid-write leaves the previous record intact.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from vibe.events.schema import RunEvent, utc_now_iso
from vibe.utils.file_lock import atomic_write_json, file_lock

# Telemetry lives under the same CWD-relative ``.vibe/`` tree as local_state.
TELEMETRY_DIR = Path(".vibe/telemetry")
RUNS_SUBDIR = "runs"
CURRENT_RUN_FILE = "current_run"

# Record lifecycle states.
STATE_RUNNING = "running"
STATE_TERMINAL = "terminal"


def telemetry_dir(base_path: Path | None = None) -> Path:
    """Root telemetry directory (``.vibe/telemetry`` under *base_path* or CWD)."""
    return (base_path / TELEMETRY_DIR) if base_path else TELEMETRY_DIR


def runs_dir(base_path: Path | None = None) -> Path:
    """Directory holding one JSON file per run."""
    return telemetry_dir(base_path) / RUNS_SUBDIR


def record_path(run_id: str, base_path: Path | None = None) -> Path:
    """On-disk path for a single run's record."""
    return runs_dir(base_path) / f"{run_id}.json"


def current_run_path(base_path: Path | None = None) -> Path:
    """Pointer file naming the most recently started run.

    Lets the CLI emit ``complete`` without the caller threading a run id back
    through the shell loop — the common single-run-per-machine case.
    """
    return telemetry_dir(base_path) / CURRENT_RUN_FILE


@dataclass
class RunRecord:
    """The durable, mutable state of one run.

    ``events`` keeps the full ordered history (start, then completion) so the
    record doubles as the per-run audit trail usage reporting will read.
    """

    run_id: str
    state: str  # STATE_RUNNING | STATE_TERMINAL
    started_at: str
    ticket: str | None = None
    pr_url: str | None = None
    engine: str | None = None
    outcome: str | None = None  # success | failure | timeout, once terminal
    reason: str | None = None
    ended_at: str | None = None
    host: str | None = None
    pid: int | None = None
    timeout_seconds: float | None = None
    heartbeat_at: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)

    @property
    def is_terminal(self) -> bool:
        return self.state == STATE_TERMINAL

    def append_event(self, event: RunEvent) -> None:
        self.events.append(event.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunRecord:
        known = {f for f in cls.__dataclass_fields__}  # noqa: C416 - explicit set
        return cls(**{k: v for k, v in data.items() if k in known})


def write_record(record: RunRecord, base_path: Path | None = None) -> None:
    """Atomically persist a run record to disk."""
    atomic_write_json(record_path(record.run_id, base_path), record.to_dict())


def load_record(run_id: str, base_path: Path | None = None) -> RunRecord | None:
    """Load a single run record, or ``None`` if it does not exist."""
    path = record_path(run_id, base_path)
    if not path.exists():
        return None
    with open(path) as f:
        return RunRecord.from_dict(json.load(f))


def iter_records(base_path: Path | None = None) -> list[RunRecord]:
    """Load every run record currently on disk (unsorted)."""
    directory = runs_dir(base_path)
    if not directory.exists():
        return []
    records: list[RunRecord] = []
    for path in directory.glob("*.json"):
        try:
            with open(path) as f:
                records.append(RunRecord.from_dict(json.load(f)))
        except (json.JSONDecodeError, OSError, TypeError):
            # A corrupt or partially-written sibling must not break the sweep;
            # skip it rather than let one bad file mask every other run.
            continue
    return records


def set_current_run(run_id: str, base_path: Path | None = None) -> None:
    """Record *run_id* as the machine's current run."""
    path = current_run_path(base_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with file_lock(path):
        path.write_text(run_id + "\n")


def get_current_run(base_path: Path | None = None) -> str | None:
    """Return the current run id, or ``None`` if none is set."""
    path = current_run_path(base_path)
    if not path.exists():
        return None
    value = path.read_text().strip()
    return value or None


def clear_current_run(run_id: str | None = None, base_path: Path | None = None) -> None:
    """Clear the current-run pointer.

    If *run_id* is given, only clears the pointer when it still names that run —
    so a finished run never clobbers a newer run that has since started.
    """
    path = current_run_path(base_path)
    if not path.exists():
        return
    with file_lock(path):
        if run_id is not None and path.read_text().strip() != run_id:
            return
        path.unlink(missing_ok=True)


def make_running_record(
    *,
    run_id: str,
    ticket: str | None,
    pr_url: str | None,
    engine: str | None,
    host: str | None,
    pid: int | None,
    timeout_seconds: float | None,
) -> RunRecord:
    """Build a fresh ``running`` record stamped with the current start time."""
    now = utc_now_iso()
    return RunRecord(
        run_id=run_id,
        state=STATE_RUNNING,
        started_at=now,
        ticket=ticket,
        pr_url=pr_url,
        engine=engine,
        host=host,
        pid=pid,
        timeout_seconds=timeout_seconds,
        heartbeat_at=now,
    )
