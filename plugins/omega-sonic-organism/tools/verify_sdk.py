"""Match SDK compiler inputs and CMake configuration to the pinned archive.

Usage: verify_sdk.py archive.zip sdk-directory report.json build-directory
Run after Ninja finishes. Unused local documentation/assets are not compared.
"""
import hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
archive,sdk,output,build=map(Path,sys.argv[1:])
expected='64965f1b74e08a6d4087a35af7a716f4dcff5852c66ad7ee13f1c47e79c1ab77'
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
assert digest(archive)==expected
sdk=sdk.resolve();build=build.resolve();prefix='VST_SDK/vst3sdk/'
sdk_prefix=os.path.normcase(str(sdk))+os.sep;used=set()
def add(path):
    candidate=Path(path)
    if not candidate.is_absolute():candidate=build/candidate
    absolute=os.path.normpath(os.path.abspath(candidate))
    if os.path.normcase(absolute).startswith(sdk_prefix):used.add(os.path.relpath(absolute,sdk).replace('\\','/').casefold())
commands=json.loads((build/'compile_commands.json').read_text())
for command in commands:add(command['file'])
cache=(build/'CMakeCache.txt').read_text()
ninja=next(line.split('=',1)[1] for line in cache.splitlines() if line.startswith('CMAKE_MAKE_PROGRAM:FILEPATH='))
deps=subprocess.run([ninja,'-C',str(build),'-t','deps'],capture_output=True,text=True,check=True)
before_includes=len(used)
for line in deps.stdout.splitlines():
    if line.startswith('    '):add(line.strip())
include_count=len(used)-before_includes
required=('pluginterfaces/base/funknown.h','vstgui4/vstgui/lib/controls/cbuttons.cpp')
assert include_count>0 and all(name in used for name in required),'Missing complete SDK compiler dependency inventory'
files=[]
with zipfile.ZipFile(archive) as z:
    entries={e.filename[len(prefix):].casefold():e for e in z.infolist() if not e.is_dir() and e.filename.startswith(prefix)}
    used.update(name for name in entries if name.endswith('.cmake') or name.endswith('cmakelists.txt'))
    for name in sorted(used):
        assert name in entries,('SDK compiler input absent from archive',name)
        entry=entries[name];relative=entry.filename[len(prefix):];target=sdk/relative
        assert target.is_file(),relative
        archived=hashlib.sha256(z.read(entry)).hexdigest()
        assert digest(target)==archived,relative
        files.append(dict(path=relative,sha256=archived))
result=dict(archiveSha256=expected,buildDirectory=str(build),compiledSdkInputsMatchArchive=True,checkedFiles=len(files),ninjaIncludeCount=include_count,requiredIncludesFound=list(required),scope='SDK translation units, Ninja-reported includes and SDK CMake configuration; unused local documentation/assets are not compared',files=files)
temporary=output.with_suffix(output.suffix+'.tmp');temporary.write_text(json.dumps(result,indent=2)+'\n');temporary.replace(output)
print(f'PASS {len(files)} SDK build/configuration inputs match the pinned distribution')
