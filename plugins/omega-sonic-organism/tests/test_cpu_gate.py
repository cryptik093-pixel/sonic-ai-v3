"""Regression coverage for false release passes, without timing fixtures as proof."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("cpu_gate", Path(__file__).parents[1] / "tools/evaluate_cpu_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class GateTests(unittest.TestCase):
    def setUp(self):
        mode = dict(callbacks=5625, medianMs=.3, p95Ms=.8, p99Ms=1.5, maximumMs=3., overruns=0, nonFiniteFaults=0)
        self.input = dict(sampleRate=48000, frames=256, voices=16, secondsPerMode=30,
                          modes=[dict(mode, quality=q) for q in ("Eco", "HQ")])

    def test_synthetic_passing_fixture_only(self):
        self.assertEqual(gate.evaluate(self.input)["result"], "PASS")

    def test_failures_cannot_be_ignored(self):
        for field, value in (("p95Ms", 1.01), ("p99Ms", 2.01), ("overruns", 1),
                             ("maximumMs", 6.), ("nonFiniteFaults", 1), ("callbacks", 5624),
                             ("medianMs", float("nan"))):
            with self.subTest(field=field):
                data = copy.deepcopy(self.input)
                data["modes"][1][field] = value
                self.assertEqual(gate.evaluate(data)["result"], "FAIL")

    def test_workload_cannot_be_reduced(self):
        for field, value in (("voices", 8), ("frames", 1024), ("sampleRate", 44100),
                             ("secondsPerMode", 1), ("modes", [self.input["modes"][0]]),
                             ("modes", [])):
            with self.subTest(field=field):
                data = copy.deepcopy(self.input)
                data[field] = value
                self.assertEqual(gate.evaluate(data)["result"], "FAIL")


if __name__ == "__main__":
    unittest.main()
