import copy
import csv
import importlib.util
import json
import hashlib
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('run_profile', Path(__file__).with_name('run_profile.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ProfileEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.csv = Path(self.directory.name) / 'raw.csv'
        rows = []
        modes = []
        for name in ['steady', 'transitions']:
            rows += [dict(mode=name, block=i, wall_ms=wall, thread_cycles=100+i, start_lag_ms=0) for i, wall in enumerate([1., 2.])]
            modes.append(dict(mode=name, blocks=2, finite=True, deadline_misses=0,
                              cycle_p50=100, cycle_p95=101, cycle_p99=101, cycle_max=101, start_lag_p99_ms=0.,
                              wall_outliers_gt_2x_median=0, low_cycle_wall_outliers_le_1_5x_median=0,
                              wall_p50_ms=1., wall_p95_ms=2., wall_p99_ms=2., wall_max_ms=2., output_fnv1a64='abc'))
        with self.csv.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
        self.report = dict(diagnostic_only=True, release_qualified=False, cpu_budget='PENDING',
                           sample_rate=8, block_size=4, seconds_per_mode=1, warmup_audio_seconds=3,
                           deadline_ms=500., cycles_enabled=True, paced=True, modes=modes)

    def test_valid_raw_evidence(self):
        self.assertEqual(4, module.validate_report(self.report, self.csv)['raw_rows'])

    def test_release_promotion_rejected(self):
        self.report['release_qualified'] = True
        with self.assertRaises(ValueError): module.validate_report(self.report, self.csv)

    def test_deadline_definition_rejected(self):
        self.report['deadline_ms'] = 499.
        with self.assertRaisesRegex(ValueError, 'deadline'): module.validate_report(self.report, self.csv)

    def test_missing_rows_rejected(self):
        self.csv.write_text('mode,block,wall_ms,thread_cycles,start_lag_ms\n')
        with self.assertRaisesRegex(ValueError, 'rows'): module.validate_report(self.report, self.csv)

    def test_duplicate_block_sequence_rejected(self):
        self.csv.write_text(self.csv.read_text().replace('steady,1,', 'steady,0,'))
        with self.assertRaisesRegex(ValueError, 'sequence'): module.validate_report(self.report, self.csv)

    def test_nonfinite_raw_timing_rejected(self):
        self.csv.write_text(self.csv.read_text().replace('steady,0,1.0,', 'steady,0,nan,'))
        with self.assertRaisesRegex(ValueError, 'timing'): module.validate_report(self.report, self.csv)

    def test_quantile_tampering_rejected(self):
        self.report['modes'][0]['wall_p99_ms'] = 99.
        with self.assertRaisesRegex(ValueError, 'quantile'): module.validate_report(self.report, self.csv)

    def test_cycle_quantile_tampering_rejected(self):
        self.report['modes'][0]['cycle_p99'] = 999
        with self.assertRaisesRegex(ValueError, 'Cycle quantile'): module.validate_report(self.report, self.csv)

    def test_lag_quantile_tampering_rejected(self):
        self.report['modes'][0]['start_lag_p99_ms'] = 99.
        with self.assertRaisesRegex(ValueError, 'Lag quantile'): module.validate_report(self.report, self.csv)

    def test_outlier_count_tampering_rejected(self):
        for field in ['wall_outliers_gt_2x_median', 'low_cycle_wall_outliers_le_1_5x_median']:
            with self.subTest(field=field):
                changed = copy.deepcopy(self.report); changed['modes'][0][field] = 1
                with self.assertRaisesRegex(ValueError, 'Outlier counts'): module.validate_report(changed, self.csv)

    def test_disabled_cycles_must_be_zero(self):
        self.report['cycles_enabled'] = False
        with self.assertRaisesRegex(ValueError, 'Disabled cycle'): module.validate_report(self.report, self.csv)

    def test_deadline_miss_tampering_rejected(self):
        self.report['modes'][0]['deadline_misses'] = 1
        with self.assertRaisesRegex(ValueError, 'miss count'): module.validate_report(self.report, self.csv)

    def test_instrumentation_continuity(self):
        control = copy.deepcopy(self.report); control['cycles_enabled'] = False
        self.assertTrue(module.compare_output(control, self.report)['synthetic_fingerprints_equal'])
        self.assertFalse(module.compare_output(control, self.report)['cryptographic_audio_golden'])

    def test_changed_audio_fingerprint_rejected(self):
        changed = copy.deepcopy(self.report); changed['modes'][0]['output_fnv1a64'] = 'different'
        with self.assertRaisesRegex(ValueError, 'fingerprint'): module.compare_output(self.report, changed)

    def test_different_profile_comparison_rejected(self):
        changed = copy.deepcopy(self.report); changed['paced'] = False
        with self.assertRaisesRegex(ValueError, 'configurations'): module.compare_output(self.report, changed)

    def test_cycles_must_not_be_negative(self):
        self.csv.write_text(self.csv.read_text().replace('steady,0,1.0,100,', 'steady,0,1.0,-1,'))
        with self.assertRaisesRegex(ValueError, 'cycle'): module.validate_report(self.report, self.csv)

    def frozen(self):
        root = Path(self.directory.name) / 'source'; root.mkdir()
        (root / 'one.h').write_bytes(b'original')
        records = [{'path': 'one.h', 'bytes': 8, 'sha256': module.sha(root / 'one.h')}]
        declared = {'files': records, 'content_sha256': hashlib.sha256(json.dumps(records, sort_keys=True, separators=(',', ':')).encode()).hexdigest()}
        return root, declared

    def test_source_manifest_hash_and_bytes_match(self):
        root, declared = self.frozen()
        self.assertEqual(declared['content_sha256'], module.verify_frozen_source(root, declared))

    def test_changed_frozen_source_rejected(self):
        root, declared = self.frozen(); (root / 'one.h').write_bytes(b'modified')
        with self.assertRaisesRegex(ValueError, 'differs'): module.verify_frozen_source(root, declared)

    def test_undeclared_source_file_rejected(self):
        root, declared = self.frozen(); (root / 'extra.h').write_bytes(b'injected')
        with self.assertRaisesRegex(ValueError, 'inventory'): module.verify_frozen_source(root, declared)

    def test_source_path_escape_rejected(self):
        root, declared = self.frozen(); declared['files'][0]['path'] = '../outside.h'
        with self.assertRaisesRegex(ValueError, 'Unsafe'): module.verify_frozen_source(root, declared)

    def test_source_manifest_digest_tamper_rejected(self):
        root, declared = self.frozen(); declared['content_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'manifest hash'): module.verify_frozen_source(root, declared)


if __name__ == '__main__': unittest.main()
