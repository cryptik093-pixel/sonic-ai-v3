"""Run and retain checks for the exact current Windows sampler artifact."""
from pathlib import Path
import datetime as dt
import hashlib,json,platform,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(label,args):
    start=dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=600)
        code,out,err=p.returncode,p.stdout,p.stderr
    except subprocess.TimeoutExpired as e:code,out,err=-1,e.stdout or b'',(e.stderr or b'')+b'\nTIMEOUT\n'
    (ROOT/f'evidence/sampler-{label}.stdout.log').write_bytes(out)
    (ROOT/f'evidence/sampler-{label}.stderr.log').write_bytes(err)
    return dict(arguments=list(map(str,args)),started_utc=start,exit_code=code,status='PASS' if code==0 else 'FAIL'),out.decode('utf-8',errors='replace')
def main():
    source=[p for p in (ROOT/'Source').glob('*') if p.is_file()]
    newest=max(p.stat().st_mtime for p in source)
    binary=ROOT/'build/OmegaDrumSupply_artefacts/Release/VST3/Omega Drum Supply.vst3/Contents/x86_64-win/Omega Drum Supply.vst3'
    info=binary.parents[1]/'Resources/moduleinfo.json'
    version=bool(info.exists() and re.search(r'"Version"\s*:\s*"0\.2\.0"',info.read_text()))
    result=dict(created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),configuration='Release Windows x64 C++20 MSVC / JUCE 8.0.16-security',hardware='Intel Core i5-4310U @ 2.00 GHz, 2 cores / 4 logical processors, approximately 8 GiB RAM',os=dict(system=platform.system(),version=platform.version(),machine=platform.machine()),float_precision='32-bit only',fl_studio='NOT_TESTED',human_listening='PENDING',commercial_framework_eligibility='PENDING',clean_machine_install='NOT_TESTED',validation_directories=[])
    result['build']='PASS' if binary.exists() and version and binary.stat().st_mtime>=newest else 'FAIL'
    if binary.exists():result['binary']=dict(path=str(binary),bytes=binary.stat().st_size,sha256=sha(binary))
    result['source_hashes']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(source)}
    result['baseline_git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    for name,program,extra,test in [('sample_dsp','DrumSampleTests.exe',[],'SampleTests.cpp'),('processor','DrumProcessorTests.exe',['evidence/sampler-fixtures'],'ProcessorTests.cpp')]:
        exe=ROOT/'build'/program
        threshold=max((ROOT/'Tests'/test).stat().st_mtime,(ROOT/'Source/SampleEngine.h').stat().st_mtime if name=='sample_dsp' else newest)
        if not exe.exists() or exe.stat().st_mtime<threshold:
            result[name]='FAIL';result[name+'_run']={'error':'Test executable is missing or stale'};continue
        detail,out=run(name,[str(exe),*extra]);detail['executable_sha256']=sha(exe);result[name]=detail['status'];result[name+'_run']=detail
        if name=='processor':
            line=next((line for line in out.splitlines() if line.startswith('BENCHMARK ')),None)
            result['performance_line']=line;result['performance']='PASS' if line and 'budget=PASS' in line else 'FAIL'
    (ROOT/'evidence/sampler-verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:result.get(k) for k in ['build','sample_dsp','processor','performance','binary','performance_line']},indent=2))
    return 0 if all(result.get(k)=='PASS' for k in ['build','sample_dsp','processor']) else 1
if __name__=='__main__':sys.exit(main())
