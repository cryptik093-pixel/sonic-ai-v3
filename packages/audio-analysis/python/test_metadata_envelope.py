import unittest

from metadata_envelope import build_asset_intelligence_envelope, validate_asset_intelligence_envelope


SHA_A = "a" * 64
SHA_B = "b" * 64


def measurement() -> dict:
    return {
        "profile_id": "OH-M04",
        "profile_version": "1.0.0",
        "source": {"sha256": SHA_A},
        "interpretation": {"status": "not_performed"},
    }


def candidate_defect() -> dict:
    return {
        "taxonomy_id": "OH-M02",
        "taxonomy_version": "1.0.0",
        "defect_code": "OH-DEF-ST-NEG-001",
        "state": "candidate",
        "severity": "unrated",
        "cause_status": "unknown",
    }


def build(**overrides) -> dict:
    kwargs = {
        "record_id": "OH-REC-001",
        "production_id": "OH-PROD-001",
        "asset_id": "OH-ASSET-001",
        "filename": "beat.wav",
        "asset_class": "beat",
        "content_sha256": SHA_A,
        "media_type": "audio/wav",
        "derivation_type": "original",
        "provenance_source_ref": "runtime:upload:OH-ASSET-001",
        "provenance_method": "upload_ingestion",
        "observed_at": "2026-09-04T16:00:00Z",
    }
    kwargs.update(overrides)
    return build_asset_intelligence_envelope(**kwargs)


class MetadataEnvelopeTests(unittest.TestCase):
    def test_original_asset_defaults_rights_to_explicit_unknown(self) -> None:
        envelope = build()

        self.assertEqual(envelope["schema_id"], "OH-M05")
        self.assertEqual(envelope["rights"]["status"], "unknown")
        self.assertIsNone(envelope["rights"]["rights_state_id"])
        self.assertIsNone(envelope["rights"]["license_id"])
        self.assertEqual(envelope["rights"]["ai_ml_training_permission"], "unknown")

    def test_unknown_rights_cannot_invent_training_permission(self) -> None:
        with self.assertRaises(ValueError):
            build(
                rights={
                    "status": "unknown",
                    "rights_state_id": None,
                    "license_id": None,
                    "ai_ml_training_permission": "permitted",
                }
            )

    def test_derived_asset_requires_parent_lineage(self) -> None:
        with self.assertRaises(ValueError):
            build(derivation_type="derived")

        envelope = build(
            asset_id="OH-ASSET-002",
            content_sha256=SHA_B,
            derivation_type="derived",
            parent_asset_ids=["OH-ASSET-001"],
        )
        self.assertEqual(envelope["lineage"]["parent_asset_ids"], ["OH-ASSET-001"])

    def test_defects_cannot_travel_without_source_measurement(self) -> None:
        with self.assertRaises(ValueError):
            build(defects=[candidate_defect()])

        envelope = build(measurement=measurement(), defects=[candidate_defect()])
        self.assertEqual(envelope["analysis"]["measurement"]["profile_id"], "OH-M04")
        self.assertEqual(envelope["analysis"]["defects"][0]["taxonomy_id"], "OH-M02")

    def test_candidate_defect_cannot_gain_severity_or_cause_during_transport(self) -> None:
        defect = candidate_defect()
        defect["severity"] = "major"
        with self.assertRaises(ValueError):
            build(measurement=measurement(), defects=[defect])

        defect = candidate_defect()
        defect["cause_status"] = "suspected"
        with self.assertRaises(ValueError):
            build(measurement=measurement(), defects=[defect])

    def test_validated_evidence_requires_reference(self) -> None:
        with self.assertRaises(ValueError):
            build(evidence_state="validated")

        envelope = build(
            evidence_state="validated",
            evidence_refs=["docs/knowledge/requirements/evidence/OH-M04-v1.yaml"],
        )
        self.assertEqual(envelope["evidence"]["state"], "validated")

    def test_measurement_must_preserve_no_interpretation_boundary(self) -> None:
        invalid = measurement()
        invalid["interpretation"]["status"] = "performed"
        with self.assertRaises(ValueError):
            build(measurement=invalid)

    def test_duplicate_parent_ids_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build(
                derivation_type="render",
                parent_asset_ids=["OH-ASSET-001", "OH-ASSET-001"],
            )

    def test_semantic_validator_rejects_bad_asset_hash(self) -> None:
        envelope = build()
        envelope["asset"]["content_sha256"] = "bad"
        with self.assertRaises(ValueError):
            validate_asset_intelligence_envelope(envelope)


if __name__ == "__main__":
    unittest.main()
