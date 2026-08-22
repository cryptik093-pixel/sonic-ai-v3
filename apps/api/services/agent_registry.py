from __future__ import annotations

from schemas.agent_protocol import AgentId, AgentManifest


class AgentRegistryError(ValueError):
    pass


class AgentRegistry:
    def __init__(self, manifests: list[AgentManifest] | None = None) -> None:
        self._manifests: dict[AgentId, AgentManifest] = {}
        for manifest in default_manifests() if manifests is None else manifests:
            self.register(manifest)

    def register(self, manifest: AgentManifest) -> None:
        if manifest.agent_id in self._manifests:
            raise AgentRegistryError(f"Agent {manifest.agent_id.value} is already registered.")
        if not manifest.supports_external_actions:
            manifest = manifest.model_copy(update={"supports_external_actions": False})
        self._manifests[manifest.agent_id] = manifest

    def get(self, agent_id: AgentId | str) -> AgentManifest:
        try:
            normalized_id = AgentId(agent_id)
        except ValueError as exc:
            raise AgentRegistryError(f"Agent {agent_id!r} is unsupported.") from exc

        manifest = self._manifests.get(normalized_id)
        if manifest is None or not manifest.enabled:
            raise AgentRegistryError(f"Agent {normalized_id.value} is unsupported.")
        return manifest

    def find_by_capability(self, capability: str) -> list[AgentManifest]:
        return [
            manifest
            for manifest in self._manifests.values()
            if manifest.enabled and capability in manifest.capabilities
        ]

    def list_agents(self) -> list[AgentManifest]:
        return list(self._manifests.values())


def default_manifests() -> list[AgentManifest]:
    return [
        AgentManifest(
            agent_id=AgentId.OMEGA,
            display_name="OMEGA AI BRAIN",
            description="Routes and validates Sonic AI business intelligence tasks.",
            capabilities=["task_routing", "agent_delegation", "result_validation", "recommendation_synthesis"],
            accepted_task_types=["studio_assistance", "orchestration", "recommendation_review"],
        ),
        AgentManifest(
            agent_id=AgentId.SPECTRA,
            display_name="SPECTRA Customer Segmentation",
            description="Analyzes customer behavior and creates actionable segments.",
            capabilities=["customer_segmentation", "behavior_analysis", "personalization"],
            accepted_task_types=["customer_segmentation", "personalization"],
        ),
        AgentManifest(
            agent_id=AgentId.HAVEN,
            display_name="HAVEN Customer Support",
            description="Classifies and drafts accurate, empathetic support responses.",
            capabilities=["customer_support", "ticket_classification", "troubleshooting", "escalation_recommendations"],
            accepted_task_types=["customer_support", "ticket_classification"],
        ),
        AgentManifest(
            agent_id=AgentId.NEBULA,
            display_name="NEBULA Predictive Analytics",
            description="Analyzes trends, forecasts, anomalies, risks, and opportunities.",
            capabilities=["predictive_analytics", "trend_analysis", "forecasting", "anomaly_detection"],
            accepted_task_types=["predictive_analytics", "forecasting", "trend_analysis"],
        ),
        AgentManifest(
            agent_id=AgentId.MERCURY,
            display_name="MERCURY Product Metadata",
            description="Creates structured metadata from product and audio evidence.",
            capabilities=["product_metadata", "audio_metadata", "tag_classification", "genre_classification", "mood_classification"],
            accepted_task_types=["product_metadata", "audio_metadata"],
        ),
        AgentManifest(
            agent_id=AgentId.ATLAS,
            display_name="ATLAS Sales Funnel Optimization",
            description="Analyzes customer journeys and recommends conversion improvements.",
            capabilities=["sales_funnel", "conversion_analysis", "landing_page_optimization", "upsell_cross_sell_recommendations"],
            accepted_task_types=["sales_funnel", "conversion_analysis"],
        ),
        AgentManifest(
            agent_id=AgentId.ORION,
            display_name="ORION SEO and Content",
            description="Improves search visibility, discoverability, and content quality.",
            capabilities=["seo", "content_optimization", "keyword_analysis", "internal_linking"],
            accepted_task_types=["seo", "content_optimization"],
        ),
    ]


agent_registry = AgentRegistry()
