"""Configuration management agent."""

from typing import Any, Callable, Mapping

from ..config import Settings
from ..tools import NetworkInteractionToolset
from ..tools.network_interaction import GetOperationalStateInput, SetConfigurationInput
from .base import AbstractNetworkAgent


class ConfigurationManagementAgent(AbstractNetworkAgent):
    """Ensures devices remain compliant and configurations stay pristine."""

    def __init__(self, settings: Settings, capability_resolver, **kwargs: Any) -> None:
        self._capability_resolver = capability_resolver
        super().__init__(
            settings,
            role="Configuration Management Agent",
            goal="Audit and enforce configuration standards across the fleet.",
            backstory=(
                "You guard the golden configs. Every drift, every unauthorized change is your enemy. "
                "With surgical precision you revert and remediate."
            ),
            allow_delegation=False,
            verbose=False,
            **kwargs,
        )

    def tool_factories(self) -> Mapping[str, Callable[[], Any]]:
        return {"network": lambda: NetworkInteractionToolset(self._capability_resolver)}

    def check_operational_state(self, device: str, path: str):
        tool: NetworkInteractionToolset = self.get_tool("network")
        params = GetOperationalStateInput(device=device, path=path)
        return tool.get_operational_state(params)

    def push_configuration(self, device: str, payload: dict):
        tool: NetworkInteractionToolset = self.get_tool("network")
        params = SetConfigurationInput(device=device, payload=payload)
        return tool.set_configuration(params)
