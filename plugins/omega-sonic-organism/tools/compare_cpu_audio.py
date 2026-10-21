"""Compare captured production audio before/after a CPU-only optimization.

Usage: compare_cpu_audio.py before-directory after-directory output.json
Accepts probe float WAV, PCM24 audition WAV and raw float32 metric captures.
Numerical limits are fixed here before comparison, not derived from results.
"""
import array,hashlib,json,math,struct,sys
from pathlib import Path

def samples(path,raw):
    if path.suffix=='.f32':data=raw;kind='float32'
    else:
        assert raw[:4]==b'RIFF' and raw[8:12]==b'WAVE'
        offset=12;fmt=None;data=None
        while offset+8<=len(raw):
            name=raw[offset:offset+4];size=struct.unpack_from('<I',raw,offset+4)[0]
            chunk=raw[offset+8:offset+8+size];assert len(chunk)==size
            if name==b'fmt ':fmt=struct.unpack_from('<HHIIHH',chunk)
            if name==b'data':data=chunk
            offset+=8+size+(size&1)
        assert fmt and data is not None
        if fmt[0]==3 and fmt[5]==32:kind='float32'
        else:assert fmt[0]==1 and fmt[5]==24;kind='pcm24'
    if kind=='float32':
        values=array.array('f');values.frombytes(data)
        if sys.byteorder!='little':values.byteswap()
    else:
        values=[]
        for i in range(0,len(data),3):
            x=data[i]|data[i+1]<<8|data[i+2]<<16
            values.append((x-16777216 if x&8388608 else x)/8388607)
    return kind,values

before,after,output=map(Path,sys.argv[1:]);records=[];failures=[]
paths=sorted(p for p in before.iterdir() if p.suffix in ('.f32','.wav'))
assert paths and {p.name for p in paths}=={p.name for p in after.iterdir() if p.suffix in ('.f32','.wav')}
for path in paths:
    a=path.read_bytes();b=(after/path.name).read_bytes()
    same=a==b
    record=dict(file=path.name,beforeSha256=hashlib.sha256(a).hexdigest(),afterSha256=hashlib.sha256(b).hexdigest(),bitIdentical=same)
    if not same:
        ka,va=samples(path,a);kb,vb=samples(path,b);assert ka==kb and len(va)==len(vb)
        assert all(math.isfinite(x) for x in va) and all(math.isfinite(x) for x in vb)
        peak=max(abs(x-y) for x,y in zip(va,vb));error=sum((x-y)**2 for x,y in zip(va,vb))
        relative=math.sqrt(error/max(sum(x*x for x in va),1e-30))
        limit=1e-7 if ka=='float32' else 1/8388607
        passed=peak<=limit and relative<=1e-6
        record.update(maximumAbsoluteDifference=peak,relativeRmsError=relative,absoluteLimit=limit,passed=passed)
        if not passed:failures.append(path.name)
    records.append(record)
report=dict(status='FAIL' if failures else 'PASS',scope='numerical audio preservation; not listening approval',relativeRmsLimit=1e-6,files=len(records),bitIdenticalFiles=sum(x['bitIdentical'] for x in records),failures=failures,records=records)
output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='records'}));sys.exit(bool(failures))
