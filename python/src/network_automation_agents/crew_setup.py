"""Factory for assembling the network operations crew."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Sequence, cast

if TYPE_CHECKING:  # pragma: no cover - typing only
    from crewai import Crew as CrewType  # type: ignore[import-not-found]
    from crewai import Process as ProcessType  # type: ignore[import-not-found]
else:  # pragma: no cover - runtime fallback when crewai unavailable
    CrewType = Any
    ProcessType = Any

try:  # pragma: no cover - avoid hard dependency during static analysis
    from crewai import Crew, Process
except ModuleNotFoundError:  # pragma: no cover - fallback for optional install
    Crew = cast("CrewType", object)
    Process = cast("ProcessType", object)

from .agents import (
    ConductorAIAgent,
    ConfigurationManagementAgent,
    DataCollectionAgent,
    DiscoveryInventoryAgent,
    LifecycleManagementAgent,
    PerformanceMonitoringAgent,
)
from .agents.base import AbstractNetworkAgent
from .config import Settings, load_settings
from .tools.network_interaction import DeviceCapabilities

CapabilityResolver = Callable[[str], DeviceCapabilities]


def _default_capability_resolver(_: str) -> DeviceCapabilities:
    """Return permissive default capabilities for demonstrations/tests."""

    return DeviceCapabilities(
        supports_gnmi=True,
        supports_netconf=True,
        supports_snmp=True,
        gnmi_paths={},
        netconf_paths={},
        snmp_oids={},
    )


@dataclass(frozen=True)
class NetworkOperationsCrew:
    """Container bundling the crew, conductor, and specialists."""

    crew: Any
    conductor: ConductorAIAgent
    specialists: Dict[str, AbstractNetworkAgent]

    def agent(self, name: str) -> AbstractNetworkAgent:
        return self.specialists[name]


def _materialize_agents(
    settings: Settings,
    capability_resolver: CapabilityResolver,
    extra_agents: Optional[Sequence[AbstractNetworkAgent]] = None,
) -> List[AbstractNetworkAgent]:
    catalog: List[AbstractNetworkAgent] = [
        DiscoveryInventoryAgent(settings=settings, name="Discovery & Inventory Agent"),
        DataCollectionAgent(settings=settings, name="Data Collection Agent"),
        ConfigurationManagementAgent(
            settings=settings,
            capability_resolver=capability_resolver,
            name="Configuration Management Agent",
        ),
        PerformanceMonitoringAgent(settings=settings, name="Performance Monitoring Agent"),
        LifecycleManagementAgent(settings=settings, name="Lifecycle Management Agent"),
    ]

    if extra_agents:
        catalog.extend(extra_agents)

    return catalog


def build_network_operations_super_crew(
    settings: Optional[Settings] = None,
    *,
    capability_resolver: Optional[CapabilityResolver] = None,
    extra_agents: Optional[Sequence[AbstractNetworkAgent]] = None,
    crew_process: Optional[Any] = None,
    crew_verbose: bool = False,
) -> NetworkOperationsCrew:
    """Instantiate the conductor and specialist agents as a hierarchical crew."""

    resolved_settings = settings or load_settings()
    resolved_resolver = capability_resolver or _default_capability_resolver

    conductor = ConductorAIAgent(settings=resolved_settings, name="Conductor AI Agent")
    specialists = _materialize_agents(resolved_settings, resolved_resolver, extra_agents)

    specialists_by_role: Dict[str, AbstractNetworkAgent] = {agent.role: agent for agent in specialists}

    process_value = crew_process if crew_process is not None else getattr(Process, "hierarchical", None)

    crew = Crew(
        agents=[conductor, *specialists],
        manager_agent=conductor,
        tasks=[],
        process=process_value,
        verbose=crew_verbose,
    )

    return NetworkOperationsCrew(crew=crew, conductor=conductor, specialists=specialists_by_role)
