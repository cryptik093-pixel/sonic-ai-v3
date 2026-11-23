import importlib.util
from pathlib import Path
import tempfile
import struct
import json
import unittest

spec = importlib.util.spec_from_file_location('pipeline', Path(__file__).with_name('pipeline.py'))
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


class EvidenceTests(unittest.TestCase):
    def test_bundle_hash_covers_resources_and_names(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'plugin.vst3').write_bytes(b'module')
            (root / 'resource.json').write_bytes(b'one')
            initial = pipeline.manifest(root)['content_sha256']
            (root / 'resource.json').write_bytes(b'two')
            self.assertNotEqual(initial, pipeline.manifest(root)['content_sha256'])
            initial = pipeline.manifest(root)['content_sha256']
            (root / 'resource.json').rename(root / 'other.json')
            self.assertNotEqual(initial, pipeline.manifest(root)['content_sha256'])

    def test_audio_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            a, b = Path(temp) / 'a', Path(temp) / 'b'
            a.write_bytes(b'pcm'); b.write_bytes(b'pcm')
            self.assertEqual(pipeline.compare_files(a, b)['status'], 'PASS')
            b.write_bytes(b'changed')
            self.assertEqual(pipeline.compare_files(a, b)['status'], 'FAIL')

    def test_empty_artifact_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                pipeline.manifest(Path(temp))

    def test_existing_evidence_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(FileExistsError):
                pipeline.Run(Path(temp))

    def test_missing_source_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                pipeline.selected_files(Path(temp), ['missing'])

    def test_nonfinite_audio_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'bad.wav'
            fmt = struct.pack('<HHIIHH', 3, 2, 48000, 384000, 8, 32)
            pcm = struct.pack('<ff', float('nan'), 0.)
            body = b'WAVEfmt ' + struct.pack('<I', len(fmt)) + fmt + b'data' + struct.pack('<I', len(pcm)) + pcm
            path.write_bytes(b'RIFF' + struct.pack('<I', len(body)) + body)
            with self.assertRaisesRegex(ValueError, 'Nonfinite'):
                pipeline.validate_float_wave(path)

    def test_executable_location_must_be_unambiguous(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'tool.exe').write_bytes(b'one')
            self.assertEqual(pipeline.executable(root, 'tool.exe'), str(root / 'tool.exe'))
            (root / 'bin').mkdir()
            (root / 'bin/tool.exe').write_bytes(b'two')
            with self.assertRaises(ValueError):
                pipeline.executable(root, 'tool.exe')

    def test_failed_command_is_persisted(self):
        with tempfile.TemporaryDirectory() as temp:
            run = pipeline.Run(Path(temp) / 'new')
            with self.assertRaises(RuntimeError):
                run.command('negative', [pipeline.sys.executable, '-c', 'raise SystemExit(7)'])
            self.assertEqual(run.report['commands'][0]['exit_code'], 7)
            self.assertTrue((run.output / 'report.json').is_file())

    def test_timeout_retains_failure_and_stops_owned_process(self):
        with tempfile.TemporaryDirectory() as temp:
            run = pipeline.Run(Path(temp) / 'new')
            with self.assertRaises(pipeline.subprocess.TimeoutExpired):
                run.command('timeout', [pipeline.sys.executable, '-c', 'import time; time.sleep(60)'], timeout=.1)
            row = run.report['commands'][0]
            self.assertEqual(row['error'], 'TIMEOUT')
            self.assertIsNone(row['exit_code'])
            self.assertIn('finished_utc', row)

    def test_resume_rejects_active_or_changed_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'source').mkdir(); (root / 'build').mkdir()
            (root / 'source/file.cpp').write_text('original')
            expected = pipeline.manifest(root / 'source')
            data = {'status': 'RUNNING', 'product': 'eq', 'build_source_manifest': expected}
            (root / 'report.json').write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                pipeline.resume_paths(root, 'eq', expected)
            data['status'] = 'FAIL'
            (root / 'report.json').write_text(json.dumps(data))
            self.assertEqual(pipeline.resume_paths(root, 'eq', expected), (root / 'source', root / 'build'))
            (root / 'source/file.cpp').write_text('changed')
            with self.assertRaises(ValueError):
                pipeline.resume_paths(root, 'eq', expected)


if __name__ == '__main__':
    unittest.main()
