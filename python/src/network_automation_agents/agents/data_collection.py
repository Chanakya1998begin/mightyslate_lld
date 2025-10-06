"""Data collection agent implementation."""

from typing import Any, Callable, Mapping, Sequence

from ..tools import (
    FlowCollectorConfig,
    FlowCollectorTool,
    GNMISubscriptionTool,
    SNMPPollingJob,
    SNMPPollingTool,
    SyslogEndpoint,
    SyslogIngestionTool,
    TelemetrySubscription,
)
from ..config import Settings
from .base import AbstractNetworkAgent


class DataCollectionAgent(AbstractNetworkAgent):
    """Orchestrates telemetry ingestion across the network."""

    def __init__(self, settings: Settings, **kwargs: Any) -> None:
        super().__init__(
            settings,
            role="Data Collection Agent",
            goal="Maintain telemetry streams and ensure data fidelity for analytics.",
            backstory=(
                "You are the nervous system of the platform, deploying collectors, maintaining "
                "subscriptions, and ensuring every byte of telemetry reaches the analytics stack."
            ),
            allow_delegation=False,
            verbose=False,
            **kwargs,
        )

    def tool_factories(self) -> Mapping[str, Callable[[], Any]]:
        return {
            "gnmi": GNMISubscriptionTool,
            "snmp": SNMPPollingTool,
            "syslog": SyslogIngestionTool,
            "flow": FlowCollectorTool,
        }

    def ensure_gnmi_subscription(self, device: str, subscriptions: Sequence[TelemetrySubscription]):
        tool: GNMISubscriptionTool = self.get_tool("gnmi")
        return tool.manage_subscription(device, subscriptions, action="create")

    def remove_gnmi_subscription(self, device: str, subscriptions: Sequence[TelemetrySubscription]):
        tool: GNMISubscriptionTool = self.get_tool("gnmi")
        return tool.manage_subscription(device, subscriptions, action="delete")

    def configure_snmp_job(self, device: str, job: SNMPPollingJob, action: str):
        tool: SNMPPollingTool = self.get_tool("snmp")
        return tool.manage_polling_job(device, job, action=action)

    def configure_syslog(self, endpoint: SyslogEndpoint):
        tool: SyslogIngestionTool = self.get_tool("syslog")
        return tool.configure_endpoint(endpoint)

    def configure_flow_collection(self, config: FlowCollectorConfig):
        tool: FlowCollectorTool = self.get_tool("flow")
        return tool.configure(config)
