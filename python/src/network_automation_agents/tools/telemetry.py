"""Telemetry ingestion tool wrappers."""

from typing import List, Literal

from pydantic import BaseModel, Field

from ..logging import build_logger
from ..models import ToolOutput


class TelemetrySubscription(BaseModel):
    path: str = Field(..., description="Telemetry path to subscribe to.")
    sample_interval_ms: int = Field(..., description="Sampling interval in milliseconds.")


class GNMISubscriptionTool:
    """Manage gNMI telemetry subscriptions (stub)."""

    def __init__(self) -> None:
        self._logger = build_logger("GNMISubscriptionTool")

    def manage_subscription(
        self, device: str, subscriptions: List[TelemetrySubscription], action: Literal["create", "delete"]
    ) -> ToolOutput:
        self._logger.info(
            "manage_subscription",
            device=device,
            action=action,
            count=len(subscriptions),
        )
        return ToolOutput.ok({"device": device, "action": action, "count": len(subscriptions)})


class SNMPPollingJob(BaseModel):
    oids: List[str] = Field(..., description="List of OIDs to poll.")
    poll_interval_sec: int = Field(..., gt=0, description="Polling interval in seconds.")


class SNMPPollingTool:
    """Manage SNMP polling jobs (stub)."""

    def __init__(self) -> None:
        self._logger = build_logger("SNMPPollingTool")

    def manage_polling_job(
        self, device: str, job: SNMPPollingJob, action: Literal["create", "delete"]
    ) -> ToolOutput:
        self._logger.info(
            "manage_polling_job",
            device=device,
            action=action,
            oids=job.oids,
        )
        return ToolOutput.ok({"device": device, "action": action, "oids": job.oids})


class SyslogEndpoint(BaseModel):
    listener: str = Field(..., description="Syslog listener address.")
    formats: List[str] = Field(default_factory=list, description="Accepted log formats.")


class SyslogIngestionTool:
    """Configure syslog ingestion endpoints (stub)."""

    def __init__(self) -> None:
        self._logger = build_logger("SyslogIngestionTool")

    def configure_endpoint(self, endpoint: SyslogEndpoint) -> ToolOutput:
        self._logger.info("configure_syslog", endpoint=endpoint.model_dump())
        return ToolOutput.ok({"endpoint": endpoint.listener})


class FlowCollectorConfig(BaseModel):
    exporters: List[str] = Field(..., description="List of exporters sending flow records.")
    protocol: Literal["ipfix", "netflow", "sflow"] = Field(..., description="Flow protocol in use.")


class FlowCollectorTool:
    """Manage flow data collection (stub)."""

    def __init__(self) -> None:
        self._logger = build_logger("FlowCollectorTool")

    def configure(self, config: FlowCollectorConfig) -> ToolOutput:
        self._logger.info("configure_flow", exporters=config.exporters, protocol=config.protocol)
        return ToolOutput.ok(config.model_dump())
