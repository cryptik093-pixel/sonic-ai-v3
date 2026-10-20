"""Compare the SDK files used by the compiler with the pinned distribution."""
import hashlib,json,sys,zipfile
from pathlib import Path
archive,sdk,output=map(Path,sys.argv[1:])
expected='64965f1b74e08a6d4087a35af7a716f4dcff5852c66ad7ee13f1c47e79c1ab77'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==expected
files=[];prefix='VST_SDK/vst3sdk/'
with zipfile.ZipFile(archive) as z:
    for entry in z.infolist():
        if entry.is_dir() or not entry.filename.startswith(prefix):continue
        relative=entry.filename[len(prefix):];target=sdk/relative
        assert target.is_file(),relative
        archived=hashlib.sha256(z.read(entry)).hexdigest()
        assert hashlib.sha256(target.read_bytes()).hexdigest()==archived,relative
        files.append(dict(path=relative,sha256=archived))
assert len(files)>100
result=dict(archiveSha256=expected,archiveFilesMatchBuildSdk=True,checkedFiles=len(files),files=files)
output.write_text(json.dumps(result,indent=2)+'\n')
print(f'PASS {len(files)} pinned SDK files match the build SDK')
