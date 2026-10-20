"""Offline analysis of the binary probe's IEEE float WAVs, using only stdlib."""
import cmath
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

def fft(values):
    n = len(values)
    out = list(map(complex, values))
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            out[i], out[j] = out[j], out[i]
    size = 2
    while size <= n:
        root = cmath.exp(-2j * math.pi / size)
        for start in range(0, n, size):
            w = 1
            for k in range(size // 2):
                a, b = out[start+k], w*out[start+k+size//2]
                out[start+k], out[start+k+size//2] = a+b, a-b
                w *= root
        size *= 2
    return out

if __name__ == '__main__':
    # Check sign/bin convention against an analytic, coherent sinusoid.
    check = fft([math.sin(2*math.pi*7*n/128) for n in range(128)])
    assert abs(check[7]+64j) < 1e-9 and abs(check[121]-64j) < 1e-9
    folder = Path(sys.argv[1])
    paths = sorted(folder.glob('morph-*-note-*.wav'))
    assert len(paths) == 27, f'Expected 27 binary renders, got {len(paths)}'
    records = []
    for path in paths:
        raw = path.read_bytes()
        assert raw[:4] == b'RIFF' and raw[8:16] == b'WAVEfmt '
        assert struct.unpack_from('<HHI', raw, 20) == (3, 2, 48000)
        assert raw[36:40] == b'data'
        data = struct.unpack_from('<'+'f'*((len(raw)-44)//4), raw, 44)[::2]
        assert len(data) == 96000 and all(math.isfinite(x) and abs(x) <= 1 for x in data)
        rms = math.sqrt(sum(x*x for x in data)/len(data))
        assert rms > 1e-6
        # Fixed position before note-off. Magnitude-power weighting, one-sided
        # real-signal spectrum; this is not an aliasing or pitch-quality test.
        nfft, offset = 8192, 16384
        spectrum = fft([data[offset+n]*(.5-.5*math.cos(2*math.pi*n/(nfft-1))) for n in range(nfft)])
        powers = [abs(x)**2 for x in spectrum[:nfft//2+1]]
        centroid = sum(i*48000/nfft*p for i, p in enumerate(powers))/sum(powers)
        records.append(dict(file=path.name, sha256=hashlib.sha256(raw).hexdigest(),
                            rms=rms, peak=max(map(abs,data)), mean=sum(data)/len(data),
                            power_centroid_hz=centroid))
    report = dict(sample_rate=48000, duration_seconds=2, channel='left of stereo',
                  fft_size=8192, window='symmetric Hann', offset_samples=16384,
                  fft_scaling='unscaled FFT; power centroid uses normalized weights',
                  listening='NOT_TESTED', aliasing='NOT_TESTED', records=records)
    (folder/'analysis.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS 27 finite, nonzero, bounded actual-binary renders; FFT convention verified.')
    for r in records:
        if r['file'].endswith('note-48.wav'):
            print(f"{r['file']}: rms={r['rms']:.6f}, peak={r['peak']:.6f}, power centroid={r['power_centroid_hz']:.2f} Hz")
