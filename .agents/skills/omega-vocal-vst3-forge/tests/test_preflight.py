from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from preflight import run


class PreflightTests(unittest.TestCase):
    def test_detects_manifest_without_writing_to_repo(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "CMakeLists.txt").write_text("project(test)\n", encoding="utf-8")
            before = sorted(path.name for path in root.iterdir())
            report = run(root)
            after = sorted(path.name for path in root.iterdir())
            self.assertEqual(before, after)
            self.assertTrue(report["read_only"])
            self.assertIn("CMakeLists.txt", report["top_level_markers"]["CMakeLists.txt"])

    def test_missing_directory_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                run(Path(folder) / "absent")


if __name__ == "__main__":
    unittest.main()
