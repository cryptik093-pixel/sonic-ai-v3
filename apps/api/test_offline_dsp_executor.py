import tempfile
import unittest
import wave
from pathlib import Path
from array import array

from .session_integrity import IntegrityError, IntegrityLedger
from .fl_studio_integrity import capture_project
from .session_transactions import SessionTransactionController
from .offline_dsp_executor import execute_gain


class OfflineDSPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        self.output = self.base / "output"
        self.source.mkdir()
        self.output.mkdir()
        (self.source / "test.flp").write_bytes(b"fixture")
        self.wav = self.source / "stem.wav"
        with wave.open(str(self.wav), "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(44100)
            f.writeframes(array("h", [0, 1000, -1000, 32760, -32760]).tobytes())
        self.ledger = IntegrityLedger(self.base / "ledger.db")
        self.record = capture_project(self.ledger, self.source, "test.flp", assets=["stem.wav"])
        self.controller = SessionTransactionController(self.ledger, self.source)

    def tearDown(self):
        self.temp.cleanup()

    def execute(self, **changes):
        args = dict(controller=self.controller, session_id=self.record["session_id"],
                    expected_revision=0, expected_hash=self.record["sha256"],
                    source_relative="stem.wav", gain=0.5, output_dir=self.output,
                    output_name="candidate.wav")
        args.update(changes)
        return execute_gain(**args)

    def test_publish_preserves_source_and_samples(self):
        before = self.wav.read_bytes()
        result = self.execute()
        self.assertEqual(result["status"], "published_offline_candidate")
        self.assertEqual(before, self.wav.read_bytes())
        with wave.open(str(self.output / "candidate.wav"), "rb") as f:
            samples = array("h", f.readframes(f.getnframes()))
            self.assertEqual(samples.tolist(), [0, 500, -500, 16380, -16380])
        self.assertEqual(self.ledger.get(self.record["session_id"])["revision"], 0)

    def test_no_overwrite(self):
        self.execute()
        with self.assertRaises(IntegrityError):
            self.execute()
        self.assertEqual(len(list(self.output.iterdir())), 1)

    def test_changed_source_fails_closed(self):
        self.wav.write_bytes(b"changed")
        with self.assertRaises(IntegrityError):
            self.execute()
        self.assertEqual(list(self.output.iterdir()), [])

    def test_stale_revision_fails_closed(self):
        self.ledger.checkpoint(self.record["session_id"], 0, self.record["state"])
        with self.assertRaises(IntegrityError):
            self.execute()
        self.assertEqual(list(self.output.iterdir()), [])

    def test_invalid_gain_rejected(self):
        for gain in (-1, 1.1, float("nan"), "0.5"):
            with self.assertRaises(IntegrityError):
                self.execute(gain=gain)

    def test_output_inside_project_denied(self):
        with self.assertRaises(IntegrityError):
            self.execute(output_dir=self.source)

    def test_unrecorded_source_denied(self):
        with self.assertRaises(IntegrityError):
            self.execute(source_relative="other.wav")

    def test_unsupported_wav_cleans_staging(self):
        with wave.open(str(self.wav), "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(1)
            f.setframerate(22050)
            f.writeframes(b"1234")
        newer = capture_project(self.ledger, self.source, "test.flp",
                                session_id=self.record["session_id"], expected_revision=0,
                                assets=["stem.wav"])
        with self.assertRaises(IntegrityError):
            self.execute(expected_revision=1, expected_hash=newer["sha256"])
        self.assertEqual(list(self.output.iterdir()), [])
