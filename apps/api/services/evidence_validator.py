from __future__ import annotations

from schemas.agent_protocol import EvidenceRef
from schemas.context import ContextObservation, ContextPackage


class EvidenceValidationError(ValueError):
    pass


class EvidenceValidator:
    def validate(self, evidence_refs: list[EvidenceRef], package: ContextPackage) -> None:
        observations = {observation.observation_id: observation for observation in package.observations}
        for evidence in evidence_refs:
            observation = observations.get(evidence.observation_id)
            if observation is None:
                raise EvidenceValidationError(
                    f"Evidence observation {evidence.observation_id} is not present in the context package."
                )
            self._validate_match(evidence, observation)

    def _validate_match(self, evidence: EvidenceRef, observation: ContextObservation) -> None:
        source = observation.source
        if source.source_type.value != evidence.source_type.value:
            raise EvidenceValidationError("Evidence source type does not match its observation.")
        if source.source_id != evidence.source_id:
            raise EvidenceValidationError("Evidence source ID does not match its observation.")
        if source.field != evidence.field:
            raise EvidenceValidationError("Evidence field does not match its observation.")
        if source.observed_at != evidence.observed_at:
            raise EvidenceValidationError("Evidence timestamp does not match its observation.")
        if source.reliability != evidence.reliability:
            raise EvidenceValidationError("Evidence reliability does not match its observation.")
        if source.provenance != evidence.provenance:
            raise EvidenceValidationError("Evidence provenance does not match its observation.")
        if observation.value != evidence.value:
            raise EvidenceValidationError("Evidence value does not match its observation.")
        if observation.is_inference:
            raise EvidenceValidationError("Inference cannot be represented as observed evidence.")


evidence_validator = EvidenceValidator()
