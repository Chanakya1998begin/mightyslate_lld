"""Root cause correlation tool."""

from datetime import datetime, timedelta
from typing import Iterable, List

from pydantic import BaseModel, Field

from ..logging import build_logger
from ..models import ToolOutput


class EventRecord(BaseModel):
    timestamp: datetime = Field(..., description="Event timestamp in UTC.")
    domain: str = Field(..., description="Domain (performance, security, config, etc.).")
    summary: str = Field(..., description="Short event description.")
    severity: str = Field(..., description="Event severity level.")


class RCAOutput(BaseModel):
    root_cause: str = Field(..., description="Identified root cause hypothesis.")
    supporting_events: List[EventRecord] = Field(..., description="Events supporting the conclusion.")
    confidence: float = Field(..., description="Confidence score between 0 and 1.")


class RCACorrelationTool:
    """Simple heuristic-based correlation engine."""

    def __init__(self, window_minutes: int = 5) -> None:
        self._window = timedelta(minutes=window_minutes)
        self._logger = build_logger("RCACorrelationTool")

    def correlate_events(self, events: Iterable[EventRecord]) -> ToolOutput:
        events_list = sorted(events, key=lambda e: e.timestamp)
        if not events_list:
            return ToolOutput.fail("No events supplied for correlation")

        latest = events_list[-1]
        window_start = latest.timestamp - self._window
        correlated = [event for event in events_list if event.timestamp >= window_start]

        dominant_domain = self._dominant_domain(correlated)
        root_cause = f"Potential {dominant_domain} issue" if dominant_domain else "Inconclusive"
        confidence = min(1.0, 0.6 + 0.1 * len(correlated))
        self._logger.info(
            "correlated_events",
            count=len(correlated),
            dominant_domain=dominant_domain,
            confidence=confidence,
        )
        return ToolOutput.ok(
            RCAOutput(
                root_cause=root_cause,
                supporting_events=correlated,
                confidence=confidence,
            )
        )

    @staticmethod
    def _dominant_domain(events: List[EventRecord]) -> str:
        tally = {}
        for event in events:
            tally[event.domain] = tally.get(event.domain, 0) + 1
        if not tally:
            return ""
        return max(tally.items(), key=lambda item: item[1])[0]
