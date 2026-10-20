"""Read back exported PCM24 files and compare signal metrics with the render log."""
import hashlib,json,math,sys,wave
from pathlib import Path
folder=Path(sys.argv[1]);report=json.loads((folder/'audition-results.json').read_text(encoding='utf-8-sig'))
files=[]
for entry in report['renders']:
    path=folder/entry['file']
    with wave.open(str(path),'rb') as w:
        assert (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())==(2,3,48000,288000)
        data=w.readframes(w.getnframes());assert len(data)==288000*6
    power=0;peak=0;total=0;clipped=0
    for i in range(0,len(data),3):
        value=data[i]|data[i+1]<<8|data[i+2]<<16
        if value&0x800000:value-=0x1000000
        power+=value*value;total+=value;peak=max(peak,abs(value));clipped+=abs(value)>=8388607
    count=len(data)//3;rms=math.sqrt(power/count)/8388607;peak/=8388607
    assert rms>0 and clipped==0
    assert abs(rms-entry['rms'])<2e-6 and abs(peak-entry['peak'])<2e-6
    files.append(dict(file=entry['file'],sha256=hashlib.sha256(path.read_bytes()).hexdigest(),frames=288000,peak=peak,rms=rms,mean=total/count/8388607,clippedSamples=clipped))
assert len(files)==48
(folder/'pcm24-verification.json').write_text(json.dumps(dict(status='PASS',files=files,listening='PENDING'),indent=2)+'\n')
print('PASS all 48 WAV headers, decoded PCM24 signal metrics, nonzero energy, zero clipped samples and file hashes')
