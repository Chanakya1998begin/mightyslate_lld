"""Implementation of the Conductor AI Agent."""

from typing import Any, Callable, Dict, Mapping

from ..config import Settings
from ..models import ToolOutput
from ..tools.delegation import DelegationInput, TaskDelegationTool
from ..tools.itsm import ITSMIntegrationTool
from ..tools.nli import NLIParserTool
from ..tools.rca import RCACorrelationTool
from .base import AbstractNetworkAgent


class ConductorAIAgent(AbstractNetworkAgent):
    """Master orchestrator responsible for planning and delegation."""

    def __init__(self, settings: Settings, **kwargs: Any) -> None:
        super().__init__(
            settings,
            role="Conductor AI Agent",
            goal="Translate network intents into orchestrated, multi-agent plans.",
            backstory=(
                "You are the central intelligence of the network operations crew. You do not touch "
                "devices directly; instead, you craft plans, delegate tasks, and synthesize findings."
            ),
            allow_delegation=True,
            verbose=True,
            **kwargs,
        )

    def tool_factories(self) -> Mapping[str, Callable[[], Any]]:
        return {
            "delegation": lambda: TaskDelegationTool(self),
            "rca": RCACorrelationTool,
            "itsm": lambda: ITSMIntegrationTool(self.settings.itsm),
            "nli": NLIParserTool,
        }

    def parse_intent(self, message: str) -> ToolOutput:
        parser: NLIParserTool = self.get_tool("nli")
        return parser.parse_intent(message)

    def correlate_events(self, events) -> ToolOutput:
        rca_tool: RCACorrelationTool = self.get_tool("rca")
        return rca_tool.correlate_events(events)

    def dispatch_task(self, agent_name: str, task_description: str, context: Dict[str, Any]) -> ToolOutput:
        delegation_tool: TaskDelegationTool = self.get_tool("delegation")
        params = DelegationInput(agent_name=agent_name, task_description=task_description, context=context)
        return delegation_tool.delegate_task(params)
