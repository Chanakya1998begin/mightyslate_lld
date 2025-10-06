# Network Automation Agents

This Python package implements the agentic network management platform defined in the functional and design specifications. It provides a hierarchical crew of AI agents, tool abstractions, and structured data contracts ready for integration with crewAI.

## Features

- Abstract base agent with structured logging and shared tool loading.
- Conductor AI agent acting as planner and orchestrator with delegation, RCA, ITSM, and NLI tooling.
- Seven specialist agents (discovery, data collection, performance, configuration, lifecycle, security, proactive maintenance) with well-defined responsibilities.
- Tool abstractions that wrap network interaction protocols, telemetry subscriptions, anomaly detection, predictive maintenance, and more.
- Pydantic models for every tool input/output to guarantee schema integrity.
- Settings and secrets loading via `pydantic-settings`.
- Initial pytest coverage for model validation and crew assembly.

## Quickstart

```bash
# Install in editable mode with development dependencies
pip install -e .[dev]

# Run tests
pytest
```

## Project Layout

```text
src/network_automation_agents/
  config.py             # runtime configuration and secrets loading
  logging.py            # structured logging defaults
  models/               # shared data contracts
  tools/                # tool abstractions and protocol adapters
  agents/               # base and specialist agent implementations
  crew_setup.py         # helper to assemble the hierarchical crew

tests/
  test_tool_models.py   # validates tool input/output schema behavior
  test_agent_setup.py   # confirms crew setup wiring
```

## Next Steps

The current implementation focuses on scaffolding compliant with the specification. Integrate real protocol adapters, connect to actual NSoT/ITSM systems, and extend tests with integration scenarios as infrastructure becomes available.
