"""Event schema for PR Autopilot run telemetry.

A *run* is one execution of the PR Autopilot loop for a ticket. Its lifecycle
is described by exactly two events:

- ``start``      — emitted once, when the run begins.
- ``completion`` — emitted once, when the run reaches a terminal state. Its
  ``outcome`` says *how* it ended.

What counts as what (the definitions VIBE-146 asks the schema to pin down):

- ``success``  — the run achieved its goal: the PR merged, or it is ready +
  green + approved and handed to a human. The autopilot's job is done.
- ``failure``  — the run stopped without success for a non-time reason: an
  unrecoverable error, an escalation that ends the run, or a **crash** that
  ``reconcile`` recovered after the fact (see :mod:`vibe.events.store`).
- ``timeout``  — the run hit its declared time ceiling (e.g. the 90-minute
  hold) without reaching ``success``.

The invariant everything downstream (usage reporting, readiness checks) relies
on: **every run has exactly one start event and exactly one completion event.**
A crash or hard kill that skips the completion is repaired by ``reconcile``,
which synthesizes the missing completion so the invariant always holds
*eventually* — a failed run never just disappears.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


def utc_now() -> datetime:
    """Current time as a timezone-aware UTC ``datetime``."""
    return datetime.now(UTC)


def utc_now_iso() -> str:
    """Current UTC time as an ISO-8601 string (the on-the-wire timestamp)."""
    return utc_now().isoformat()


def new_run_id() -> str:
    """Generate a sortable, filename-safe run identifier.

    Shape: ``<compact-utc-timestamp>-<8 hex>`` (e.g. ``20260530T141203Z-1a2b3c4d``).
    The timestamp prefix makes runs sort chronologically on disk; the random
    suffix keeps two runs started in the same second distinct.
    """
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


class EventKind(StrEnum):
    """The two points in a run's lifecycle that emit telemetry."""

    START = "start"
    COMPLETION = "completion"


class Outcome(StrEnum):
    """How a run ended. Set on the ``completion`` event only."""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"

    @property
    def is_failure(self) -> bool:
        """True for any non-success terminal state (failure *or* timeout).

        Sinks key on this to decide how loudly to surface the outcome — a
        failed or timed-out run must stay visible to humans.
        """
        return self is not Outcome.SUCCESS


@dataclass(frozen=True)
class RunEvent:
    """One immutable telemetry event in a run's lifecycle.

    The shape is deliberately flat and JSON-friendly: it is both the Linear
    comment source and the structured record a future Axiom forwarder (or
    usage-reporting aggregator) consumes without reshaping.
    """

    run_id: str
    kind: EventKind
    timestamp: str  # ISO-8601 UTC
    ticket: str | None = None
    pr_url: str | None = None
    engine: str | None = None
    outcome: Outcome | None = None  # set iff kind == COMPLETION
    reason: str | None = None
    host: str | None = None
    pid: int | None = None
    duration_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # The schema's central invariant, enforced at construction: an outcome
        # belongs to a completion and nowhere else.
        if self.kind is EventKind.COMPLETION and self.outcome is None:
            raise ValueError("completion events require an outcome")
        if self.kind is EventKind.START and self.outcome is not None:
            raise ValueError("start events must not carry an outcome")

    @property
    def is_terminal(self) -> bool:
        return self.kind is EventKind.COMPLETION

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain JSON-safe dict (enums flattened to their values)."""
        return {
            "run_id": self.run_id,
            "kind": self.kind.value,
            "timestamp": self.timestamp,
            "ticket": self.ticket,
            "pr_url": self.pr_url,
            "engine": self.engine,
            "outcome": self.outcome.value if self.outcome else None,
            "reason": self.reason,
            "host": self.host,
            "pid": self.pid,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunEvent:
        """Rebuild a :class:`RunEvent` from :meth:`to_dict` output."""
        outcome = data.get("outcome")
        return cls(
            run_id=data["run_id"],
            kind=EventKind(data["kind"]),
            timestamp=data["timestamp"],
            ticket=data.get("ticket"),
            pr_url=data.get("pr_url"),
            engine=data.get("engine"),
            outcome=Outcome(outcome) if outcome else None,
            reason=data.get("reason"),
            host=data.get("host"),
            pid=data.get("pid"),
            duration_seconds=data.get("duration_seconds"),
            metadata=data.get("metadata") or {},
        )
