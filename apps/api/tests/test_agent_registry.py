import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schemas.agent_protocol import AgentId, AgentManifest
from services.agent_registry import AgentRegistry, AgentRegistryError, agent_registry


EXPECTED_AGENTS = {
    AgentId.OMEGA,
    AgentId.SPECTRA,
    AgentId.HAVEN,
    AgentId.NEBULA,
    AgentId.MERCURY,
    AgentId.ATLAS,
    AgentId.ORION,
}


def test_default_registry_contains_only_supported_phase_one_agents() -> None:
    registered = {manifest.agent_id for manifest in agent_registry.list_agents()}

    assert registered == EXPECTED_AGENTS
    assert all(not manifest.supports_external_actions for manifest in agent_registry.list_agents())


def test_echo_is_unsupported() -> None:
    with pytest.raises(AgentRegistryError, match="unsupported"):
        agent_registry.get("echo")


def test_registry_rejects_duplicate_registration() -> None:
    registry = AgentRegistry(manifests=[])
    manifest = AgentManifest(
        agent_id=AgentId.OMEGA,
        display_name="OMEGA",
        description="Test manifest",
    )
    registry.register(manifest)

    with pytest.raises(AgentRegistryError, match="already registered"):
        registry.register(manifest)


def test_registry_finds_specialist_by_capability() -> None:
    matches = agent_registry.find_by_capability("predictive_analytics")

    assert [manifest.agent_id for manifest in matches] == [AgentId.NEBULA]
