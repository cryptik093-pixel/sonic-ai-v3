"""OH-M05 canonical metadata envelope for Sonic AI V3.

The envelope transports asset identity, lineage, deterministic OH-M04 analysis,
OH-M02 candidate signals, provenance, evidence state, and explicitly scoped
rights metadata without converting unknown facts into defaults.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

SCHEMA_ID = "OH-M05"
SCHEMA_VERSION = "1.0.0"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")

ASSET_CLASSES = {
    "beat",
    "melody",
    "stem",
    "midi",
    "one_shot",
    "drum_loop",
    "preset",
    "preview",
    "document",
    "other",
}
DERIVATION_TYPES = {"original", "derived", "render", "export", "package"}
INVALIDATION_STATES = {"current", "stale", "unknown"}
EVIDENCE_STATES = {"unvalidated", "validated", "historical", "not_applicable"}
RIGHTS_STATUSES = {"unknown", "known"}
TRAINING_PERMISSIONS = {"unknown", "permitted", "prohibited"}
PROVENANCE_TYPES = {"runtime", "import", "archive", "manual"}


def _require_nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _require_sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{field} must be a lowercase 64-character SHA-256 hex digest")
    return value


def _require_iso8601(value: Any, field: str) -> str:
    _require_nonempty(value, field)
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"{field} must be ISO-8601") from exc
    return value


def _validate_rights(rights: dict[str, Any]) -> None:
    status = rights.get("status")
    if status not in RIGHTS_STATUSES:
        raise ValueError("rights.status must be unknown or known")
    training = rights.get("ai_ml_training_permission")
    if training not in TRAINING_PERMISSIONS:
        raise ValueError("rights.ai_ml_training_permission has an invalid value")

    state_id = rights.get("rights_state_id")
    license_id = rights.get("license_id")
    if status == "unknown":
        if state_id is not None or license_id is not None:
            raise ValueError("unknown rights must not carry authoritative rights_state_id or license_id")
        if training != "unknown":
            raise ValueError("unknown rights must keep AI/ML training permission unknown")
    else:
        _require_nonempty(state_id, "rights.rights_state_id")


def _validate_measurement(measurement: dict[str, Any] | None) -> None:
    if measurement is None:
        return
    if measurement.get("profile_id") != "OH-M04":
        raise ValueError("analysis.measurement must be an OH-M04 result")
    source = measurement.get("source")
    if not isinstance(source, dict):
        raise ValueError("OH-M04 measurement must preserve source provenance")
    _require_sha256(source.get("sha256"), "analysis.measurement.source.sha256")
    interpretation = measurement.get("interpretation")
    if not isinstance(interpretation, dict) or interpretation.get("status") != "not_performed":
        raise ValueError("OH-M04 measurement must preserve the observation/interpretation boundary")


def _validate_defect_record(record: dict[str, Any]) -> None:
    if record.get("taxonomy_id") != "OH-M02":
        raise ValueError("analysis.defects entries must be OH-M02 records")
    _require_nonempty(record.get("defect_code"), "analysis.defects[].defect_code")
    if record.get("state") not in {"signal", "candidate", "confirmed", "resolved", "accepted_exception"}:
        raise ValueError("analysis.defects[].state is invalid")
    if record.get("state") == "candidate":
        if record.get("severity") != "unrated":
            raise ValueError("OH-M02 v1 candidate records must remain severity=unrated")
        if record.get("cause_status") != "unknown":
            raise ValueError("OH-M02 v1 candidate records must remain cause_status=unknown")


def validate_asset_intelligence_envelope(envelope: dict[str, Any]) -> None:
    """Validate OH-M05 v1 semantic invariants using the Python standard library."""
    if envelope.get("schema_id") != SCHEMA_ID:
        raise ValueError("schema_id must be OH-M05")
    if envelope.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")

    _require_nonempty(envelope.get("record_id"), "record_id")
    _require_nonempty(envelope.get("production_id"), "production_id")
    _require_nonempty(envelope.get("asset_id"), "asset_id")

    asset = envelope.get("asset")
    if not isinstance(asset, dict):
        raise ValueError("asset must be an object")
    _require_nonempty(asset.get("filename"), "asset.filename")
    if asset.get("class") not in ASSET_CLASSES:
        raise ValueError("asset.class is invalid")
    _require_sha256(asset.get("content_sha256"), "asset.content_sha256")
    _require_nonempty(asset.get("media_type"), "asset.media_type")

    lineage = envelope.get("lineage")
    if not isinstance(lineage, dict):
        raise ValueError("lineage must be an object")
    if lineage.get("derivation_type") not in DERIVATION_TYPES:
        raise ValueError("lineage.derivation_type is invalid")
    if lineage.get("invalidation_state") not in INVALIDATION_STATES:
        raise ValueError("lineage.invalidation_state is invalid")
    parents = lineage.get("parent_asset_ids")
    if not isinstance(parents, list) or any(not isinstance(item, str) or not item for item in parents):
        raise ValueError("lineage.parent_asset_ids must be a list of non-empty strings")
    if len(parents) != len(set(parents)):
        raise ValueError("lineage.parent_asset_ids must not contain duplicates")
    if lineage.get("derivation_type") == "original" and parents:
        raise ValueError("original assets cannot declare parent_asset_ids")
    if lineage.get("derivation_type") != "original" and not parents:
        raise ValueError("derived/render/export/package assets must declare parent_asset_ids")

    analysis = envelope.get("analysis")
    if not isinstance(analysis, dict):
        raise ValueError("analysis must be an object")
    measurement = analysis.get("measurement")
    _validate_measurement(measurement)
    defects = analysis.get("defects")
    if not isinstance(defects, list):
        raise ValueError("analysis.defects must be an array")
    for record in defects:
        if not isinstance(record, dict):
            raise ValueError("analysis.defects entries must be objects")
        _validate_defect_record(record)
    if defects and measurement is None:
        raise ValueError("measurement-derived OH-M02 records cannot travel without their OH-M04 measurement")

    evidence = envelope.get("evidence")
    if not isinstance(evidence, dict):
        raise ValueError("evidence must be an object")
    if evidence.get("state") not in EVIDENCE_STATES:
        raise ValueError("evidence.state is invalid")
    refs = evidence.get("refs")
    if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref for ref in refs):
        raise ValueError("evidence.refs must be a list of non-empty strings")
    if evidence.get("state") == "validated" and not refs:
        raise ValueError("validated evidence requires at least one evidence reference")

    provenance = envelope.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("provenance must be an object")
    if provenance.get("source_type") not in PROVENANCE_TYPES:
        raise ValueError("provenance.source_type is invalid")
    _require_nonempty(provenance.get("source_ref"), "provenance.source_ref")
    _require_nonempty(provenance.get("method"), "provenance.method")
    _require_iso8601(provenance.get("observed_at"), "provenance.observed_at")

    rights = envelope.get("rights")
    if not isinstance(rights, dict):
        raise ValueError("rights must be an object")
    _validate_rights(rights)


def build_asset_intelligence_envelope(
    *,
    record_id: str,
    production_id: str,
    asset_id: str,
    filename: str,
    asset_class: str,
    content_sha256: str,
    media_type: str,
    derivation_type: str,
    parent_asset_ids: list[str] | None = None,
    invalidation_state: str = "current",
    measurement: dict[str, Any] | None = None,
    defects: list[dict[str, Any]] | None = None,
    evidence_state: str = "unvalidated",
    evidence_refs: list[str] | None = None,
    provenance_source_type: str = "runtime",
    provenance_source_ref: str,
    provenance_method: str,
    observed_at: str,
    rights: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build and validate one canonical OH-M05 asset-intelligence envelope."""
    envelope = {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "record_id": record_id,
        "production_id": production_id,
        "asset_id": asset_id,
        "asset": {
            "filename": filename,
            "class": asset_class,
            "content_sha256": content_sha256,
            "media_type": media_type,
        },
        "lineage": {
            "derivation_type": derivation_type,
            "parent_asset_ids": list(parent_asset_ids or []),
            "invalidation_state": invalidation_state,
        },
        "analysis": {
            "measurement": measurement,
            "defects": list(defects or []),
        },
        "evidence": {
            "state": evidence_state,
            "refs": list(evidence_refs or []),
        },
        "provenance": {
            "source_type": provenance_source_type,
            "source_ref": provenance_source_ref,
            "method": provenance_method,
            "observed_at": observed_at,
        },
        "rights": rights
        if rights is not None
        else {
            "status": "unknown",
            "rights_state_id": None,
            "license_id": None,
            "ai_ml_training_permission": "unknown",
        },
    }
    validate_asset_intelligence_envelope(envelope)
    return envelope
