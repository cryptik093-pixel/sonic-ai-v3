"""Offline checks for the pinned public-safe OS reference (no private fetch)."""
import hashlib
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
REF = ROOT / "docs/operating-system/founder_contract_reference.json"

class ContractReferenceTests(unittest.TestCase):
    def test_pinned_reference_is_explicit_and_not_runtime(self):
        raw = REF.read_bytes()
        data = json.loads(raw)
        self.assertEqual(data["canonical_repository"], "cryptik093-pixel/OMEGA-HOUSE-OS")
        self.assertEqual(data["contract_id"], "OH-FOUNDER-ONBOARDING")
        self.assertEqual(data["contract_version"], "1.1.0")
        self.assertRegex(data["canonical_commit"], r"^[0-9a-f]{40}$")
        self.assertRegex(data["contract_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(data["runtime_enforcement"], "not_integrated")
        self.assertIs(data["automatic_loading_implemented"], False)
        self.assertNotIn("token", data)
        self.assertNotIn("secret", data)

if __name__ == "__main__":
    unittest.main()
