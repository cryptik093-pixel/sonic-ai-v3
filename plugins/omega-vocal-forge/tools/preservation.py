"""Record/compare original ADLIB93 source without modifying any original file."""
import hashlib
import json
import os
from pathlib import Path
import sys

project = Path(__file__).resolve().parents[1]
original = project.parent / 'adlib-93'
manifest = project / 'evidence/adlib93-preservation-before.json'
paths = []
for folder, directories, files in os.walk(original):
    directories[:] = [d for d in directories if d not in {'build','dist','evidence','.git','__pycache__'} and not d.startswith('build-')]
    paths.extend(Path(folder) / name for name in files)
def checksum(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
current = {p.relative_to(original).as_posix(): checksum(p) for p in sorted(paths)}
if sys.argv[1:] == ['record']:
    if manifest.exists():
        raise RuntimeError('Refusing to replace preservation baseline')
    manifest.write_text(json.dumps(current, indent=2) + '\n')
    print(f'Recorded {len(current)} original source/config/doc/test files')
else:
    before = json.loads(manifest.read_text())
    changed = [p for p in before if current.get(p) != before[p]]
    added = [p for p in current if p not in before]
    result = {'status': 'FAIL' if changed or added else 'PASS', 'checkedFiles': len(before), 'changedOrMissing': changed, 'added': added}
    (project / 'evidence/adlib93-preservation-after.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    if changed or added:
        raise SystemExit(1)
