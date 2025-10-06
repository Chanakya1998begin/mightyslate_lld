"""Common base class for network automation agents."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Mapping

try:  # pragma: no cover - exercised indirectly via optional dependency
    from crewai import Agent  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - fallback for test environments
    class Agent:  # type: ignore[too-many-ancestors,override]
        """Lightweight stand-in used when crewAI isn't installed."""

        def __init__(self, **kwargs: Any) -> None:
            for key, value in kwargs.items():
                setattr(self, key, value)

        def __call__(self, *args: Any, **kwargs: Any) -> Any:  # noqa: D401 - mimic Agent callable
            raise NotImplementedError("crewAI Agent methods require the real dependency")

from ..config import Settings
from ..logging import build_logger


class AbstractNetworkAgent(Agent, ABC):
    """Provides shared initialization, logging, and tool loading."""

    def __init__(self, settings: Settings, **kwargs: Any) -> None:
        self.settings = settings
        self.logger = build_logger(self.__class__.__name__)
        super().__init__(**kwargs)
        self.tools_registry: Dict[str, Any] = {}
        self._load_tools()

    @abstractmethod
    def tool_factories(self) -> Mapping[str, Callable[[], Any]]:
        """Return a mapping of tool name to factory callables."""

    def _load_tools(self) -> None:
        for name, factory in self.tool_factories().items():
            try:
                instance = factory()
                self.tools_registry[name] = instance
                self.logger.info("tool_loaded", tool=name)
            except Exception as exc:  # pragma: no cover - guard for dependency errors
                self.logger.error("tool_load_failed", tool=name, error=str(exc))

    def get_tool(self, name: str) -> Any:
        if name not in self.tools_registry:
            raise KeyError(f"Tool '{name}' not loaded for agent {self.__class__.__name__}")
        return self.tools_registry[name]
