"""Maintenance orchestration tooling."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field

from ..logging import build_logger
from ..models import ToolOutput
from .analytics import FailurePrediction
from .itsm import ITSMIntegrationTool, TicketPayload


class MaintenanceScheduleResult(BaseModel):
    """Details about a scheduled maintenance activity."""

    ticket_id: str = Field(...)
    scheduled_start: datetime = Field(...)
    scheduled_end: datetime = Field(...)
    priority: str = Field(...)
    device: str = Field(...)
    component_id: str = Field(...)
    target_failure_probability: float = Field(..., ge=0.0, le=1.0)


class MaintenanceSchedulerTool:
    """Translate failure predictions into ITSM maintenance requests."""

    def __init__(self, itsm_tool: ITSMIntegrationTool, default_duration_hours: int = 2, default_priority: str = "Medium") -> None:
        self._itsm_tool = itsm_tool
        self._default_duration = default_duration_hours
        self._default_priority = default_priority
        self._logger = build_logger("MaintenanceSchedulerTool")

    def schedule_maintenance(
        self,
        prediction: FailurePrediction,
        start_time: Optional[datetime] = None,
        duration_hours: Optional[int] = None,
        priority: Optional[str] = None,
    ) -> ToolOutput:
        window_start = start_time or datetime.utcnow() + timedelta(hours=4)
        window_end = window_start + timedelta(hours=duration_hours or self._default_duration)
        priority_value = priority or self._default_priority

        ticket = TicketPayload(
            summary=f"Proactive maintenance for {prediction.device}",
            description=(
                "Automated scheduling triggered by predictive maintenance model. "
                f"Component {prediction.component_id} has a failure probability of "
                f"{prediction.failure_probability:.2f}."
            ),
            urgency=priority_value,
            additional_fields={
                "device": prediction.device,
                "component_id": prediction.component_id,
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
                "contributing_factors": prediction.contributing_factors,
            },
        )
        self._logger.info(
            "maintenance_schedule_request",
            device=prediction.device,
            component=prediction.component_id,
            probability=prediction.failure_probability,
        )
        result = self._itsm_tool.create_ticket(ticket)
        if not result.success:
            return result

        ticket_id = result.data.get("ticket_id") if isinstance(result.data, dict) else None
        if ticket_id is None:
            ticket_id = f"TICKET-{prediction.device}-{int(window_start.timestamp())}"

        schedule = MaintenanceScheduleResult(
            ticket_id=ticket_id,
            scheduled_start=window_start,
            scheduled_end=window_end,
            priority=priority_value,
            device=prediction.device,
            component_id=prediction.component_id,
            target_failure_probability=prediction.failure_probability,
        )
        return ToolOutput.ok(schedule)


__all__ = ["MaintenanceSchedulerTool", "MaintenanceScheduleResult"]
