import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schemas.context import ContextArea, ContextObservation, ContextSourceType, SourceRef


def test_context_observation_requires_real_source() -> None:
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
        ),
    )

    assert observation.is_inference is False
    assert observation.source.source_id == "7"


def test_inference_cannot_be_stored_as_context_observation() -> None:
    with pytest.raises(ValidationError, match="cannot represent inference"):
        ContextObservation(
            observation_id=uuid4(),
            context_area=ContextArea.PROJECT,
            field="forecast",
            value="Likely to improve",
            is_inference=True,
            source=SourceRef(
                source_type=ContextSourceType.PROJECT,
                source_id="7",
                field="forecast",
                provenance="project repository",
                observed_at=datetime.now(timezone.utc),
            ),
        )
