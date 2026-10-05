from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..intelligence_store import IntelligenceStore
from .decision_schemas import DecisionRankRequest

AUTHORITY_PENALTY = {
    "L0_READ_ONLY": 0.00,
    "L1_LOCAL_REVERSIBLE": 0.01,
    "L2_EXTERNAL_REVERSIBLE": 0.04,
    "L3_BUSINESS_MUTATION": 0.08,
    "L4_IRREVERSIBLE": 0.15,
}

AUTHORITY_ORDER = {level: index for index, level in enumerate(AUTHORITY_PENALTY)}

WEIGHTS = {
    "alignment": 0.28,
    "expected_impact": 0.24,
    "evidence_strength": 0.16,
    "urgency": 0.10,
    "reversibility": 0.10,
    "execution_efficiency": 0.12,
}
RISK_WEIGHT = 0.18


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass(frozen=True)
class RankedOption:
    option_id: str
    action: str
    score: float
    authority_level: str
    risk: float
    evidence_strength: float
    contributions: dict[str, float]
    penalty_components: dict[str, float]
    evidence: list[dict[str, Any]]
    dependencies: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "option_id": self.option_id,
            "action": self.action,
            "score": round(self.score, 6),
            "authority_level": self.authority_level,
            "requires_explicit_approval": self.authority_level != "L0_READ_ONLY",
            "execution_exposed": False,
            "risk": round(self.risk, 6),
            "evidence_strength": round(self.evidence_strength, 6),
            "contributions": {key: round(value, 6) for key, value in self.contributions.items()},
            "penalties": {key: round(value, 6) for key, value in self.penalty_components.items()},
            "evidence": self.evidence,
            "dependencies": self.dependencies,
        }


class DecisionIntelligence:
    def __init__(self, store: IntelligenceStore | None = None) -> None:
        self.store = store or IntelligenceStore()

    def _evidence_strength(self, evidence: list[dict[str, Any]]) -> float:
        if not evidence:
            return 0.0
        average_confidence = sum(float(item.get("confidence", 0.0)) for item in evidence) / len(evidence)
        saturation = min(len(evidence) / 3.0, 1.0)
        return clamp(average_confidence * saturation)

    def _rank_option(self, option, intent_id: str) -> RankedOption:
        evidence = self.store.get_evidence_records(option.evidence_ids, intent_id=intent_id)
        evidence_strength = self._evidence_strength(evidence)
        execution_efficiency = 1.0 - ((option.effort + option.resource_cost) / 2.0)

        contributions = {
            "alignment": WEIGHTS["alignment"] * option.alignment,
            "expected_impact": WEIGHTS["expected_impact"] * option.expected_impact,
            "evidence_strength": WEIGHTS["evidence_strength"] * evidence_strength,
            "urgency": WEIGHTS["urgency"] * option.urgency,
            "reversibility": WEIGHTS["reversibility"] * option.reversibility,
            "execution_efficiency": WEIGHTS["execution_efficiency"] * execution_efficiency,
        }
        penalties = {
            "risk": RISK_WEIGHT * option.risk,
            "authority_friction": AUTHORITY_PENALTY[option.authority_level],
        }
        score = clamp(sum(contributions.values()) - sum(penalties.values()))

        safe_evidence = [
            {
                "evidence_id": item["evidence_id"],
                "kind": item["kind"],
                "source": item["source"],
                "observed_at": item["observed_at"],
                "confidence": item["confidence"],
                "claim": item.get("claim"),
            }
            for item in evidence
        ]
        return RankedOption(
            option_id=option.option_id,
            action=option.action,
            score=score,
            authority_level=option.authority_level,
            risk=option.risk,
            evidence_strength=evidence_strength,
            contributions=contributions,
            penalty_components=penalties,
            evidence=safe_evidence,
            dependencies=option.dependencies,
        )

    def rank(self, request: DecisionRankRequest) -> dict[str, Any]:
        self.store.get_intent(request.intent_id)
        ids = [option.option_id for option in request.options]
        if len(ids) != len(set(ids)):
            raise ValueError("option_id values must be unique")

        ranked = [self._rank_option(option, request.intent_id) for option in request.options]
        ranked.sort(
            key=lambda item: (
                item.score,
                item.evidence_strength,
                -item.risk,
                -AUTHORITY_ORDER[item.authority_level],
                item.option_id,
            ),
            reverse=True,
        )

        top = ranked[0]
        runner_up = ranked[1]
        gap = max(0.0, top.score - runner_up.score)
        confidence = clamp(
            0.65 * top.evidence_strength
            + 0.35 * min(gap / 0.20, 1.0)
        )

        if top.evidence_strength < 0.15:
            status = "needs_evidence"
        elif top.authority_level == "L4_IRREVERSIBLE" or top.risk >= 0.80:
            status = "manual_review"
        elif confidence < 0.45 or gap < 0.03:
            status = "provisional"
        else:
            status = "recommend"

        advantage_breakdown: list[dict[str, Any]] = []
        for component in WEIGHTS:
            delta = top.contributions[component] - runner_up.contributions[component]
            if abs(delta) >= 0.005:
                advantage_breakdown.append({
                    "component": component,
                    "delta": round(delta, 6),
                    "favors": top.option_id if delta > 0 else runner_up.option_id,
                })
        for component in ("risk", "authority_friction"):
            delta = runner_up.penalty_components[component] - top.penalty_components[component]
            if abs(delta) >= 0.005:
                advantage_breakdown.append({
                    "component": component,
                    "delta": round(delta, 6),
                    "favors": top.option_id if delta > 0 else runner_up.option_id,
                })

        context_memories = []
        if request.memory_limit:
            context_memories = self.store.retrieve_materialized_memories(
                request.objective,
                intent_id=request.intent_id,
                limit=request.memory_limit,
            )

        return {
            "objective": request.objective,
            "intent_id": request.intent_id,
            "decision_status": status,
            "recommended_option_id": top.option_id,
            "decision_confidence": round(confidence, 6),
            "score_gap": round(gap, 6),
            "authority": {
                "recommendation_only": True,
                "execution_exposed": False,
                "required_for_recommendation": top.authority_level,
                "explicit_approval_required": top.authority_level != "L0_READ_ONLY",
            },
            "why_this_beats_runner_up": {
                "runner_up_option_id": runner_up.option_id,
                "advantage_breakdown": advantage_breakdown,
            },
            "ranking_method": {
                "id": "tier2_decision_score_v1",
                "weights": WEIGHTS,
                "risk_weight": RISK_WEIGHT,
                "authority_penalties": AUTHORITY_PENALTY,
                "evidence_strength": "mean_evidence_confidence * min(evidence_count/3, 1)",
                "execution_efficiency": "1 - mean(effort, resource_cost)",
                "confidence": "0.65 * top_evidence_strength + 0.35 * min(score_gap/0.20, 1)",
            },
            "ranked_options": [item.as_dict() for item in ranked],
            "context_memories": context_memories,
        }
