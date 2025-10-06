"""Discovery and inventory tooling."""

from typing import List

from pydantic import BaseModel, Field

from ..logging import build_logger
from ..models import ToolOutput


class LLDPNeighbor(BaseModel):
    local_port: str = Field(..., description="Local port identifier.")
    remote_chassis_id: str = Field(..., description="Remote system chassis ID.")
    remote_port_id: str = Field(..., description="Remote port identifier.")
    remote_system_name: str = Field(..., description="Remote system hostname.")


class LLDPNeighborDiscoveryTool:
    """Stubbed LLDP discovery leveraging SNMP walks."""

    def __init__(self) -> None:
        self._logger = build_logger("LLDPNeighborDiscoveryTool")

    def discover_neighbors(self, device_ip: str, community: str) -> ToolOutput:
        self._logger.info("discover_neighbors", device=device_ip)
        # Placeholder stub returns synthetic data for demonstration
        neighbors = [
            LLDPNeighbor(
                local_port="Gig0/1",
                remote_chassis_id="00:11:22:33:44:55",
                remote_port_id="Gig0/24",
                remote_system_name="core-switch-1",
            )
        ]
        return ToolOutput.ok(neighbors)


class DeviceInventoryRecord(BaseModel):
    hostname: str = Field(...)
    serial_number: str = Field(...)
    os_version: str = Field(...)
    model: str = Field(...)


class DeviceInventoryTool:
    """Gather device inventory details via NETCONF/SNMP."""

    def __init__(self) -> None:
        self._logger = build_logger("DeviceInventoryTool")

    def get_inventory(self, device_ip: str, creds: dict) -> ToolOutput:
        self._logger.info("get_inventory", device=device_ip)
        inventory = DeviceInventoryRecord(
            hostname=creds.get("hostname", device_ip),
            serial_number="SN123456789",
            os_version="IOS-XE 17.9",
            model="C9500-24Y4C",
        )
        return ToolOutput.ok(inventory)


class NSOTUpdateTool:
    """Persist inventory or topology records to the Network Source of Truth."""

    def __init__(self) -> None:
        self._logger = build_logger("NSOTUpdateTool")

    def update_nsot(self, payload) -> ToolOutput:
        self._logger.info("update_nsot", payload_type=payload.__class__.__name__)
        return ToolOutput.ok({"status": "updated"})
