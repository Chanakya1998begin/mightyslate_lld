"""Protocol abstraction toolset for interacting with network devices."""

from dataclasses import dataclass
from typing import Dict, Optional

from pydantic import BaseModel, Field

from ..logging import build_logger
from ..models import ToolOutput


@dataclass
class DeviceCapabilities:
    supports_gnmi: bool
    supports_netconf: bool
    supports_snmp: bool
    gnmi_paths: Optional[Dict[str, str]] = None
    netconf_paths: Optional[Dict[str, str]] = None
    snmp_oids: Optional[Dict[str, str]] = None


class GetOperationalStateInput(BaseModel):
    device: str = Field(..., description="Hostname or IP of the network device.")
    path: str = Field(..., description="Model-agnostic path requested by the agent.")


class SetConfigurationInput(BaseModel):
    device: str = Field(..., description="Hostname or IP of the network device.")
    payload: Dict[str, str] = Field(..., description="Configuration key/value changes to apply.")


class NetworkInteractionToolset:
    """High-level abstraction over protocol-specific interactions."""

    def __init__(self, capability_resolver) -> None:
        self._capability_resolver = capability_resolver
        self._logger = build_logger("NetworkInteractionToolset")

    def get_operational_state(self, params: GetOperationalStateInput) -> ToolOutput:
        capabilities: DeviceCapabilities = self._capability_resolver(params.device)
        self._logger.info(
            "get_operational_state",
            device=params.device,
            requested_path=params.path,
            capabilities=capabilities,
        )

        if capabilities.supports_gnmi:
            path = (capabilities.gnmi_paths or {}).get(params.path, params.path)
            return ToolOutput.ok({"protocol": "gNMI", "path": path})
        if capabilities.supports_netconf:
            path = (capabilities.netconf_paths or {}).get(params.path, params.path)
            return ToolOutput.ok({"protocol": "NETCONF", "path": path})
        if capabilities.supports_snmp:
            oid = (capabilities.snmp_oids or {}).get(params.path)
            if not oid:
                return ToolOutput.fail("Requested path unavailable via SNMP", details={"path": params.path})
            return ToolOutput.ok({"protocol": "SNMP", "oid": oid})

        return ToolOutput.fail("No supported protocol for device", details={"device": params.device})

    def set_configuration(self, params: SetConfigurationInput) -> ToolOutput:
        capabilities: DeviceCapabilities = self._capability_resolver(params.device)
        self._logger.info(
            "set_configuration",
            device=params.device,
            payload_keys=list(params.payload.keys()),
            capabilities=capabilities,
        )
        if capabilities.supports_netconf:
            return ToolOutput.ok({"protocol": "NETCONF", "payload": params.payload})
        if capabilities.supports_gnmi:
            return ToolOutput.ok({"protocol": "gNMI", "payload": params.payload})
        return ToolOutput.fail(
            "Device does not support transactional configuration protocols",
            details={"device": params.device},
        )
