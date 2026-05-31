"""Where telemetry events go once emitted.

A *sink* receives every event the emitter produces. Sinks are intentionally
dumb and independent: the emitter dispatches to each one best-effort and a sink
that raises is logged, never allowed to take down the run or its sibling sinks
(telemetry must never be the thing that breaks the autopilot).

Two sinks ship here:

- :class:`LogSink` — writes the event as a structured JSON line. This is the
  always-on, Axiom-ready shape; forwarding those lines to Axiom is deliberately
  secondary to the Linear-visible source of truth (VIBE-146 scope).
- :class:`LinearSink` — posts a human-readable comment on the run's *own*
  ticket, so a person watching the issue sees the run start and, crucially, sees
  failures and timeouts without needing Axiom.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod

from vibe.events.schema import EventKind, Outcome, RunEvent
from vibe.trackers.base import TrackerBase

logger = logging.getLogger("vibe.events")


class EventSink(ABC):
    """A destination for run telemetry events."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier used in dispatch-error logging."""

    @abstractmethod
    def emit(self, event: RunEvent) -> None:
        """Deliver *event*. May raise; the emitter isolates failures."""


class LogSink(EventSink):
    """Emit each event as one structured JSON line via the logging module.

    This is the canonical machine-readable record — the exact dict a future
    Axiom forwarder or usage-reporting aggregator would ingest unchanged.
    """

    def __init__(self, log: logging.Logger | None = None, level: int = logging.INFO) -> None:
        self._log = log or logger
        self._level = level

    @property
    def name(self) -> str:
        return "log"

    def emit(self, event: RunEvent) -> None:
        self._log.log(self._level, "vibe.run_event %s", json.dumps(event.to_dict()))


class LinearSink(EventSink):
    """Post run telemetry as comments on the run's own ticket.

    Failures and timeouts are surfaced prominently so they remain visible to
    humans in Linear with no Axiom dependency. An event with no ticket is
    skipped (nothing to comment on).
    """

    def __init__(self, tracker: TrackerBase) -> None:
        self._tracker = tracker

    @property
    def name(self) -> str:
        return "linear"

    def emit(self, event: RunEvent) -> None:
        if not event.ticket:
            return
        self._tracker.comment_ticket(event.ticket, format_comment(event))


# Outcome → (emoji, headline) for the terminal comment. Failures lead with a
# red mark so they stand out in the issue thread.
_OUTCOME_PRESENTATION: dict[Outcome, tuple[str, str]] = {
    Outcome.SUCCESS: ("✅", "PR Autopilot run completed"),
    Outcome.FAILURE: ("❌", "PR Autopilot run failed"),
    Outcome.TIMEOUT: ("⏱️", "PR Autopilot run timed out"),
}


def format_comment(event: RunEvent) -> str:
    """Render a telemetry event as a Linear comment body (Markdown)."""
    if event.kind is EventKind.START:
        lines = [f"🟢 **PR Autopilot run started** · `{event.run_id}`"]
    else:
        assert event.outcome is not None  # guaranteed by RunEvent invariant
        emoji, headline = _OUTCOME_PRESENTATION[event.outcome]
        lines = [f"{emoji} **{headline}** · `{event.run_id}`"]

    detail: list[str] = []
    if event.pr_url:
        detail.append(f"- PR: {event.pr_url}")
    if event.engine:
        detail.append(f"- Engine: `{event.engine}`")
    if event.duration_seconds is not None:
        detail.append(f"- Duration: {event.duration_seconds:.0f}s")
    if event.reason:
        detail.append(f"- Reason: {event.reason}")
    detail.append(f"- At: {event.timestamp}")

    return "\n".join([*lines, "", *detail])
