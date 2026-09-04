import hashlib
import json
import math
import unittest
from pathlib import Path

from defect_taxonomy import detect_measurement_signals
from metadata_envelope import build_asset_intelligence_envelope
from sonic_measurement import measure_pcm_wav


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "audio" / "golden"
MANIFEST_PATH = FIXTURE_ROOT / "manifest.json"
FLOAT_TOLERANCE = 1e-9


def assert_optional_float(testcase: unittest.TestCase, actual, expected) -> None:
    if expected is None:
        testcase.assertIsNone(actual)
    else:
        testcase.assertIsNotNone(actual)
        testcase.assertTrue(
            math.isclose(actual, expected, rel_tol=0.0, abs_tol=FLOAT_TOLERANCE),
            msg=f"expected {expected}, got {actual}",
        )


class GoldenAudioFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_manifest_declares_phase2_contract_stack(self) -> None:
        self.assertEqual(self.manifest["schema_id"], "OH-M03")
        self.assertEqual(self.manifest["measurement_profile"], "OH-M04")
        self.assertEqual(self.manifest["defect_taxonomy"], "OH-M02")
        self.assertEqual(self.manifest["metadata_schema"], "OH-M05")
        self.assertGreaterEqual(len(self.manifest["fixtures"]), 5)

    def test_all_golden_fixture_bytes_measure_and_signal_as_declared(self) -> None:
        for fixture in self.manifest["fixtures"]:
            with self.subTest(fixture=fixture["fixture_id"]):
                path = FIXTURE_ROOT / fixture["filename"]
                self.assertTrue(path.is_file())

                actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(actual_sha, fixture["sha256"])

                measurement = measure_pcm_wav(path)
                expected = fixture["expected"]

                self.assertEqual(measurement["source"]["sha256"], fixture["sha256"])
                self.assertEqual(measurement["format"]["sample_rate_hz"], expected["sample_rate_hz"])
                self.assertEqual(measurement["format"]["channels"], expected["channels"])
                self.assertEqual(measurement["format"]["bit_depth"], expected["bit_depth"])
                self.assertEqual(measurement["format"]["frame_count"], expected["frame_count"])
                assert_optional_float(self, measurement["format"]["duration_seconds"], expected["duration_seconds"])
                assert_optional_float(self, measurement["amplitude"]["sample_peak_dbfs"], expected["sample_peak_dbfs"])
                assert_optional_float(self, measurement["amplitude"]["rms_dbfs"], expected["rms_dbfs"])
                assert_optional_float(self, measurement["amplitude"]["crest_factor_db"], expected["crest_factor_db"])
                self.assertEqual(
                    measurement["amplitude"]["full_scale_sample_count"],
                    expected["full_scale_sample_count"],
                )
                assert_optional_float(
                    self,
                    measurement["amplitude"]["silent_sample_ratio"],
                    expected["silent_sample_ratio"],
                )
                assert_optional_float(
                    self,
                    measurement["stereo"]["correlation"],
                    expected["stereo_correlation"],
                )

                signals = detect_measurement_signals(measurement)
                actual_codes = [signal["defect_code"] for signal in signals]
                self.assertEqual(actual_codes, expected["defect_codes"])

                envelope = build_asset_intelligence_envelope(
                    record_id=f"OH-REC-{fixture['fixture_id']}",
                    production_id=self.manifest["production_id"],
                    asset_id=fixture["asset_id"],
                    filename=fixture["filename"],
                    asset_class="other",
                    content_sha256=fixture["sha256"],
                    media_type="audio/wav",
                    derivation_type="original",
                    measurement=measurement,
                    defects=signals,
                    evidence_state="validated",
                    evidence_refs=["tests/fixtures/audio/golden/manifest.json"],
                    provenance_source_type="runtime",
                    provenance_source_ref=f"golden-fixture:{fixture['fixture_id']}",
                    provenance_method="OH-M03 persistent fixture corpus",
                    observed_at="2026-09-04T17:00:00Z",
                )
                self.assertEqual(envelope["schema_id"], "OH-M05")
                self.assertEqual(envelope["asset"]["content_sha256"], fixture["sha256"])
                self.assertEqual(envelope["evidence"]["state"], "validated")
                self.assertEqual(envelope["rights"]["status"], "unknown")


if __name__ == "__main__":
    unittest.main()
