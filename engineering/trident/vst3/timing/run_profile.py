"""Build and validate a Windows-only diagnostic against a retained tested core.

No source, library, installed plugin, DAW state or power configuration is changed.
The caller must enter the existing process-local x64 compiler environment first.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import platform
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import time


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def validate_report(report, csv_path):
    if report.get('diagnostic_only') is not True or report.get('release_qualified') is not False or report.get('cpu_budget') != 'PENDING':
        raise ValueError('Diagnostic must never promote release qualification')
    rate, block = report['sample_rate'], report['block_size']
    if rate <= 0 or block <= 0 or not math.isclose(report['deadline_ms'], 1000 * block / rate, rel_tol=1e-10):
        raise ValueError('Invalid sample rate, block size or callback deadline')
    expected = math.ceil(report['seconds_per_mode'] * rate / block)
    modes = report['modes']
    if [r['mode'] for r in modes] != ['steady', 'transitions']:
        raise ValueError('Both independent modes are required')
    with Path(csv_path).open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != expected * 2:
        raise ValueError('Missing or duplicate raw timing rows')
    for result in modes:
        name = result['mode']
        selected = [r for r in rows if r['mode'] == name]
        if len(selected) != expected or [int(r['block']) for r in selected] != list(range(expected)):
            raise ValueError('Raw block sequence does not match report')
        if result['blocks'] != expected or result['finite'] is not True:
            raise ValueError('Invalid mode count or nonfinite audio')
        wall = [float(r['wall_ms']) for r in selected]
        cycles = [int(r['thread_cycles']) for r in selected]
        lag = [float(r['start_lag_ms']) for r in selected]
        if not all(math.isfinite(v) and v >= 0 for v in wall + lag) or any(v < 0 for v in cycles):
            raise ValueError('Invalid timing/cycle observation')
        if result['deadline_misses'] != sum(v > report['deadline_ms'] for v in wall):
            raise ValueError('Deadline miss count differs from raw data')
        ordered = sorted(wall)
        for suffix, q in [('p50', .5), ('p95', .95), ('p99', .99), ('max', 1.)]:
            actual = ordered[math.ceil(expected * q) - 1]
            if not math.isclose(result[f'wall_{suffix}_ms'], actual, rel_tol=1e-9, abs_tol=1e-9):
                raise ValueError('Wall quantile differs from raw data')
        ordered_cycles = sorted(cycles)
        for suffix, q in [('p50', .5), ('p95', .95), ('p99', .99), ('max', 1.)]:
            if result[f'cycle_{suffix}'] != ordered_cycles[math.ceil(expected * q) - 1]:
                raise ValueError('Cycle quantile differs from raw data')
        if not math.isclose(result['start_lag_p99_ms'], sorted(lag)[math.ceil(expected * .99) - 1], rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError('Lag quantile differs from raw data')
        median_wall = ordered[math.ceil(expected * .5) - 1]
        median_cycles = ordered_cycles[math.ceil(expected * .5) - 1]
        outliers = [i for i, value in enumerate(wall) if value > 2 * median_wall]
        low_cycles = sum(report['cycles_enabled'] and median_cycles > 0 and cycles[i] <= 1.5 * median_cycles for i in outliers)
        if result['wall_outliers_gt_2x_median'] != len(outliers) or result['low_cycle_wall_outliers_le_1_5x_median'] != low_cycles:
            raise ValueError('Outlier counts differ from raw data')
        if not report['cycles_enabled'] and any(cycles):
            raise ValueError('Disabled cycle capture contains observations')
        if report['cycles_enabled'] and not any(cycles):
            raise ValueError('Cycle counter recorded no positive observations')
    return {'modes': 2, 'raw_rows': len(rows), 'validated': True}


def compare_output(a, b):
    fields = ('sample_rate', 'block_size', 'seconds_per_mode', 'warmup_audio_seconds', 'paced')
    if any(a.get(f) != b.get(f) for f in fields):
        raise ValueError('Fingerprint comparison configurations differ')
    left = [(r['mode'], r['blocks'], r['output_fnv1a64']) for r in a['modes']]
    right = [(r['mode'], r['blocks'], r['output_fnv1a64']) for r in b['modes']]
    if left != right:
        raise ValueError('Instrumentation changed synthetic output fingerprint')
    return {'synthetic_fingerprints_equal': True, 'cryptographic_audio_golden': False}


def verify_frozen_source(source, declared):
    records = declared['files']
    expected = {}
    if source.is_symlink() or source.is_junction():
        raise ValueError('Linked frozen source is forbidden')
    for record in records:
        relative = PurePosixPath(record['path'])
        if relative.is_absolute() or '..' in relative.parts or ':' in str(relative) or '\\' in str(relative) or not relative.parts:
            raise ValueError('Unsafe frozen-source manifest path')
        target = source.joinpath(*relative.parts)
        for parent in [target, *list(target.parents)[:len(relative.parts)-1]]:
            if parent.is_symlink() or parent.is_junction():
                raise ValueError('Linked frozen-source input is forbidden')
        if str(relative).casefold() in expected:
            raise ValueError('Duplicate frozen-source identity')
        if target.stat().st_size != record['bytes'] or sha(target) != record['sha256']:
            raise ValueError('Frozen source differs from passing baseline')
        expected[str(relative).casefold()] = record
    actual = set()
    for item in source.rglob('*'):
        if item.is_symlink() or item.is_junction():
            raise ValueError('Linked frozen-source input is forbidden')
        if item.is_file():
            actual.add(item.relative_to(source).as_posix().casefold())
    if not records or actual != set(expected):
        raise ValueError('Frozen source inventory differs from passing baseline')
    encoded = json.dumps(records, sort_keys=True, separators=(',', ':')).encode()
    if hashlib.sha256(encoded).hexdigest() != declared['content_sha256']:
        raise ValueError('Baseline source manifest hash is invalid')
    return declared['content_sha256']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--seconds', type=int, default=30, choices=range(1, 121))
    args = parser.parse_args()
    baseline = args.baseline.resolve(strict=True)
    report_path = baseline / 'report.json'
    retained = json.loads(report_path.read_text(encoding='utf-8'))
    if retained['status'] != 'PASS' or retained['product'] != 'adlib-93-core':
        raise RuntimeError('Retained baseline did not pass')
    source = baseline / 'source'
    source_identity = verify_frozen_source(source, retained['build_source_manifest'])
    library = baseline / 'build' / 'adlib93_dsp.lib'
    compiler = shutil.which('cl.exe')
    if not compiler or sys.platform != 'win32':
        raise RuntimeError('Enter the existing Windows x64 compiler environment')
    own_source = Path(__file__).with_name('ProfileADLIB.cpp').resolve(strict=True)
    tracked = [report_path, library, own_source, Path(__file__).resolve(), Path(compiler)] + sorted((source / 'src').rglob('*.h')) + sorted((source / 'src').rglob('*.cpp'))
    before = {str(p): sha(p) for p in tracked}
    output = args.output.resolve()
    if output == baseline or baseline in output.parents or output in baseline.parents:
        raise RuntimeError('Evidence output must be separate from baseline')
    output.mkdir(parents=True, exist_ok=False)
    record = {'schema': 1, 'status': 'RUNNING', 'release_qualified': False,
              'baseline': str(baseline), 'core_linkage': 'Retained tested core library; not a fresh native VST3 build',
              'frozen_source_manifest_sha256': source_identity,
              'environment': {'platform': platform.platform(), 'processor_identifier': os.environ.get('PROCESSOR_IDENTIFIER'),
                              'logical_processors': os.cpu_count(), 'priority_or_power_changed': False},
              'hashes_before': before, 'commands': [], 'started_unix': time.time()}
    evidence = output / 'run.json'

    def run(command, label, expected=0, timeout=300):
        log = output / (label + '.log')
        argv = [str(x) for x in command]
        item = {'argv': argv, 'log': str(log)}
        record['commands'].append(item)
        with log.open('x', encoding='utf-8') as stream:
            process = subprocess.Popen(argv, cwd=output, stdout=stream, stderr=subprocess.STDOUT)
            item['pid'] = process.pid
            try:
                item['exit_code'] = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                item['timed_out'] = True
                cleanup = subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                         stdout=stream, stderr=subprocess.STDOUT, timeout=20)
                item['tree_cleanup_exit'] = cleanup.returncode
                process.wait(timeout=20)
                raise RuntimeError(f'{label} timed out; only its owned process tree was targeted')
        if item['exit_code'] != expected:
            raise RuntimeError(f"{label} returned {item['exit_code']}; see retained log")

    try:
        exe = output / 'profile_adlib.exe'
        run([compiler, '/nologo', '/std:c++17', '/EHsc', '/O2', '/MT', '/DNDEBUG', '/Zc:__cplusplus', '/W4',
             '/I' + str(source / 'src'), str(own_source), str(library), '/Fe:' + str(exe), '/Fo:' + str(output / 'profile.obj')], 'compile')
        run([exe, '--self-test'], 'self-test')
        outputs = []
        for label, seconds, cycle_flag in [('control-off', 2, 'false'), ('control-on', 2, 'true'), ('measurement', args.seconds, 'true')]:
            destination = output / (label + '.json')
            raw = output / (label + '.csv')
            run([exe, '--report', destination, '--csv', raw, '--seconds', seconds, '--warmup', '3', '--paced', 'true', '--cycles', cycle_flag], label, timeout=max(120, seconds * 6))
            value = json.loads(destination.read_text())
            record[label] = validate_report(value, raw)
            outputs.append(value)
        record['continuity'] = compare_output(outputs[0], outputs[1])
        control = output / 'control-on.json'
        control_hash = sha(control)
        run([exe, '--report', control, '--csv', output / 'must-not-clobber.csv', '--seconds', '1'], 'reject-existing-output', expected=1)
        if sha(control) != control_hash:
            raise RuntimeError('Existing evidence was changed')
        run([exe, '--seconds', '-1', '--report', output / 'invalid.json', '--csv', output / 'invalid.csv'], 'reject-negative-number', expected=1)
        record['hashes_after'] = {str(p): sha(p) for p in tracked}
        verify_frozen_source(source, retained['build_source_manifest'])
        if before != record['hashes_after']:
            raise RuntimeError('Baseline/library/tool inputs changed during diagnostic')
        record['artifact_sha256'] = {p.name: sha(p) for p in sorted(output.iterdir())
                                     if p.is_file() and p.suffix in ('.json', '.csv', '.log', '.exe') and p != evidence}
        record['exe_sha256'] = sha(exe)
        record['status'] = 'PASS_DIAGNOSTIC_COLLECTION_ONLY'
    except Exception as error:
        record['status'] = 'FAIL'
        record['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        record['finished_unix'] = time.time()
        evidence.write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps({'status': record['status'], 'output': str(output), 'release_qualified': False}))


if __name__ == '__main__':
    main()
