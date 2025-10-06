"""Unit tests for crew assembly utilities."""

from types import SimpleNamespace

import pytest

from network_automation_agents.agents import (
    ConductorAIAgent,
    ConfigurationManagementAgent,
    LifecycleManagementAgent,
)
from network_automation_agents.config import Settings
from network_automation_agents.crew_setup import build_network_operations_super_crew


@pytest.fixture()
def settings() -> Settings:
    return Settings()


class DummyCrew:
    """Minimal stand-in for crewAI.Crew capturing constructor data."""

    def __init__(self, *, agents, manager_agent, tasks, process, verbose):
        self.agents = agents
        self.manager_agent = manager_agent
        self.tasks = tasks
        self.process = process
        self.verbose = verbose


def test_lifecycle_agent_enrolled(monkeypatch: pytest.MonkeyPatch, settings: Settings) -> None:
    captured = {}

    def crew_factory(**kwargs):
        captured.update(kwargs)
        return DummyCrew(**kwargs)

    monkeypatch.setattr("network_automation_agents.crew_setup.Crew", crew_factory)
    monkeypatch.setattr(
        "network_automation_agents.crew_setup.Process",
        SimpleNamespace(hierarchical="hierarchical"),
    )

    bundle = build_network_operations_super_crew(settings=settings, crew_verbose=True)

    assert isinstance(bundle.conductor, ConductorAIAgent)
    lifecycle = bundle.agent("Lifecycle Management Agent")
    assert isinstance(lifecycle, LifecycleManagementAgent)

    assert captured["manager_agent"] is bundle.conductor
    assert bundle.conductor in captured["agents"]
    assert lifecycle in captured["agents"]
    assert captured["process"] == "hierarchical"
    assert captured["verbose"] is True


def test_configuration_agent_uses_provided_resolver(
    monkeypatch: pytest.MonkeyPatch, settings: Settings
) -> None:
    def crew_factory(**kwargs):
        return DummyCrew(**kwargs)

    monkeypatch.setattr("network_automation_agents.crew_setup.Crew", crew_factory)
    monkeypatch.setattr(
        "network_automation_agents.crew_setup.Process",
        SimpleNamespace(hierarchical="hierarchical"),
    )

    def resolver(device: str):
        return SimpleNamespace(
            device=device,
            supports_gnmi=False,
            supports_netconf=True,
            supports_snmp=False,
            gnmi_paths=None,
            netconf_paths=None,
            snmp_oids=None,
        )

    bundle = build_network_operations_super_crew(settings=settings, capability_resolver=resolver)
    config_agent = bundle.agent("Configuration Management Agent")
    assert isinstance(config_agent, ConfigurationManagementAgent)

    result = config_agent.check_operational_state(
        device="edge-1", path="interfaces/interface[name=xe-0]/state"
    )
    assert result.success is True
    assert result.data["protocol"] == "NETCONF"