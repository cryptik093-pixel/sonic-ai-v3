import tempfile
import unittest
from pathlib import Path

from .fl_studio_integrity import capture_project
from .intelligence_store import IntelligenceStore
from .session_integrity import IntegrityError, IntegrityLedger
from .session_evidence_bridge import export_checkpoint


class SessionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project = self.root / "fixture.flp"
        self.project.write_bytes(b"TEST FIXTURE: not a playable FLP")
        self.original = self.project.read_bytes()
        self.ledger = IntegrityLedger(self.root / "integrity.db")
        self.record = capture_project(self.ledger, self.root, self.project)
        self.store = IntelligenceStore(self.root / "intelligence.db")

    def export(self, revision=0, store=None):
        return export_checkpoint(self.ledger, store or self.store,
                                 self.record["session_id"], revision, self.root)

    def test_retry_is_idempotent_and_source_unchanged(self):
        first = self.export()
        counts = self.store.counts()
        second = self.export()
        self.assertEqual(first["status"], "RECORDED")
        self.assertEqual(second["status"], "ALREADY_RECORDED")
        self.assertFalse(any(second["recorded"].values()))
        self.assertEqual(self.store.counts(), counts)
        self.assertEqual(self.project.read_bytes(), self.original)
        self.assertFalse(first["host_state_verified"])

    def test_changed_bytes_reject_before_evidence_write(self):
        before = self.store.counts()
        self.project.write_bytes(b"different fixture")
        with self.assertRaises(IntegrityError) as ctx:
            self.export()
        self.assertEqual(ctx.exception.code, "file_mismatch")
        self.assertEqual(self.store.counts(), before)

    def test_stale_revision_rejects(self):
        self.ledger.checkpoint(self.record["session_id"], 0, self.record["state"])
        before = self.store.counts()
        with self.assertRaises(IntegrityError) as ctx:
            self.export()
        self.assertEqual(ctx.exception.code, "conflict")
        self.assertEqual(self.store.counts(), before)

    def test_other_owner_or_workspace_rejected(self):
        for owner, workspace in [("other", "omega-house-studio"), ("local-producer", "other")]:
            store = IntelligenceStore(self.root / "intelligence.db", owner_id=owner, workspace_id=workspace)
            before = store.counts()
            with self.assertRaises(IntegrityError) as ctx:
                self.export(store=store)
            self.assertEqual(ctx.exception.code, "outside_scope")
            self.assertEqual(store.counts(), before)

    def test_partial_write_retry_completes_checkpoint(self):
        original = self.store.append_checkpoint
        self.store.append_checkpoint = lambda _: (_ for _ in ()).throw(RuntimeError("fixture interruption"))
        with self.assertRaises(RuntimeError):
            self.export()
        self.store.append_checkpoint = original
        result = self.export()
        self.assertFalse(result["recorded"]["evidence"])
        self.assertTrue(result["recorded"]["checkpoint"])


if __name__ == "__main__":
    unittest.main()
