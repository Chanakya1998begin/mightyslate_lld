"""Agent implementations for the network operations crew."""

from importlib import import_module
from typing import Any, Dict, Tuple

__all__ = [
    "AbstractNetworkAgent",
    "ConductorAIAgent",
    "ConfigurationManagementAgent",
    "DataCollectionAgent",
    "DiscoveryInventoryAgent",
    "LifecycleManagementAgent",
    "PerformanceMonitoringAgent",
    "ProactiveMaintenanceAgent",
    "SecurityThreatDetectionAgent",
]

_LAZY_IMPORTS: Dict[str, Tuple[str, str]] = {
    "AbstractNetworkAgent": ("network_automation_agents.agents.base", "AbstractNetworkAgent"),
    "ConductorAIAgent": ("network_automation_agents.agents.conductor", "ConductorAIAgent"),
    "ConfigurationManagementAgent": (
        "network_automation_agents.agents.configuration",
        "ConfigurationManagementAgent",
    ),
    "DataCollectionAgent": ("network_automation_agents.agents.data_collection", "DataCollectionAgent"),
    "DiscoveryInventoryAgent": ("network_automation_agents.agents.discovery", "DiscoveryInventoryAgent"),
    "LifecycleManagementAgent": ("network_automation_agents.agents.lifecycle", "LifecycleManagementAgent"),
    "PerformanceMonitoringAgent": (
        "network_automation_agents.agents.performance",
        "PerformanceMonitoringAgent",
    ),
    "ProactiveMaintenanceAgent": (
        "network_automation_agents.agents.proactive",
        "ProactiveMaintenanceAgent",
    ),
    "SecurityThreatDetectionAgent": (
        "network_automation_agents.agents.security",
        "SecurityThreatDetectionAgent",
    ),
}


def __getattr__(name: str) -> Any:  # pragma: no cover - trivial delegator
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module 'network_automation_agents.agents' has no attribute {name!r}")
    module_name, attr_name = _LAZY_IMPORTS[name]
    module = import_module(module_name)
    attr = getattr(module, attr_name)
    globals()[name] = attr
    return attr
