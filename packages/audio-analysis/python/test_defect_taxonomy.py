import unittest

from defect_taxonomy import detect_measurement_signals


def base_measurement() -> dict:
    return {
        "profile_id": "OH-M04",
        "format": {"duration_seconds": 1.0},
        "amplitude": {
            "full_scale_sample_count": 0,
            "silent_sample_ratio": 0.0,
        },
        "stereo": {
            "correlation_status": "measured",
            "correlation": 0.75,
        },
    }


class DefectTaxonomyTests(unittest.TestCase):
    def test_clean_measurement_emits_no_candidates(self) -> None:
        self.assertEqual(detect_measurement_signals(base_measurement()), [])

    def test_full_scale_incidence_is_candidate_not_clipping_claim(self) -> None:
        measurement = base_measurement()
        measurement["amplitude"]["full_scale_sample_count"] = 4

        signals = detect_measurement_signals(measurement)

        self.assertEqual(len(signals), 1)
        signal = signals[0]
        self.assertEqual(signal["defect_code"], "OH-DEF-DYN-FS-001")
        self.assertEqual(signal["state"], "candidate")
        self.assertEqual(signal["severity"], "unrated")
        self.assertEqual(signal["cause_status"], "unknown")
        self.assertNotIn("proof of upstream clipping", signal["rationale"].lower())

    def test_negative_correlation_is_review_signal_not_mono_failure_claim(self) -> None:
        measurement = base_measurement()
        measurement["stereo"]["correlation"] = -0.8

        signals = detect_measurement_signals(measurement)

        self.assertEqual(signals[0]["defect_code"], "OH-DEF-ST-NEG-001")
        self.assertEqual(signals[0]["state"], "candidate")
        self.assertIn("does not by itself prove", signals[0]["rationale"])

    def test_digital_silence_requires_context_before_defect_confirmation(self) -> None:
        measurement = base_measurement()
        measurement["amplitude"]["silent_sample_ratio"] = 1.0

        signals = detect_measurement_signals(measurement)

        self.assertEqual(signals[0]["defect_code"], "OH-DEF-SIG-SIL-001")
        self.assertEqual(signals[0]["required_confirmation"], "contextual or comparative evidence")

    def test_wrong_measurement_profile_is_rejected(self) -> None:
        measurement = base_measurement()
        measurement["profile_id"] = "UNKNOWN"
        with self.assertRaises(ValueError):
            detect_measurement_signals(measurement)


if __name__ == "__main__":
    unittest.main()
