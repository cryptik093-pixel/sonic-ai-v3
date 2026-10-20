"""Reproducible offline alias/tuning/DC/benchmark analysis; standard library only."""
import array
import json
import math
import sys
from pathlib import Path
from analyze_renders import fft

def samples(path):
    values=array.array('f')
    values.frombytes(path.read_bytes())
    if sys.byteorder!='little':
        values.byteswap()
    assert all(math.isfinite(v) for v in values), path
    return values

def power(values, hann=False):
    n=len(values)
    windowed=[v*(.5-.5*math.cos(2*math.pi*i/(n-1))) for i,v in enumerate(values)] if hann else values
    return [abs(x)**2 for x in fft(windowed)[:n//2+1]]

def pitch(values, expected, rate=48000):
    n=len(values)
    p=power(values,True)
    lo=max(1,int(expected*.95*n/rate))
    hi=min(len(p)-2,int(expected*1.05*n/rate)+1)
    k=max(range(lo,hi+1),key=p.__getitem__)
    a,b,c=[math.log(max(p[i],1e-300)) for i in (k-1,k,k+1)]
    delta=.5*(a-c)/(a-2*b+c)
    return (k+max(-.5,min(.5,delta)))*rate/n

if __name__=='__main__':
    folder=Path(sys.argv[1])
    config=json.loads((folder/'alias-input.json').read_text())
    n=config['fftSize'];k=config['fundamentalBin']
    alias={}
    for mode in ('eco','hq'):
        values=samples(folder/f'drive-{mode}.f32')
        assert len(values)==n
        p=power(values)
        fundamental=2*p[k]
        other=2*sum(v for i,v in enumerate(p[1:-1],1) if i!=k)+p[0]+p[-1]
        alias[mode]=dict(nonfundamental_to_fundamental_db=10*math.log10(max(other,1e-300)/fundamental),fundamental_rms=math.sqrt(fundamental)/n)
    improvement=alias['eco']['nonfundamental_to_fundamental_db']-alias['hq']['nonfundamental_to_fundamental_db']
    gain_delta=20*math.log10(alias['hq']['fundamental_rms']/alias['eco']['fundamental_rms'])
    failures=[]
    if improvement<10:
        failures.append('HQ alias improvement below proposed 10 dB experiment criterion')
    if abs(gain_delta)>.5:
        failures.append('Eco/HQ fundamental gain differs by more than 0.5 dB')
    tuning=[]
    for note in (36,48,60,72,84):
        expected=440*2**((note-69)/12)
        synthetic=[math.sin(2*math.pi*expected*i/48000) for i in range(n)]
        calibration=1200*math.log2(pitch(synthetic,expected)/expected)
        assert abs(calibration)<1, f'Pitch estimator error {calibration} cents'
    for path in sorted(folder.glob('tuning-family-*-note-*.f32')):
        note=int(path.stem.split('-')[-1]);expected=440*2**((note-69)/12)
        values=samples(path);assert len(values)==144000
        window=values[-n:]
        measured=pitch(window,expected)
        cents=1200*math.log2(measured/expected)
        mean=sum(window)/len(window)
        dc_db=20*math.log10(max(abs(mean),1e-20))
        tuning.append(dict(file=path.name,expected_hz=expected,measured_hz=measured,error_cents=cents,window_mean=mean,dc_dbfs=dc_db,peak=max(map(abs,values))))
        if abs(cents)>5:
            failures.append(f'{path.name}: tuning exceeds proposed 5-cent criterion')
        if dc_db>=-60:
            failures.append(f'{path.name}: DC fails blueprint -60 dBFS criterion')
    assert len(tuning)==20
    benchmark=json.loads((folder/'benchmark.json').read_text())
    for mode in benchmark['modes']:
        mode['reference_percentile_goal_met']=mode['p95Ms']<=1 and mode['p99Ms']<=2
        mode['deadline_ms']=256/48000*1000
    report=dict(alias_input=config,alias=alias,alias_improvement_db=improvement,fundamental_gain_delta_db=gain_delta,
                tuning_window=dict(fft_size=n,window='symmetric Hann',location='last 65536 of 144000 frames',sample_rate=48000,interpolation='three-bin log power parabola',estimator_check='synthetic root tones <1 cent'),
                tuning=tuning,benchmark=benchmark,audio_criteria_failures=failures,
                caveats=['Alias ratio includes all nonfundamental energy in a coherent high-frequency odd-nonlinearity test; it is not a general instrument alias score.',
                         'Only the fundamental is an intended in-band harmonic for this specified stimulus.',
                         'Percussion is intentionally excluded from pitched steady-tone tuning checks.',
                         'CPU measurements are the production core outside a DAW; all callback outliers remain included.',
                         'Listening and FL Studio validation remain NOT_TESTED.'])
    (folder/'analysis.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f"HQ/Eco nonfundamental energy improvement {improvement:.2f} dB; fundamental gain delta {gain_delta:.3f} dB")
    print(f"20 root-tone tests: max pitch error {max(abs(t['error_cents']) for t in tuning):.3f} cents; worst window DC {max(t['dc_dbfs'] for t in tuning):.2f} dBFS")
    for mode in benchmark['modes']:
        print(mode)
    for failure in failures:
        print('FAIL:',failure)
    print('PASS audio criteria' if not failures else 'FAIL audio criteria; see complete report')
    sys.exit(bool(failures))
