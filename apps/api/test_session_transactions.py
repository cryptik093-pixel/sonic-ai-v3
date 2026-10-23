import tempfile
import unittest
from pathlib import Path

from .fl_studio_integrity import capture_project
from .session_integrity import IntegrityError, IntegrityLedger
from .session_transactions import SessionTransactionController


class SessionTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "test.flp").write_bytes(b"original project")
        (self.root / "stem.wav").write_bytes(b"original stem")
        self.ledger = IntegrityLedger(self.root / "state.db")
        self.record = capture_project(self.ledger, self.root, "test.flp", assets=["stem.wav"])
        self.controller = SessionTransactionController(self.ledger, self.root)

    def tearDown(self):
        self.temp.cleanup()

    def plan(self, **overrides):
        args = {"session_id": self.record["session_id"],
                "expected_revision": self.record["revision"],
                "expected_hash": self.record["sha256"],
                "action": "analyze_audio", "parameters": {"window_ms": 20}}
        args.update(overrides)
        return self.controller.plan(**args)

    def test_plan_is_read_only_and_deterministic(self):
        before = [(p.name, p.read_bytes()) for p in [self.root / "test.flp", self.root / "stem.wav"]]
        result = self.plan()
        self.assertEqual(result["status"], "proposed_only")
        self.assertFalse(result["host_mutation_permitted"])
        self.assertEqual(result["proposal_sha256"], self.plan()["proposal_sha256"])
        self.assertEqual(before, [(p.name, p.read_bytes()) for p in [self.root / "test.flp", self.root / "stem.wav"]])
        self.assertEqual(self.ledger.get(self.record["session_id"])["revision"], 0)

    def test_changed_project_rejected(self):
        (self.root / "test.flp").write_bytes(b"new")
        with self.assertRaises(IntegrityError) as ctx:
            self.plan()
        self.assertEqual(ctx.exception.code, "baseline_mismatch")

    def test_changed_stem_rejected(self):
        (self.root / "stem.wav").write_bytes(b"new")
        with self.assertRaises(IntegrityError) as ctx:
            self.plan()
        self.assertEqual(ctx.exception.code, "baseline_mismatch")

    def test_missing_asset_rejected(self):
        (self.root / "stem.wav").unlink()
        with self.assertRaises(IntegrityError) as ctx:
            self.plan()
        self.assertEqual(ctx.exception.code, "baseline_mismatch")

    def test_stale_revision_rejected(self):
        self.ledger.checkpoint(self.record["session_id"], 0, self.record["state"])
        with self.assertRaises(IntegrityError) as ctx:
            self.plan()
        self.assertEqual(ctx.exception.code, "conflict")

    def test_incorrect_hash_rejected(self):
        with self.assertRaises(IntegrityError) as ctx:
            self.plan(expected_hash="0" * 64)
        self.assertEqual(ctx.exception.code, "conflict")

    def test_host_mutations_denied(self):
        with self.assertRaises(IntegrityError) as ctx:
            self.plan(action="set_mixer_gain")
        self.assertEqual(ctx.exception.code, "operation_denied")

    def test_invalid_parameters_rejected(self):
        with self.assertRaises(IntegrityError) as ctx:
            self.plan(parameters={"gain": float("nan")})
        self.assertEqual(ctx.exception.code, "invalid_operation")

    def test_symlink_escape_rejected_if_supported(self):
        with tempfile.TemporaryDirectory() as outside:
            p = Path(outside) / "stem.wav"
            p.write_bytes(b"out")
            link = self.root / "outside.wav"
            try:
                link.symlink_to(p)
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks unavailable on this Windows host")
            current = self.ledger.get(self.record["session_id"])
            changed = dict(current["state"])
            changed["assets"] = [{**changed["assets"][0], "relative_path": "outside.wav"}]
            self.ledger.checkpoint(self.record["session_id"], 0, changed)
            record = self.ledger.get(self.record["session_id"])
            with self.assertRaises(IntegrityError) as ctx:
                self.controller.validate(record["session_id"], record["revision"], record["sha256"])
            self.assertEqual(ctx.exception.code, "baseline_mismatch")
