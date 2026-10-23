"""Measure real native V4 renders; subjective listening remains untested."""
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys


def read_audio(path):
    raw = path.read_bytes()
    assert raw[:4] == b'RIFF' and raw[8:16] == b'WAVEfmt '
    assert struct.unpack_from('<HHI', raw, 20) == (3, 2, 48000)
    assert raw[36:40] == b'data'
    audio = struct.unpack_from('<' + 'f' * ((len(raw)-44)//4), raw, 44)
    assert len(audio) == 192000
    assert all(math.isfinite(x) and abs(x) <= .980001 for x in audio)
    return raw, audio


def main():
    folder, legacy = map(Path, sys.argv[1:3])
    paths = sorted(folder.glob('v4-anchor-*-pattern-*-note-48.wav'))
    assert len(paths) == 15
    records = []
    for path in paths:
        match = re.fullmatch(r'v4-anchor-(\d)-pattern-(\d)-note-48.wav', path.name)
        assert match
        anchor, pattern = map(int, match.groups())
        assert 0 <= anchor <= 4 and 1 <= pattern <= 3
        raw, audio = read_audio(path)
        _, before = read_audio(legacy / f'morph-{anchor*2}-note-48.wav')
        rms = math.sqrt(sum(x*x for x in audio)/len(audio))
        difference = math.sqrt(sum((x-y)**2 for x, y in zip(audio, before))/len(audio))
        assert rms > 1e-6 and difference > 1e-6
        records.append(dict(file=path.name, anchor=anchor, pattern=pattern,
                            sha256=hashlib.sha256(raw).hexdigest(), rms=rms,
                            peak=max(map(abs, audio)), rms_difference_from_legacy=difference))
    report = dict(result='PASS', scope='actual native DLL finite nonzero V4 audio and measured change',
                  listening='NOT_TESTED', sampleRate=48000, channels=2,
                  criteria=dict(peak_max=.980001, rms_min=1e-6, rms_difference_min=1e-6), records=records)
    (folder/'analysis.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('PASS 15 actual V4 renders: bounded, nonzero, distinct from legacy at every anchor; listening NOT_TESTED.')


if __name__ == '__main__':
    main()
