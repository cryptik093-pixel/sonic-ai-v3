import json
import tempfile
import unittest
from pathlib import Path

from .session_integrity import IntegrityLedger, IntegrityError
from .fl_studio_probe_import import import_probe

class ProbeImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.ledger = IntegrityLedger(self.root / "ledger.db")
        self.session = self.ledger.create({
            "project_id": "demo.flp", "host": "FL Studio",
            "tracks": [], "assets": []})
        self.file = self.root / "probe.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_import_is_audited_and_unverified(self):
        self.file.write_text(json.dumps({
            "schema": "sonic.fl.readonly.v1",
            "channels": [], "mixer_tracks": [],
            "tempo": {"status": "available", "value": 130}}))
        result = import_probe(self.ledger, self.session["session_id"], 0, self.file)
        self.assertEqual(result["revision"], 1)
        self.assertEqual(result["state"]["host_observation"]["reported"]["tempo"]["value"], 130)
        self.assertFalse(result["state"]["host_observation"]["vst_state_verified"])
        self.assertEqual(self.ledger.operations(self.session["session_id"])[0]["kind"], "checkpoint")

    def test_invalid_schema_rejected(self):
        self.file.write_text('{"schema":"wrong","channels":[],"mixer_tracks":[]}')
        with self.assertRaises(IntegrityError):
            import_probe(self.ledger, self.session["session_id"], 0, self.file)

    def test_stale_revision_rejected(self):
        self.file.write_text('{"schema":"sonic.fl.readonly.v1","channels":[],"mixer_tracks":[]}')
        import_probe(self.ledger, self.session["session_id"], 0, self.file)
        with self.assertRaises(IntegrityError):
            import_probe(self.ledger, self.session["session_id"], 0, self.file)
