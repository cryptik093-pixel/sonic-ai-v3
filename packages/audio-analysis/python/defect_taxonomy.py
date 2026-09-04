"""OH-M02 defect-signal taxonomy for Sonic AI V3.

This layer converts deterministic OH-M04 observations into reviewable signals.
It does not promote a signal into a confirmed production defect and does not
claim a causal mechanism without additional evidence.
"""
from __future__ import annotations

from typing import Any

TAXONOMY_ID = "OH-M02"
TAXONOMY_VERSION = "1.0.0"


def _candidate(
    code: str,
    name: str,
    category: str,
    evidence_path: str,
    observed_value: Any,
    rationale: str,
) -> dict[str, Any]:
    return {
        "taxonomy_id": TAXONOMY_ID,
        "taxonomy_version": TAXONOMY_VERSION,
        "defect_code": code,
        "name": name,
        "category": category,
        "state": "candidate",
        "severity": "unrated",
        "cause_status": "unknown",
        "evidence_class": "deterministic_observation",
        "evidence": {
            "measurement_profile": "OH-M04",
            "field": evidence_path,
            "observed_value": observed_value,
        },
        "rationale": rationale,
        "required_confirmation": "contextual or comparative evidence",
    }


def detect_measurement_signals(measurement: dict[str, Any]) -> list[dict[str, Any]]:
    """Return conservative candidate signals from a validated OH-M04 result."""
    if measurement.get("profile_id") != "OH-M04":
        raise ValueError("OH-M02 v1 accepts OH-M04 measurement results only")

    signals: list[dict[str, Any]] = []
    amplitude = measurement.get("amplitude", {})
    stereo = measurement.get("stereo", {})
    fmt = measurement.get("format", {})

    full_scale_count = int(amplitude.get("full_scale_sample_count", 0) or 0)
    if full_scale_count > 0:
        signals.append(
            _candidate(
                code="OH-DEF-DYN-FS-001",
                name="Digital full-scale sample incidence",
                category="dynamics",
                evidence_path="amplitude.full_scale_sample_count",
                observed_value=full_scale_count,
                rationale=(
                    "One or more PCM samples reached an exact digital full-scale extremum. "
                    "This is a review signal, not proof of upstream clipping or limiter use."
                ),
            )
        )

    correlation = stereo.get("correlation")
    if stereo.get("correlation_status") == "measured" and correlation is not None and correlation < 0.0:
        signals.append(
            _candidate(
                code="OH-DEF-ST-NEG-001",
                name="Negative stereo correlation risk",
                category="stereo",
                evidence_path="stereo.correlation",
                observed_value=correlation,
                rationale=(
                    "The measured two-channel correlation is below zero. This warrants mono/center review, "
                    "but does not by itself prove audible mono failure."
                ),
            )
        )

    duration = float(fmt.get("duration_seconds", 0.0) or 0.0)
    silent_ratio = float(amplitude.get("silent_sample_ratio", 0.0) or 0.0)
    if duration > 0.0 and silent_ratio == 1.0:
        signals.append(
            _candidate(
                code="OH-DEF-SIG-SIL-001",
                name="Digital silence present",
                category="signal_integrity",
                evidence_path="amplitude.silent_sample_ratio",
                observed_value=silent_ratio,
                rationale=(
                    "The entire measured file is at or below the OH-M04 silence threshold. "
                    "Intent is unknown, so this remains a candidate until the asset role is known."
                ),
            )
        )

    return signals
