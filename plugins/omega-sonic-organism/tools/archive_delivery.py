"""Create and independently read back a hash-verified deliverable archive."""
import hashlib,json,sys,zipfile
from pathlib import Path

stage=Path(sys.argv[1]).resolve();target=Path(str(stage)+'.zip')
assert stage.is_dir() and not target.exists()
manifest=json.loads((stage/'BUILD_MANIFEST.json').read_text(encoding='utf-8-sig'))
expected={entry['path'].replace('\\','/'):entry['sha256'].lower() for entry in manifest['files']}
files={p.relative_to(stage).as_posix():p for p in stage.rglob('*') if p.is_file()}
assert set(files)==set(expected)|{'BUILD_MANIFEST.json'}
with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name,path in sorted(files.items()):z.write(path,name)
with zipfile.ZipFile(target) as z:
    assert len(z.infolist())==len(files)
    assert z.testzip() is None
    for name in sorted(files):
        actual=hashlib.sha256(z.read(name)).hexdigest()
        reference=expected.get(name,hashlib.sha256(files[name].read_bytes()).hexdigest())
        assert actual==reference,(name,actual,reference)
print(json.dumps(dict(zip=str(target),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),files=len(files),crcAndEveryFileHash='PASS')))
