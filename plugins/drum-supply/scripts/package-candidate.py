"""Stage local evaluation/source ZIPs with allowlisted contents and read-back hashes."""
from __future__ import annotations
import datetime as dt
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import unicodedata
import wave
import zipfile

ROOT = Path(__file__).resolve().parents[1]
STAMP = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d-%H%M%S')
NAME = f'Drum-Shot-Supply-Co-0.3.0-{STAMP}'


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def copy_file(source: Path, destination: Path):
    if source.is_symlink() or not source.is_file():
        raise ValueError(f'Expected regular file: {source}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def tree(source: Path, destination: Path):
    for path in source.rglob('*'):
        if path.is_file():
            copy_file(path, destination / path.relative_to(source))


def manifest(folder: Path):
    rows = [{'path': p.relative_to(folder).as_posix(), 'bytes': p.stat().st_size, 'sha256': digest(p)}
            for p in sorted(folder.rglob('*')) if p.is_file() and p.name not in {'SHA256SUMS.json','SHA256SUMS.txt'}]
    (folder / 'SHA256SUMS.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    (folder / 'SHA256SUMS.txt').write_text(''.join(f"{row['sha256']}  {row['path']}\n" for row in rows), encoding='utf-8')


def archive(folder: Path, target: Path):
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED) as out:
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                out.write(path, path.relative_to(folder).as_posix())
    with zipfile.ZipFile(target) as check:
        keys = set()
        total = 0
        for entry in check.infolist():
            name = entry.filename
            parts = PurePosixPath(name)
            key = unicodedata.normalize('NFC', name).casefold()
            if (parts.is_absolute() or '..' in parts.parts or '\\' in name or ':' in name
                    or key in keys or stat.S_ISLNK(entry.external_attr >> 16)):
                raise ValueError(f'Unsafe archive entry: {name}')
            keys.add(key)
            total += entry.file_size
            if total > 256 * 1024 * 1024:
                raise ValueError('Archive expansion exceeds staging budget')
        if check.testzip() is not None:
            raise ValueError('ZIP CRC validation failed')
        for item in json.loads(check.read('SHA256SUMS.json')):
            content = check.read(item['path'])
            assert len(content) == item['bytes']
            assert hashlib.sha256(content).hexdigest() == item['sha256']
            if item['path'].endswith('.wav'):
                with wave.open(io.BytesIO(content)) as wav:
                    assert wav.getnchannels() in (1, 2) and wav.getnframes() > 0
                    assert len(wav.readframes(wav.getnframes())) == wav.getnframes() * wav.getnchannels() * wav.getsampwidth()
    return {'path': str(target), 'bytes': target.stat().st_size, 'sha256': digest(target)}


def main():
    report = ROOT / 'evidence/release-verification.json'
    results = json.loads(report.read_text())
    for gate in ('build', 'synthesis_dsp', 'legacy_dsp', 'sample_dsp', 'processor', 'validators', 'original_assets', 'text_integrity', 'windows_x64_pe', 'vst3_class_ids', 'offline_renders','wav_exports'):
        if results[gate] != 'PASS':
            raise RuntimeError(f'Refusing to package without a passing {gate} gate')
    destination = ROOT / 'dist' / NAME
    destination.mkdir(parents=True, exist_ok=False)
    validation=json.loads((Path(results['validation_directories'][-1])/'validation.json').read_text())
    binary=Path(validation.get('bundle',validation.get('bundlePath','')))
    if not binary.is_dir(): raise ValueError('Validated bundle directory missing')
    executable = binary / 'Contents/x86_64-win/DrumShotSupplyCo.vst3'
    if {p.relative_to(binary).as_posix():digest(p) for p in binary.rglob('*') if p.is_file()} != validation['bundleFilesAfter']:
        raise ValueError('Validated bundle contents changed')
    if digest(executable) != results['binary']['sha256']:
        raise ValueError('Binary changed after verification')
    for relative, expected in results['source_hashes'].items():
        if digest(ROOT / relative) != expected:
            raise ValueError(f'Source changed after verification: {relative}')
    release = destination / 'DrumShotSupplyCo'
    release.mkdir()
    tree(binary, release / 'Plugin' / binary.name)
    tree(ROOT / 'Assets', release / 'Samples')
    for document in (ROOT / 'docs').rglob('*'):
        if document.is_file() and document.name not in {'BASELINE_AND_REVISION.md','PRODUCT_AND_DESIGN_BRIEF.md','FEATURE_ACCEPTANCE.csv'}:
            copy_file(document, release / 'Documentation' / document.relative_to(ROOT / 'docs'))
    presets=list((ROOT / 'evidence/release-fixtures').glob('*.dhpreset'))
    if len(presets)<6: raise ValueError('Expected verified factory synthesis kits')
    for preset in presets:
        copy_file(preset, release / 'FactoryPresets' / preset.name)
    tree(ROOT / 'evidence/release-fixtures/FactoryAudio', release / 'FactoryKits')
    tree(ROOT / 'recovery', release / 'Validation/Recovery')
    for name in ('README.md', 'THIRD_PARTY_LICENSES.md'):
        copy_file(ROOT / name, release / name)
    tree(ROOT / 'notices', release / 'Third Party Notices')
    copy_file(report, release / 'Validation/release-verification.json')
    copy_file(ROOT / 'evidence/RELEASE_VERIFICATION.md', release / 'Validation/REPORT.md')
    fixtures = ROOT / 'evidence/release-fixtures'
    for file in fixtures.iterdir():
        if file.is_file() and file.suffix in {'.wav','.png','.json'}: copy_file(file, release/'Validation/Fixtures'/file.name)
    for name in ('synthesis-build-final.log','asan-run.log','release-processor.stdout.log','release-synthesis_dsp.stdout.log','release-legacy_dsp.stdout.log','release-sample_dsp.stdout.log'):
        copy_file(ROOT/'evidence'/name,release/'Validation'/name)
    for original,alias in [('MANUAL.md','UserManual.md'),('INSTALLATION.md','Installation.md'),('CHANGELOG.md','ReleaseNotes.md')]:
        copy_file(ROOT/'docs'/original,release/'Documentation'/alias)
    for name in ('BuildReport.md','DSPTests.md','VST3Validation.md','FLStudioAcceptance.md'):
        copy_file(ROOT/'evidence'/name,release/'Validation'/name)
    for validation in results.get('validation_directories', []):
        source = Path(validation).resolve()
        if not source.is_relative_to((ROOT / 'evidence').resolve()):
            raise ValueError('Validator evidence must stay within this plugin')
        tree(source, release / 'Validation' / source.name)
    manifest(release)
    copy_file(release/'SHA256SUMS.txt',release/'Checksums.sha256')
    manifest(release)
    release_zip = destination / 'Drum_Shot_Supply_Co_Windows_x64.zip'
    archives = [archive(release, release_zip)]

    # Clean staging read-back; this does not modify any installed VST3 or scan cache.
    staging = destination / 'installation-staging'
    staging.mkdir()
    with zipfile.ZipFile(release_zip) as check:
        check.extractall(staging)  # Entries were validated above; generated archive only.
    for entry in json.loads((staging / 'SHA256SUMS.json').read_text()):
        assert digest(staging / entry['path']) == entry['sha256']

    source = destination / 'source'
    source.mkdir()
    for directory in ('Source', 'Tests', 'Assets', 'docs', 'scripts', 'legacy', 'notices', 'recovery'):
        for path in (ROOT / directory).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix.lower() not in {'.pyc','.obj','.pdb','.exe','.dll'}:
                copy_file(path, source / directory / path.relative_to(ROOT / directory))
    for name in ('CMakeLists.txt', 'README.md', 'THIRD_PARTY_LICENSES.md', '.gitignore'):
        copy_file(ROOT / name, source / name)
    for name in ('release-verification.json', 'RELEASE_VERIFICATION.md', 'supplied-samples.json'):
        copy_file(ROOT / 'evidence' / name, source / 'evidence' / name)
    manifest(source)
    source_zip = destination / 'Drum_Shot_Supply_Co_Source.zip'
    archives.append(archive(source, source_zip))
    source_staging = destination / 'source-extraction-verification'
    source_staging.mkdir()
    with zipfile.ZipFile(source_zip) as check:
        check.extractall(source_staging)
    for entry in json.loads((source_staging / 'SHA256SUMS.json').read_text()):
        assert digest(source_staging / entry['path']) == entry['sha256']
    assert (source_staging / 'Source/PluginEditor.cpp').stat().st_size > 10000
    assert (source_staging / 'Source/DrumEngine.h').stat().st_size > 10000
    result = {'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'archives': archives,
              'archive_crc_and_manifest_readback': 'PASS', 'factory_wav_decode': 'PASS',
              'installation_staging_readback': 'PASS', 'source_extraction_readback': 'PASS', 'clean_machine_install': 'NOT_TESTED',
              'installed_release_modified': False, 'public_distribution': 'NOT_PERFORMED', 'sample_redistribution': 'USER_AUTHORIZED'}
    (destination / 'artifacts.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
