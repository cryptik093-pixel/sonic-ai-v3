import tempfile
import unittest
from pathlib import Path

from .session_integrity import IntegrityError, IntegrityLedger

class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "ledger.db"
        self.ledger = IntegrityLedger(self.path)
        self.initial = {"project_id": "project-001", "host": "FL Studio", "tracks": [],
                        "assets": [], "tempo": 130}

    def tearDown(self):
        self.temp.cleanup()

    def test_checkpoint_restore_and_restart(self):
        session = self.ledger.create(self.initial)
        sid = session["session_id"]
        changed = {**self.initial, "tempo": 140}
        result = self.ledger.checkpoint(sid, 0, changed)
        self.assertEqual(result["revision"], 1)
        self.assertEqual(IntegrityLedger(self.path).get(sid)["state"]["tempo"], 140)
        restored = self.ledger.restore(sid, 1, 0)
        self.assertEqual(restored["revision"], 2)
        self.assertEqual(restored["state"], self.initial)
        self.assertEqual(len(self.ledger.history(sid)), 3)
        self.assertEqual([x["kind"] for x in self.ledger.operations(sid)], ["checkpoint", "restore"])

    def test_stale_revision_rejected(self):
        sid = self.ledger.create(self.initial)["session_id"]
        self.ledger.checkpoint(sid, 0, self.initial)
        with self.assertRaises(IntegrityError) as ctx:
            self.ledger.checkpoint(sid, 0, self.initial)
        self.assertEqual(ctx.exception.code, "conflict")

    def test_project_identity_immutable(self):
        sid = self.ledger.create(self.initial)["session_id"]
        with self.assertRaises(IntegrityError):
            self.ledger.checkpoint(sid, 0, {**self.initial, "project_id": "another"})

    def test_invalid_manifest_rejected(self):
        with self.assertRaises(IntegrityError):
            self.ledger.create({"project_id": "x", "host": "FL Studio", "tempo": float("nan")})

    def test_corruption_detected(self):
        sid = self.ledger.create(self.initial)["session_id"]
        with self.ledger._connect() as db:
            db.execute("UPDATE sessions SET state_json=? WHERE session_id=?",
                       ('{"project_id":"altered"}', sid))
        with self.assertRaises(IntegrityError) as ctx:
            self.ledger.get(sid)
        self.assertEqual(ctx.exception.code, "corrupt")

if __name__ == "__main__":
    unittest.main()
