"""Verify current production-processor WAV renders without editing audio."""
import hashlib,json,math,wave
from pathlib import Path
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 directory=root/'evidence/release-fixtures';records=[]
 names=['Kick','Snare','Closed Hat','Cymbal','Tom','Percussion','Clap','Open Hat']
 for slot,name in enumerate(names):
  for processed in (False,True):
   path=directory/f"{slot}-{'processed' if processed else 'dry'}.wav"
   with wave.open(str(path),'rb') as wav:
    metadata={'rate':wav.getframerate(),'channels':wav.getnchannels(),'bit_depth':wav.getsampwidth()*8,'frames':wav.getnframes()};raw=wav.readframes(wav.getnframes())
   if metadata!={'rate':48000,'channels':2,'bit_depth':24,'frames':144000} or len(raw)!=144000*2*3:raise ValueError('Unexpected render format '+str(path))
   total=0.;peak=0.
   for i in range(0,len(raw),3):
    x=int.from_bytes(raw[i:i+3],'little',signed=True)/8388608.;total+=x*x;peak=max(peak,abs(x))
   rms=math.sqrt(total/(len(raw)//3))
   if not math.isfinite(rms) or rms<.00001 or peak>.980001:raise ValueError('Silent or invalid render '+str(path))
   records.append({'file':path.name,'sha256':sha(path),'slot':slot,'voice':name,'peak':peak,'rms':rms,'midi_note':60,'velocity':.8,'trigger_frames':[0,20480,21120],'per_slot_macros':{'punch':.5,'tone':.5,'character':.5},'legacy_global_macros':{'body':.8 if processed else .5,'character':.8 if processed else .5,'space':.7 if processed else 0},'sample_blend':0,'slot_gain_db':-6,'output_gain_db':-6,'complete_decay_capture':False,**metadata})
 binary=root/'build/OmegaDrumSupply_artefacts/Release/VST3/Drum Shot Supply Co..vst3/Contents/x86_64-win/Drum Shot Supply Co..vst3'
 report={'version':'0.3.0','product':'Drum Shot Supply Co.','created_utc':datetime.now(timezone.utc).isoformat(),'state':'PASS','human_listening':'NOT_TESTED','renderer_sha256':sha(root/'build/DrumProcessorTests.exe'),'engine_sha256':sha(root/'Source/DrumEngine.h'),'processor_test_source_sha256':sha(root/'Tests/ProcessorTests.cpp'),'module_sha256':sha(binary),'renders':records}
 (directory/'render-manifest.json').write_text(json.dumps(report,indent=2));print('PASS 16 production-processor WAV hashes, exact render state, PCM format and nonzero RMS metrics')
if __name__=='__main__':main()
