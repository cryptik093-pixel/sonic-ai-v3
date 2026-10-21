"""Read back actual production-service exports and verify their PCM contents."""
from pathlib import Path
import hashlib,json,math,wave
root=Path(__file__).resolve().parents[1]
folder=root/'evidence/release-fixtures/FactoryAudio'
records=[]
for p in sorted(folder.rglob('*.wav')):
 with wave.open(str(p),'rb') as w:
  rate,channels,width,frames=w.getframerate(),w.getnchannels(),w.getsampwidth(),w.getnframes()
  assert rate in (44100,48000,96000) and channels==2 and width==3 and frames>rate*.1,p
  raw=w.readframes(frames)
 assert len(raw)==frames*6,p
 peak=0.;energy=0.
 for i in range(0,len(raw),3):
  x=int.from_bytes(raw[i:i+3],'little',signed=True)/8388608
  peak=max(peak,abs(x));energy+=x*x
 rms=math.sqrt(energy/(frames*2))
 assert rms>1.e-7 and peak<=.980001,p
 records.append(dict(file=p.relative_to(folder).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),frames=frames,rate=rate,channels=channels,bit_depth=24,seconds=frames/rate,peak=peak,rms=rms))
manifests=[]
for p in sorted(folder.glob('*/ExportManifest.json')):
 m=json.loads(p.read_text());assert m['state']=='COMPLETE' and len(m['files'])==8,p
 for row in m['files']:
  file=p.parent/row['file'];assert hashlib.sha256(file.read_bytes()).hexdigest()==row['sha256'],file
 manifests.append(dict(file=p.relative_to(folder).as_posix(),kit=m['kit'],state=m['state']))
assert len({m['kit'] for m in manifests})==6 and len(records)>=51
report=dict(state='PASS',wav_files=len(records),factory_profiles=6,manifests=manifests,renders=records,human_listening='NOT_TESTED')
(folder.parent/'export-verification.json').write_text(json.dumps(report,indent=2))
print(f"PASS {len(records)} production-service PCM24 exports, six distinct factory profiles, WAV format/audio levels and manifest hashes")
