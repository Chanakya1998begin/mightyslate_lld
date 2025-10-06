"""Lifecycle management agent."""

from typing import Any, Callable, Dict, List, Mapping, Optional

from ..config import Settings
from ..models import ToolOutput
from ..tools import CVELookupTool, NSOTQueryTool
from .base import AbstractNetworkAgent


class LifecycleManagementAgent(AbstractNetworkAgent):
    """Manages hardware/software lifecycle and vulnerability posture."""

    def __init__(self, settings: Settings, **kwargs: Any) -> None:
        super().__init__(
            settings,
            role="Lifecycle Management Agent",
            goal="Correlate inventory with vendor intelligence to manage lifecycle risk.",
            backstory=(
                "You look beyond the present, monitoring vulnerabilities and end-of-life dates to "
                "plan proactive upgrades and mitigate risk."
            ),
            allow_delegation=False,
            verbose=False,
            **kwargs,
        )

    def tool_factories(self) -> Mapping[str, Callable[[], Any]]:
        return {
            "nsot_query": NSOTQueryTool,
            "cve": CVELookupTool,
        }

    def assess_vulnerabilities(self, role: Optional[str] = None) -> ToolOutput:
        inventory: NSOTQueryTool = self.get_tool("nsot_query")
        devices = inventory.list_devices(role=role)
        if not devices.success:
            return devices

        cve_tool: CVELookupTool = self.get_tool("cve")
        reports: Dict[str, List[Dict[str, Any]]] = {}
        for record in devices.data:
            cves = cve_tool.lookup(product=record.device, version=record.os_version)
            reports[record.device] = cves.data if cves.success and cves.data else []

        payload = {
            "devices": devices.data,
            "vulnerabilities": reports,
        }
        return ToolOutput.ok(payload)
