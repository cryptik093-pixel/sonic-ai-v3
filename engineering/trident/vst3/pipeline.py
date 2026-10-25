"""Isolated local Release baseline. PASS here never authorizes a release."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import platform
from pathlib import Path
import shutil
import subprocess
import struct
import sys
import wave

HERE = Path(__file__).resolve().parent
SDK_SHA = '64965f1b74e08a6d4087a35af7a716f4dcff5852c66ad7ee13f1c47e79c1ab77'


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def manifest(root: Path, excluded_parts: tuple[str, ...] = ()) -> dict:
    if root.is_symlink() or root.is_junction():
        raise ValueError(f'Linked root is not reproducible: {root}')
    files = []
    for path in sorted(root.rglob('*')):
        if any(part in excluded_parts for part in path.relative_to(root).parts):
            continue
        if path.is_symlink() or path.is_junction():
            raise ValueError(f'Linked input is not reproducible: {path}')
        if path.is_file():
            files.append({'path': path.relative_to(root).as_posix(),
                          'bytes': path.stat().st_size, 'sha256': digest(path)})
    if not files:
        raise ValueError(f'Empty artifact/input: {root}')
    # Content digest is SHA256 of canonical UTF-8 JSON records, without newline.
    payload = json.dumps(files, sort_keys=True, separators=(',', ':')).encode()
    return {'files': files, 'content_sha256': hashlib.sha256(payload).hexdigest()}


def compare_files(left: Path, right: Path) -> dict:
    result = {'left_sha256': digest(left), 'right_sha256': digest(right)}
    result['status'] = 'PASS' if result['left_sha256'] == result['right_sha256'] else 'FAIL'
    return result


def executable(build: Path, name: str) -> str:
    candidates = [build / name, build / 'bin' / name, build / 'bin' / 'Release' / name]
    found = [p for p in candidates if p.is_file()]
    if len(found) != 1:
        raise ValueError(f'Expected one executable for {name}: {found}')
    return str(found[0])


def validate_float_wave(path: Path) -> dict:
    raw = path.read_bytes()
    if raw[:4] != b'RIFF' or raw[8:12] != b'WAVE' or len(raw) != struct.unpack_from('<I', raw, 4)[0] + 8:
        raise ValueError('Malformed WAV container')
    offset, fmt, pcm = 12, None, None
    while offset + 8 <= len(raw):
        tag, size = struct.unpack_from('<4sI', raw, offset)
        payload = raw[offset + 8:offset + 8 + size]
        if len(payload) != size:
            raise ValueError('Truncated WAV chunk')
        if tag == b'fmt ':
            fmt = struct.unpack_from('<HHIIHH', payload)
        if tag == b'data':
            pcm = payload
        offset += 8 + size + size % 2
    if fmt is None or fmt[0] != 3 or fmt[1] != 2 or fmt[5] != 32 or not pcm or len(pcm) % 8:
        raise ValueError('Expected nonempty float32 stereo WAV')
    peak = 0.
    for (value,) in struct.iter_unpack('<f', pcm):
        if not math.isfinite(value):
            raise ValueError('Nonfinite rendered audio')
        peak = max(peak, abs(value))
    if peak > 100:
        raise ValueError('Unbounded rendered audio')
    return {'frames': len(pcm) // 8, 'sample_rate': fmt[2], 'peak': peak, 'sha256': digest(path)}


def selected_files(product: Path, inputs: list[str]) -> list[Path]:
    result = []
    for name in inputs:
        source = product / name
        if not source.exists():
            raise ValueError(f'Required input missing: {source}')
        for path in ([source] if source.is_file() else [source, *source.rglob('*')]):
            if path.is_symlink() or path.is_junction():
                raise ValueError(f'Linked source forbidden: {path}')
            if path.is_file():
                result.append(path)
    return sorted(set(result))


def resume_paths(previous: Path, product: str, source_manifest: dict) -> tuple[Path, Path]:
    report = json.loads((previous / 'report.json').read_text())
    if report.get('status') not in ('PASS', 'FAIL') or report.get('product') != product:
        raise ValueError('Resume requires a completed run for the same product')
    source, build = previous / 'source', previous / 'build'
    if not build.is_dir() or build.is_symlink() or build.is_junction() or manifest(source) != source_manifest:
        raise ValueError('Resume source does not match the newly captured build inputs')
    if report.get('build_source_manifest') != source_manifest:
        raise ValueError('Resume source differs from its recorded manifest')
    return source, build


class Run:
    def __init__(self, output: Path):
        # Never reuse an evidence directory or allow build output in source/install trees.
        output.mkdir(parents=True, exist_ok=False)
        self.output = output
        self.report = {'schema': 1, 'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                       'status': 'RUNNING', 'commands': [], 'host_test': 'NOT_TESTED',
                       'cpu_measurement': 'NOT_TESTED', 'approved_audio_golden': 'NOT_PROVIDED',
                       'design_acceptance': 'NOT_TESTED', 'release_qualified': False}
        self.save()

    def save(self):
        (self.output / 'report.json').write_text(json.dumps(self.report, indent=2) + '\n')

    def command(self, label: str, args: list[str], timeout: int = 600) -> str:
        log = self.output / f'{len(self.report["commands"]):02}-{label}.log'
        row = {'argv': [str(x) for x in args], 'log': log.name,
               'cwd': str(self.output), 'started_utc': dt.datetime.now(dt.timezone.utc).isoformat()}
        self.report['commands'].append(row)
        self.save()
        print(f'{label}: running', flush=True)
        with log.open('w', encoding='utf-8') as stream:
            try:
                proc = subprocess.Popen(row['argv'], cwd=self.output, stdout=stream, stderr=subprocess.STDOUT)
                row['pid'] = proc.pid
                try:
                    row['exit_code'] = proc.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    # Terminate only this runner-owned command tree. Killing cmake
                    # alone can leave Ninja/compiler children running after timeout.
                    if os.name == 'nt':
                        subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'],
                                       stdout=stream, stderr=subprocess.STDOUT, timeout=30, check=False)
                    proc.kill()
                    proc.wait(timeout=30)
                    raise
            except subprocess.TimeoutExpired:
                row['exit_code'] = None
                row['error'] = 'TIMEOUT'
                raise
            finally:
                row['finished_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
                self.save()
        print(f'{label}: exit {proc.returncode}', flush=True)
        if proc.returncode:
            raise RuntimeError(f'{label} failed; see {log}')
        return log.read_text(encoding='utf-8', errors='replace')


def execute(args):
    repo, output = args.repo.resolve(), args.output.resolve()
    protected = [repo, Path(os.environ.get('ProgramFiles', r'C:\Program Files')),
                 Path(os.environ.get('CommonProgramFiles', r'C:\Program Files\Common Files')),
                 Path(os.environ.get('LOCALAPPDATA', r'C:\Users\Default\AppData\Local')) / 'Programs']
    if any(output == p or output.is_relative_to(p) for p in protected):
        raise ValueError('Output must be a new directory outside source and installed programs')
    run = Run(output)
    lock_fd, lock_path = None, None
    try:
        config = json.loads((HERE / 'products.json').read_text())[args.product]
        product = repo / config['path']
        run.report['product'] = args.product
        run.report['environment'] = {'windows': platform.platform(), 'python': sys.version,
                                     'processor': os.environ.get('PROCESSOR_IDENTIFIER'),
                                     'build_workers': args.jobs, 'test_workers': 1}
        run.report['coverage'] = 'VST3_AND_CORE' if config.get('bundle') else 'CORE_ONLY_NO_VST3_ARTIFACT'
        run.report['audio_regression'] = {'status': 'NOT_TESTED'}
        for name, argv in [('base_commit', ['git', '-C', str(repo), 'rev-parse', 'HEAD']),
                           ('branch', ['git', '-C', str(repo), 'branch', '--show-current']),
                           ('working_tree', ['git', '-C', str(repo), 'status', '--porcelain=v1'])]:
            run.report[name] = run.command(name, argv).strip()
        for tool, argv in [('cmake', ['cmake', '--version']), ('ninja', ['ninja', '--version']),
                           ('python', [sys.executable, '--version'])]:
            run.report[tool] = {'version': run.command(tool, argv).strip(),
                                'path': shutil.which(argv[0]), 'sha256': digest(Path(shutil.which(argv[0])))}
        compiler = Path(shutil.which('cl.exe') or '')
        if not compiler.is_file():
            raise ValueError('Use build-release.ps1 to prepare MSVC x64')
        run.report['compiler'] = {'path': str(compiler), 'sha256': digest(compiler)}
        run.report['pipeline'] = manifest(HERE, ('__pycache__',))
        dependencies = [repo / 'engineering/vst3/scripts/enter-windows.ps1']
        if config.get('bundle'):
            dependencies += [repo / 'plugins/omega-vocal-forge/tools/verify-sdk.py',
                             repo / 'plugins/omega-vocal-forge/dependencies.lock.json',
                             repo / 'engineering/vst3/skills/omega-vst-qa/scripts/validate_vst3.py']
        run.report['external_tooling'] = {str(p): digest(p) for p in dependencies}
        snapshot = output / 'source'
        snapshot.mkdir()
        originals = {}
        for source in selected_files(product, config['inputs']):
            relative = source.relative_to(product)
            target = snapshot / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            before = digest(source)
            shutil.copyfile(source, target)
            if digest(target) != before or digest(source) != before:
                raise RuntimeError(f'Source changed during snapshot: {relative}')
            originals[relative.as_posix()] = before
        run.report['source_manifest'] = manifest(snapshot)
        build = output / 'build'
        configure = ['cmake', '-S', str(snapshot), '-B', str(build), '-G', 'Ninja',
                     '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
                     '-DBUILD_TESTING=ON', '-DSMTG_CREATE_PLUGIN_LINK=OFF',
                     '-DJUCE_COPY_PLUGIN_AFTER_BUILD=OFF']
        configure += [f'-D{k}={v}' for k, v in config['definitions'].items()]
        if config.get('sdk_variable'):
            sdk = repo / 'plugins/sonic-pocket/build/steinberg/VST_SDK/vst3sdk'
            archive = repo / 'plugins/sonic-pocket/build/steinberg-sdk.zip'
            if digest(archive) != SDK_SHA:
                raise ValueError('Pinned SDK archive mismatch')
            run.report['sdk_archive_sha256'] = SDK_SHA
            configure.append(f'-D{config["sdk_variable"]}={sdk}')
            if (snapshot / 'tools/TridentRender.cpp').exists():
                raise ValueError('Renderer target conflicts with an existing product file')
            shutil.copyfile(HERE / 'RenderEQ.cpp', snapshot / 'tools/TridentRender.cpp')
            with (snapshot / 'CMakeLists.txt').open('a') as stream:
                stream.write('\nadd_executable(trident_eq_render tools/TridentRender.cpp "${OEQ_SDK_ROOT}/public.sdk/source/common/memorystream.cpp")\n'
                             'target_include_directories(trident_eq_render PRIVATE "${OEQ_SDK_ROOT}" src)\n'
                             'target_compile_definitions(trident_eq_render PRIVATE UNICODE _UNICODE NOMINMAX)\n'
                             'target_link_libraries(trident_eq_render PRIVATE sdk sdk_hosting ole32)\n')
        run.report['build_source_manifest'] = manifest(snapshot)
        if args.resume_from:
            previous = args.resume_from.resolve()
            if any(previous == p or previous.is_relative_to(p) for p in protected):
                raise ValueError('Resume cache must be outside source and installed programs')
            snapshot, build = resume_paths(previous, args.product, run.report['build_source_manifest'])
            run.report['resumed_from'] = str(previous)
            # Keep the failed report/logs immutable; only its isolated build cache
            # is reused. Reconfigure against its original, hash-identical source.
            configure[configure.index('-S') + 1] = str(snapshot)
            configure[configure.index('-B') + 1] = str(build)
        run.report['build_source_directory'] = str(snapshot)
        run.report['build_directory'] = str(build)
        build.mkdir(parents=True, exist_ok=True)
        lock_path = build / '.trident-build.lock'
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(lock_fd, str(os.getpid()).encode())
        run.command('configure', configure)
        run.command('build', ['cmake', '--build', str(build), '--config', 'Release',
                             '--parallel', str(args.jobs), '--target', *config['targets']], timeout=3600)
        listing = run.command('test-inventory', ['ctest', '--test-dir', str(build), '-N', '--show-only=json-v1'])
        if not json.loads(listing)['tests']:
            raise ValueError('CTest registered zero tests')
        run.command('ctest', ['ctest', '--test-dir', str(build), '-C', 'Release', '--parallel', '1',
                              '--output-on-failure', '--no-tests=error', '--timeout', '120',
                              '--output-junit', str(output / 'ctest.xml')])
        run.report['tests'] = {'status': 'PASS', 'registered': len(json.loads(listing)['tests'])}
        if args.product == 'adlib-93-core':
            stimulus = output / 'synthetic-input.wav'
            with wave.open(str(stimulus), 'wb') as stream:
                stream.setparams((2, 2, 48000, 0, 'NONE', 'not compressed'))
                stream.writeframes(b''.join(struct.pack('<hh', int(2000 * math.sin(2 * math.pi * 173 * n / 48000)),
                                                       int(1600 * math.sin(2 * math.pi * 997 * n / 48000))) for n in range(12000)))
            renders = []
            for preset in [1, 24]:
                paths = []
                for block in [64, 511]:
                    path = output / f'preset-{preset}-block-{block}.wav'
                    run.command(f'render-{preset}-{block}', [executable(build, 'adlib93_render.exe'),
                        '--preset', str(preset), '--input', str(stimulus), '--output', str(path),
                        '--sample-rate', '48000', '--block-size', str(block), '--tail-seconds', '1'])
                    renders.append(validate_float_wave(path))
                    paths.append(path)
                if compare_files(*paths)['status'] != 'PASS':
                    raise ValueError('ADLIB render partition determinism failed')
            run.report['deterministic_render'] = {'status': 'PASS', 'scope': 'Core production path, two presets, two partitions, synthetic 48k stereo plus tail', 'renders': renders}
        if config.get('bundle'):
            bundle = build / config['bundle']
            module = bundle / config['module']
            run.report['bundle_before'] = manifest(bundle)
            run.report['module_sha256'] = digest(module)
            run.command('sdk-inputs', [sys.executable, str(repo / 'plugins/omega-vocal-forge/tools/verify-sdk.py'),
                                     str(archive), str(sdk), str(build), str(output / 'sdk-provenance.json')])
            validator = repo / 'plugins/sonic-pocket/build/steinberg-validator/bin/validator.exe'
            pluginval = repo / 'plugins/sonic-pocket/build/pluginval/pluginval.exe'
            qa = repo / 'engineering/vst3/skills/omega-vst-qa/scripts/validate_vst3.py'
            run.report['validator_tools'] = {str(p): digest(p) for p in [validator, pluginval, qa]}
            run.command('validators', [sys.executable, str(qa), '--bundle', str(bundle),
                        '--steinberg', str(validator), '--pluginval', str(pluginval),
                        '--strictness', '5', '--timeout', '300', '--output', str(output / 'validation')], timeout=720)
            run.command('artifact-probe', [executable(build, 'oeq_artifact_probe.exe'), str(module), str(output)])
            for label in ['render-a', 'render-b']:
                run.command(label, [executable(build, 'trident_eq_render.exe'), str(module), str(output / f'{label}.f32')])
            repeat = compare_files(output / 'render-a.f32', output / 'render-b.f32')
            run.report['deterministic_render'] = repeat
            if repeat['status'] != 'PASS':
                raise ValueError('Repeated DLL renders differ')
            if args.reference_module:
                reference = args.reference_module.resolve()
                reference_hash = digest(reference)
                run.command('render-reference', [executable(build, 'trident_eq_render.exe'), str(reference), str(output / 'render-reference.f32')])
                if digest(reference) != reference_hash:
                    raise ValueError('Reference module changed during render')
                comparison = compare_files(output / 'render-a.f32', output / 'render-reference.f32')
                comparison.update({'module': str(reference), 'module_sha256': reference_hash,
                                   'approval': 'UNAPPROVED_EXISTING_BINARY_REFERENCE'})
                run.report['audio_regression'] = comparison
                if comparison['status'] != 'PASS':
                    raise ValueError('Existing binary audio regression differs; review required')
            if manifest(bundle) != run.report['bundle_before']:
                raise ValueError('Bundle changed during validation')
        # Verify both snapshot inputs and originals, including additions/removals.
        current = {p.relative_to(product).as_posix(): digest(p) for p in selected_files(product, config['inputs'])}
        if current != originals or manifest(snapshot) != run.report['build_source_manifest']:
            raise ValueError('Product or snapshot source changed during validation')
        if {str(p): digest(p) for p in dependencies} != run.report['external_tooling']:
            raise ValueError('External build/validation tooling changed during validation')
        run.report['source_preservation'] = 'PASS'
        run.report['status'] = 'PASS'
    except Exception as error:
        run.report['status'] = 'FAIL'
        run.report['error'] = str(error)
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
            lock_path.unlink()
        run.report['finished_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        run.save()
    print(f'{run.report["status"]}: {output / "report.json"}', flush=True)
    return 0 if run.report['status'] == 'PASS' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--product', choices=json.loads((HERE / 'products.json').read_text()), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference-module', type=Path)
    parser.add_argument('--jobs', type=int, choices=[1, 2], default=1)
    parser.add_argument('--resume-from', type=Path)
    sys.exit(execute(parser.parse_args()))
