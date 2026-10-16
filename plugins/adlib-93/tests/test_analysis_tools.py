import importlib.util
import math
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('analysis', Path(__file__).resolve().parents[1] / 'scripts/analyze_character.py')
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


class SpectrumCalibration(unittest.TestCase):
    def test_known_coherent_amplitudes_and_absent_bins(self):
        n = 4096
        signal = [.5 * math.sin(2 * math.pi * 509 * k / n) + .125 * math.sin(2 * math.pi * 37 * k / n) for k in range(n)]
        self.assertAlmostEqual(analysis.amplitude(signal, 509), .5, places=9)
        self.assertAlmostEqual(analysis.amplitude(signal, 37), .125, places=9)
        for bin_index in (1, 1551, 2047):
            self.assertLess(analysis.amplitude(signal, bin_index), 1e-10)


if __name__ == '__main__':
    unittest.main(verbosity=2)
