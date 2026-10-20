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
NAME = f'Drum-Supply-Headquarters-0.2.0-evaluation-{STAMP}'


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
            for p in sorted(folder.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS.json']
    (folder / 'SHA256SUMS.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')


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
    report = ROOT / 'evidence/sampler-verification.json'
    results = json.loads(report.read_text())
    for gate in ('build', 'sample_dsp', 'processor'):
        if results[gate] != 'PASS':
            raise RuntimeError(f'Refusing to package without a passing {gate} gate')
    destination = ROOT / 'dist' / NAME
    destination.mkdir(parents=True, exist_ok=False)
    binary = ROOT / 'build/OmegaDrumSupply_artefacts/Release/VST3/Omega Drum Supply.vst3'
    executable = binary / 'Contents/x86_64-win/Omega Drum Supply.vst3'
    if digest(executable) != results['binary']['sha256']:
        raise ValueError('Binary changed after verification')
    for relative, expected in results['source_hashes'].items():
        if digest(ROOT / relative) != expected:
            raise ValueError(f'Source changed after verification: {relative}')
    release = destination / 'evaluation'
    release.mkdir()
    tree(binary, release / binary.name)
    tree(ROOT / 'Assets', release / 'Factory Samples')
    tree(ROOT / 'docs', release / 'Documentation')
    for name in ('README.md', 'THIRD_PARTY_LICENSES.md'):
        copy_file(ROOT / name, release / name)
    tree(ROOT / 'notices', release / 'Third Party Notices')
    copy_file(report, release / 'Verification/sampler-verification.json')
    copy_file(ROOT / 'evidence/SAMPLER_VERIFICATION.md', release / 'Verification/REPORT.md')
    fixtures = ROOT / 'evidence/sampler-fixtures'
    tree(fixtures, release / 'Evaluation Fixtures')
    for validation in results.get('validation_directories', []):
        source = Path(validation).resolve()
        if not source.is_relative_to((ROOT / 'evidence').resolve()):
            raise ValueError('Validator evidence must stay within this plugin')
        tree(source, release / 'Verification' / source.name)
    manifest(release)
    release_zip = destination / f'{NAME}.zip'
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
    for directory in ('Source', 'Tests', 'Assets', 'docs', 'scripts', 'legacy', 'notices'):
        for path in (ROOT / directory).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix.lower() not in {'.pyc','.obj','.pdb','.exe','.dll'}:
                copy_file(path, source / directory / path.relative_to(ROOT / directory))
    for name in ('CMakeLists.txt', 'README.md', 'THIRD_PARTY_LICENSES.md', '.gitignore'):
        copy_file(ROOT / name, source / name)
    for name in ('sampler-verification.json', 'SAMPLER_VERIFICATION.md', 'supplied-samples.json'):
        copy_file(ROOT / 'evidence' / name, source / 'evidence' / name)
    manifest(source)
    archives.append(archive(source, destination / f'{NAME}-source.zip'))
    result = {'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'archives': archives,
              'archive_crc_and_manifest_readback': 'PASS', 'factory_wav_decode': 'PASS',
              'installation_staging_readback': 'PASS', 'clean_machine_install': 'NOT_TESTED',
              'installed_release_modified': False, 'public_distribution': 'NOT_AUTHORIZED'}
    (destination / 'artifacts.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
