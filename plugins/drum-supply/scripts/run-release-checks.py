"""Run and retain checks for the exact current Windows synthesis artifact."""
from pathlib import Path
import datetime as dt
import hashlib,json,platform,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def original_path(value):
    p=Path(value)
    if not p.is_absolute() and p.parts[:2]==('plugins','drum-supply'):
        return ROOT.joinpath(*p.parts[2:])
    return p

def run(label,args):
    start=dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=1800)
        code,out,err=p.returncode,p.stdout,p.stderr
    except subprocess.TimeoutExpired as e:code,out,err=-1,e.stdout or b'',(e.stderr or b'')+b'\nTIMEOUT\n'
    (ROOT/f'evidence/release-{label}.stdout.log').write_bytes(out)
    (ROOT/f'evidence/release-{label}.stderr.log').write_bytes(err)
    return dict(arguments=list(map(str,args)),started_utc=start,exit_code=code,status='PASS' if code==0 else 'FAIL'),out.decode('utf-8',errors='replace')
def main():
    source=[p for folder in ('Source','Tests') for p in (ROOT/folder).glob('*') if p.is_file()]+[ROOT/'CMakeLists.txt']
    newest=max(p.stat().st_mtime for p in source if 'Source' in p.parts)
    binary=ROOT/'build/OmegaDrumSupply_artefacts/Release/VST3/Drum Shot Supply Co..vst3/Contents/x86_64-win/Drum Shot Supply Co..vst3'
    info=binary.parents[1]/'Resources/moduleinfo.json'
    version=bool(info.exists() and re.search(r'"Version"\s*:\s*"0\.3\.0"',info.read_text()))
    result=dict(created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),configuration='Release Windows x64 C++20 MSVC / JUCE 8.0.16-security',hardware='Intel Core i5-4310U @ 2.00 GHz, 2 cores / 4 logical processors, approximately 8 GiB RAM',os=dict(system=platform.system(),version=platform.version(),machine=platform.machine()),float_precision='32-bit only',fl_studio='NOT_TESTED',human_listening='PENDING',commercial_framework_eligibility='PENDING',clean_machine_install='NOT_TESTED',validation_directories=[])
    result['build']='PASS' if binary.exists() and version and binary.stat().st_mtime>=newest else 'FAIL'
    if binary.exists():
        result['binary']=dict(path=str(binary),bytes=binary.stat().st_size,sha256=sha(binary))
        payload=binary.read_bytes();offset=int.from_bytes(payload[60:64],'little')
        result['windows_x64_pe']='PASS' if payload[:2]==b'MZ' and payload[offset:offset+4]==b'PE\0\0' and int.from_bytes(payload[offset+4:offset+6],'little')==0x8664 else 'FAIL'
    baseline=ROOT/'recovery/baseline-moduleinfo.json'
    if info.exists() and baseline.exists():
        old=re.findall(r'"CID"\s*:\s*"([A-F0-9]+)"',baseline.read_text());current=re.findall(r'"CID"\s*:\s*"([A-F0-9]+)"',info.read_text())
        result['vst3_class_ids']='PASS' if len(old)==2 and current==old else 'FAIL';result['class_ids']=current
    result['source_hashes']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(source)}
    validation=[]
    for file in sorted((ROOT/'evidence').glob('validation-*/validation.json')):
        v=json.loads(file.read_text())
        if result.get('binary',{}).get('sha256')==v.get('binarySha256Before')==v.get('binarySha256After') and v.get('artifactUnchanged') and v.get('strictness')==10:
            validation.append((file,v))
    result['validators']='NOT_RUN'
    if validation:
        file,v=validation[-1];result['validators']=v['state'];result['validation_directories']=[str(file.parent)];result['validator_tools']=v['tools']
    originals=[]
    for row in json.loads((ROOT/'recovery/input-assets-manifest.json').read_text())['files']:
        path=original_path(row['path']);originals.append(path.exists() and path.stat().st_size==row['size'] and sha(path)==row['sha256'])
    for row in json.loads((ROOT/'recovery/pre-synthesis-recovery-manifest.json').read_text())['files']:
        path=original_path(row['path'])
        if 'legacy' in path.parts or 'baseline-0.1.0' in path.parts or 'Assets' in path.parts:
            originals.append(path.exists() and path.stat().st_size==row['size'] and sha(path)==row['sha256'])
    result['original_assets']='PASS' if all(originals) else 'FAIL';result['original_files_checked']=len(originals)
    result['text_integrity']='PASS' if all(p.stat().st_size>0 and b'\0' not in p.read_bytes() for p in source) else 'FAIL'
    result['baseline_git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    for name,program,extra,test in [('synthesis_dsp','DrumSynthesisTests.exe',[],'SynthesisTests.cpp'),('legacy_dsp','DrumDspTests.exe',[],'DspTests.cpp'),('sample_dsp','DrumSampleTests.exe',[],'SampleTests.cpp'),('processor','DrumProcessorTests.exe',['evidence/release-fixtures'],'ProcessorTests.cpp')]:
        exe=ROOT/'build'/program
        threshold=max((ROOT/'Tests'/test).stat().st_mtime,(ROOT/'Source/SampleEngine.h').stat().st_mtime if name=='sample_dsp' else newest)
        if not exe.exists() or exe.stat().st_mtime<threshold:
            result[name]='FAIL';result[name+'_run']={'error':'Test executable is missing or stale'};continue
        detail,out=run(name,[str(exe),*extra]);detail['executable_sha256']=sha(exe);result[name]=detail['status'];result[name+'_run']=detail
        if name=='processor':
            line=next((line for line in out.splitlines() if line.startswith('BENCHMARK ')),None)
            result['performance_line']=line;result['performance']='PASS' if line and 'budget=PASS' in line else 'FAIL'
    if result.get('processor')=='PASS':
        detail,_=run('render_manifest',[sys.executable,str(ROOT/'scripts/manifest-renders.py')]);result['offline_renders']=detail['status'];result['render_manifest_run']=detail
    (ROOT/'evidence/release-verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:result.get(k) for k in ['build','synthesis_dsp','legacy_dsp','sample_dsp','processor','performance','validators','original_assets','text_integrity','binary','performance_line']},indent=2))
    return 0 if all(result.get(k)=='PASS' for k in ['build','synthesis_dsp','legacy_dsp','sample_dsp','processor']) else 1
if __name__=='__main__':sys.exit(main())
