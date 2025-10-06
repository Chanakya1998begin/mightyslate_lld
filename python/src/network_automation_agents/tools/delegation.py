"""Task delegation wrapper tool."""

from typing import Any, Dict, Optional

try:  # pragma: no cover - dependency optional during tests
    from crewai import Agent  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - fallback when crewAI missing
    class Agent:  # type: ignore[override,too-many-ancestors]
        def __init__(self, **kwargs: Any) -> None:
            for key, value in kwargs.items():
                setattr(self, key, value)
from pydantic import BaseModel, Field

from ..logging import build_logger
from ..models import ToolOutput


class DelegationInput(BaseModel):
    agent_name: str = Field(..., description="Target agent registered in the crew.")
    task_description: str = Field(..., description="Plain-language task summary.")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context payload for the task.")


class TaskDelegationTool:
    """Wrapper around crewAI delegation with structured logging."""

    def __init__(self, delegator: Agent) -> None:
        self._delegator = delegator
        self._logger = build_logger("TaskDelegationTool", agent=delegator.role)

    def delegate_task(self, params: DelegationInput) -> ToolOutput:
        self._logger.info(
            "delegating_task",
            target_agent=params.agent_name,
            task_hash=hash(params.task_description),
            context_keys=list(params.context.keys()),
        )
        try:
            result = self._delegator.delegate(
                agent_name=params.agent_name,
                task=params.task_description,
                context=params.context,
            )
            return ToolOutput.ok(result)
        except Exception as exc:  # pragma: no cover - crewAI raises runtime errors
            self._logger.error(
                "delegation_failed",
                target_agent=params.agent_name,
                error=str(exc),
            )
            return ToolOutput.fail("Delegation failed", details={"exception": str(exc)})
