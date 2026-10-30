"""Verify actual SDK compile inputs against the pinned official distribution."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

archive, sdk, build, output = map(Path, sys.argv[1:])
sdk, build = sdk.resolve(), build.resolve()
expected = json.loads((Path(__file__).resolve().parents[1] / 'dependencies.lock.json').read_text())['vst3sdk']['archiveSha256']
def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
if digest(archive) != expected:
    raise RuntimeError('SDK archive hash mismatch')
used = set()
def add(path):
    p = Path(path)
    if not p.is_absolute():
        p = build / p
    p = p.resolve()
    if p.is_relative_to(sdk):
        used.add(p.relative_to(sdk).as_posix().lower())
for item in json.loads((build / 'compile_commands.json').read_text()):
    add(item['file'])
cache = (build / 'CMakeCache.txt').read_text()
ninja = next(x.split('=', 1)[1] for x in cache.splitlines() if x.startswith('CMAKE_MAKE_PROGRAM:FILEPATH='))
deps = subprocess.run([ninja, '-C', str(build), '-t', 'deps'], capture_output=True, text=True, check=True)
for line in deps.stdout.splitlines():
    if line.startswith('    '):
        add(line.strip())
if 'pluginterfaces/base/funknown.h' not in used:
    raise RuntimeError('Incomplete compiler dependency inventory')
with zipfile.ZipFile(archive) as z:
    prefix = 'VST_SDK/vst3sdk/'
    entries = {x.filename[len(prefix):].lower(): x for x in z.infolist() if not x.is_dir() and x.filename.startswith(prefix)}
    used.update(n for n in entries if n.endswith('.cmake') or n.endswith('cmakelists.txt') or n == 'license.txt')
    files = []
    for name in sorted(used):
        entry = entries[name]
        relative = entry.filename[len(prefix):]
        checksum = hashlib.sha256(z.read(entry)).hexdigest()
        if digest(sdk / relative) != checksum:
            raise RuntimeError('SDK input differs from pinned archive: ' + relative)
        files.append({'path': relative, 'sha256': checksum})
output.write_text(json.dumps({'status': 'PASS', 'archiveSha256': expected, 'checkedFiles': len(files), 'files': files}, indent=2) + '\n')
print(f'PASS {len(files)} actual SDK/compiler/configuration inputs match pinned archive')
