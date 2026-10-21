"""Report the specified matched benchmark pair without filtering any callback."""
import hashlib,json,sys
from pathlib import Path
folder=Path(sys.argv[1])
def read(name):return json.loads((folder/name).read_text(encoding='utf-8-sig'))
before=read('before-repeat/benchmark.json');after=read('after-repeat/benchmark.json')
for key in ('kind','sampleRate','frames','voices','secondsPerMode'):assert before[key]==after[key],key
modes=[]
for a,b in zip(before['modes'],after['modes']):
    assert a['quality']==b['quality'] and a['callbacks']==b['callbacks']
    fields=('medianMs','p95Ms','p99Ms','maximumMs','threadCpuTotalMs')
    reduction={key:100*(1-b[key]/a[key]) for key in fields}
    modes.append(dict(quality=a['quality'],before=a,after=b,reductionPercent=reduction,referenceGoalMet=b['p95Ms']<=1 and b['p99Ms']<=2 and b['overruns']==0))
executables={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in ('before-engine-metrics.exe','after-engine-metrics.exe')}
report=dict(status='MEASURED',kind=before['kind'],sampleRate=before['sampleRate'],frames=before['frames'],voices=before['voices'],secondsPerMode=before['secondsPerMode'],baselineRevision='be3bf4ed9ff41b4a1f9fe6b4d61ebffbf62f89df',modes=modes,executableSha256=executables,caveats=['Same Windows machine and workload; normal thread priority; no power-plan, affinity, voice-count, quality, or threshold changes.','Shared-machine scheduling and frequency changes affect wall-clock tails. All observed outliers and deadline overruns remain in the reports.','Isolated function profiles are diagnostic microbenchmarks, not additive callback percentages.','This is production-core measurement, not FL Studio acceptance or a zero-dropout guarantee.'])
(folder/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
