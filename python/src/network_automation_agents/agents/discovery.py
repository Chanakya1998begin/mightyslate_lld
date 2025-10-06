"""Discovery & Inventory agent implementation."""

from typing import Any, Callable, Mapping

from ..config import Settings
from ..tools import DeviceInventoryTool, LLDPNeighborDiscoveryTool, NSOTUpdateTool
from .base import AbstractNetworkAgent


class DiscoveryInventoryAgent(AbstractNetworkAgent):
    """Maintains the Network Source of Truth."""

    def __init__(self, settings: Settings, **kwargs: Any) -> None:
        super().__init__(
            settings,
            role="Discovery & Inventory Agent",
            goal="Continuously discover network assets and maintain the NSoT.",
            backstory=(
                "You map every device, interface, and connection. Your meticulous scans keep the "
                "network source of truth fresh and accurate."
            ),
            allow_delegation=False,
            verbose=False,
            **kwargs,
        )

    def tool_factories(self) -> Mapping[str, Callable[[], Any]]:
        return {
            "lldp": LLDPNeighborDiscoveryTool,
            "inventory": DeviceInventoryTool,
            "nsot": NSOTUpdateTool,
        }

    def discover_topology(self, device_ip: str, community: str):
        lldp_tool: LLDPNeighborDiscoveryTool = self.get_tool("lldp")
        neighbors = lldp_tool.discover_neighbors(device_ip, community)
        nsot: NSOTUpdateTool = self.get_tool("nsot")
        if neighbors.success:
            for neighbor in neighbors.data:
                nsot.update_nsot(neighbor)
        return neighbors

    def refresh_inventory(self, device_ip: str, creds: dict):
        inventory_tool: DeviceInventoryTool = self.get_tool("inventory")
        record = inventory_tool.get_inventory(device_ip, creds)
        if record.success:
            nsot: NSOTUpdateTool = self.get_tool("nsot")
            nsot.update_nsot(record.data)
        return record
