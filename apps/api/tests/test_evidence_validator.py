import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schemas.agent_protocol import EvidenceRef, EvidenceSourceType
from schemas.context import ContextArea, ContextObservation, ContextPackage, ContextSourceType, SourceRef
from services.evidence_validator import EvidenceValidationError, EvidenceValidator


def make_package() -> ContextPackage:
    observed_at = datetime.now(timezone.utc)
    observation = ContextObservation(
        context_area=ContextArea.PROJECT,
        field="genre",
        value="Synthwave",
        source=SourceRef(
            source_type=ContextSourceType.PROJECT,
            source_id="7",
            field="genre",
            provenance="project repository",
            observed_at=observed_at,
            reliability=1.0,
        ),
    )
    return ContextPackage(task_query="Review project", observations=[observation])


def test_valid_evidence_must_match_context_observation() -> None:
    package = make_package()
    observation = package.observations[0]
    evidence = EvidenceRef(
        observation_id=observation.observation_id,
        source_type=EvidenceSourceType.PROJECT,
        source_id="7",
        field="genre",
        value="Synthwave",
        observed_at=observation.source.observed_at,
        provenance="project repository",
        reliability=1.0,
    )

    EvidenceValidator().validate([evidence], package)


def test_empty_evidence_is_valid_for_inference_based_recommendations() -> None:
    EvidenceValidator().validate([], make_package())


def test_unknown_observation_is_rejected() -> None:
    package = make_package()
    observation = package.observations[0]
    evidence = EvidenceRef(
        observation_id=observation.observation_id,
        source_type=EvidenceSourceType.PROJECT,
        source_id="8",
        field="genre",
        value="Synthwave",
        observed_at=observation.source.observed_at,
        provenance="project repository",
    )

    with pytest.raises(EvidenceValidationError, match="source ID"):
        EvidenceValidator().validate([evidence], package)
