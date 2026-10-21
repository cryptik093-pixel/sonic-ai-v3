#!/usr/bin/env python3
"""Validate an explicit Windows VST3 bundle; retain evidence without host claims."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def safe_tree(path):
    path = Path(path).absolute()
    if not path.exists() or path.is_symlink():
        raise ValueError('Missing path or symlink: ' + str(path))
    root = path.resolve()
    for item in [path, *path.rglob('*')] if path.is_dir() else [path]:
        if item.is_symlink() or getattr(item, 'is_junction', lambda: False)():
            raise ValueError('Symlinks/junctions are not accepted: ' + str(item))
        if not item.resolve().is_relative_to(root):
            raise ValueError('Path escapes root: ' + str(item))
    return path


def bundle_binary(bundle):
    bundle = safe_tree(bundle)
    if not bundle.is_dir() or bundle.suffix.lower() != '.vst3':
        raise ValueError('Expected a .vst3 bundle directory')
    binary = bundle / 'Contents' / 'x86_64-win' / bundle.name
    if not binary.is_file():
        raise ValueError('Missing Windows x64 binary: ' + str(binary))
    return bundle, binary


def bundle_manifest(bundle):
    bundle = safe_tree(bundle)
    return {file.relative_to(bundle).as_posix(): sha256(file)
            for file in sorted(bundle.rglob('*')) if file.is_file()}


def tree_digest(manifest):
    return hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=True).encode('utf-8')).hexdigest()


def successful(name, output):
    """Tool-specific positive completion, never accept exit status alone."""
    if name == 'pluginval':
        return bool(re.search(r'^(?:All tests passed|SUCCESS(?:\s*!!|\s*:.*?)?)\s*$', output, re.I | re.M))
    passed = re.search(r'(\d+)\s+tests?\s+passed', output, re.I)
    failed = re.search(r'(\d+)\s+tests?\s+failed', output, re.I)
    return bool(passed and int(passed[1]) > 0 and failed and int(failed[1]) == 0)


def run_tool(name, executable, arguments, output, timeout):
    result = {'state': 'PENDING', 'reason': 'Tool executable unavailable',
              'path': str(executable) if executable else None, 'args': arguments,
              'version': None}
    if not executable or not Path(executable).is_file():
        return result
    executable = Path(executable).resolve()
    try:
        result.update(path=str(executable), sha256=sha256(executable))
    except OSError as error:
        result.update(state='FAIL', reason='Cannot hash tool: ' + str(error))
        return result
    env = os.environ.copy()
    for key in list(env):
        if key.upper() in {'SKIP_GUI_TESTS', 'DISABLED_TESTS', 'RANDOMISE', 'DATA_FILE', 'VST3VALIDATOR'}:
            del env[key]
    stdout, stderr = '', ''
    try:
        process = subprocess.run([str(executable), *arguments], capture_output=True,
                                 text=True, errors='replace', timeout=timeout,
                                 env=env, shell=False)
        stdout, stderr = process.stdout, process.stderr
        result['exitCode'] = process.returncode
        result['state'] = 'PASS' if process.returncode == 0 and successful(name, stdout + '\n' + stderr) else 'FAIL'
        result['reason'] = 'Positive completion summary and exit zero' if result['state'] == 'PASS' else 'Exit failure or positive completion summary missing'
    except subprocess.TimeoutExpired as error:
        stdout, stderr = error.stdout or '', error.stderr or ''
        result.update(state='FAIL', reason='Validation timed out', timeoutSeconds=timeout)
    except OSError as error:
        result.update(state='FAIL', reason=type(error).__name__ + ': ' + str(error))
    for label, value in [('stdout', stdout), ('stderr', stderr)]:
        if isinstance(value, bytes):
            value = value.decode('utf-8', errors='replace')
        file = output / (name + '-' + label + '.txt')
        file.write_text(value, encoding='utf-8')
        result[label] = file.name
        result[label + 'Sha256'] = sha256(file)
    banner = re.search(r'(?:pluginval|VST(?:3)?\s*(?:SDK|validator)?)\s*(?:version\s*)?v?(\d+\.\d+(?:\.\d+)?)', str(stdout), re.I)
    if banner:
        result['version'] = banner[1]
    return result


def validate(bundle, pluginval, steinberg, output, strictness=5, timeout=300):
    bundle, binary = bundle_binary(bundle)
    output = Path(output).absolute()
    if output.resolve().is_relative_to(bundle.resolve()):
        raise ValueError('Evidence output must be outside the plugin bundle')
    output.mkdir(parents=True, exist_ok=False)
    before = sha256(binary)
    files_before = bundle_manifest(bundle)
    pv_args = ['--strictness-level', str(strictness), '--random-seed', '0x504f434b',
               '--sample-rates', '44100,48000,96000', '--block-sizes', '64,128,256,512,1024',
               '--repeat', '1', '--timeout-ms', str(int(timeout * 1000)),
               '--output-dir', str(output), '--output-filename', 'pluginval.txt', '--validate', str(bundle)]
    tools = {name: run_tool(name, exe, args, output, timeout) for name, exe, args in
             [('pluginval', pluginval, pv_args), ('steinberg', steinberg, [str(bundle)])]}
    try:
        bundle_binary(bundle)
        after = sha256(binary)
        files_after = bundle_manifest(bundle)
    except (ValueError, OSError):
        after = None
        files_after = None
    states = [item['state'] for item in tools.values()]
    unchanged = before == after and files_before == files_after
    state = 'FAIL' if not unchanged or 'FAIL' in states else ('PENDING' if 'PENDING' in states else 'PASS')
    report = {'schemaVersion': 2, 'timestampUtc': datetime.now(timezone.utc).isoformat(),
              'state': state, 'bundle': str(bundle), 'binary': str(binary),
              'binarySha256Before': before, 'binarySha256After': after,
              'artifactUnchanged': unchanged, 'strictness': strictness,
              'bundleFilesBefore': files_before, 'bundleFilesAfter': files_after,
              'bundleSha256Before': tree_digest(files_before),
              'bundleSha256After': tree_digest(files_after) if files_after is not None else None,
              'guiTestsRequested': True, 'sampleRates': [44100, 48000, 96000],
              'blockSizes': [64, 128, 256, 512, 1024], 'tools': tools,
              'flStudio': 'PENDING', 'listening': 'PENDING', 'commercialRelease': 'PENDING'}
    (output / 'validation.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--pluginval')
    parser.add_argument('--steinberg')
    parser.add_argument('--output', required=True, help='New evidence directory; never overwritten')
    parser.add_argument('--strictness', type=int, choices=[5, 10], default=5)
    parser.add_argument('--timeout', type=float, default=300)
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('--timeout must be finite and positive')
    try:
        result = validate(args.bundle, args.pluginval, args.steinberg, args.output, args.strictness, args.timeout)
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps(result, indent=2))
    return {'PASS': 0, 'FAIL': 1, 'PENDING': 2}[result['state']]


if __name__ == '__main__':
    raise SystemExit(main())
