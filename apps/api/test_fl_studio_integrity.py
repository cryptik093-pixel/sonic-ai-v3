import tempfile
import unittest
from pathlib import Path
from .session_integrity import IntegrityError, IntegrityLedger
from .fl_studio_integrity import capture_project, fingerprint, verify_project

class FLStudioIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.project = self.root / "song.flp"
        self.project.write_bytes(b"dummy project data")
        (self.root / "kick.wav").write_bytes(b"wav data")
        self.ledger = IntegrityLedger(self.root / "ledger.sqlite3")

    def tearDown(self):
        self.tmp.cleanup()

    def test_capture_verify_and_changed_file(self):
        s = capture_project(self.ledger, self.root, self.project, assets=["kick.wav"])
        self.assertFalse(s["state"]["capture"]["host_connected"])
        self.assertTrue(verify_project(s, self.root)["verified"])
        (self.root / "kick.wav").write_bytes(b"changed")
        self.assertFalse(verify_project(s, self.root)["verified"])

    def test_snapshot_revision_and_project_protection(self):
        s = capture_project(self.ledger, self.root, "song.flp")
        second = capture_project(self.ledger, self.root, "song.flp",
                                 session_id=s["session_id"], expected_revision=0)
        self.assertEqual(second["revision"], 1)
        with self.assertRaises(IntegrityError):
            capture_project(self.ledger, self.root, "song.flp",
                            session_id=s["session_id"], expected_revision=0)

    def test_non_project_rejected(self):
        with self.assertRaises(IntegrityError):
            capture_project(self.ledger, self.root, "kick.wav")

    def test_outside_root_and_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as other:
            external = Path(other) / "outside.flp"
            external.write_bytes(b"x")
            with self.assertRaises(IntegrityError):
                fingerprint(external, self.root)
        with self.assertRaises(IntegrityError):
            capture_project(self.ledger, self.root, "song.flp", assets=["song.flp"])

    def test_read_only(self):
        before = self.project.read_bytes()
        s = capture_project(self.ledger, self.root, "song.flp")
        verify_project(s, self.root)
        self.assertEqual(self.project.read_bytes(), before)
        self.assertEqual(len(self.ledger.history(s["session_id"])), 1)
