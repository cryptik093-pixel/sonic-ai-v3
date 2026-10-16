#!/usr/bin/env python3
"""Render generated engineering tones through the actual production renderer.

No additional Python dependencies; never reads owner vocal recordings.
DFT convention: https://numpy.org/doc/stable/reference/routines.fft.html
NumPy is a formula reference, not a runtime dependency of this script.
"""
import argparse
import cmath
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess


def amplitude(samples, bin_index):
    """2/N |sum x[n] exp(-j2*pi*k*n/N)|, non-DC/Nyquist bins only."""
    rotation = cmath.exp(-2j * math.pi * bin_index / len(samples))
    phase, total = 1 + 0j, 0j
    for sample in samples:
        total += sample * phase
        phase *= rotation
    return 2 * abs(total) / len(samples)


def write_float_wave(file, samples, rate):
    data = struct.pack('<' + 'f' * len(samples), *samples)
    header = b'RIFF' + struct.pack('<I', 36 + len(data)) + b'WAVEfmt '
    header += struct.pack('<IHHIIHH', 16, 3, 1, rate, rate * 4, 4, 32)
    with file.open('xb') as stream:
        stream.write(header + b'data' + struct.pack('<I', len(data)) + data)


def read_stereo_float(file):
    data = file.read_bytes()
    if data[:4] != b'RIFF' or data[8:12] != b'WAVE':
        raise ValueError('Renderer did not write RIFF WAVE')
    fmt, payload, cursor = None, None, 12
    while cursor + 8 <= len(data):
        size = struct.unpack_from('<I', data, cursor + 4)[0]
        if cursor + 8 + size > len(data):
            raise ValueError('Truncated renderer output')
        chunk = data[cursor + 8:cursor + 8 + size]
        if data[cursor:cursor + 4] == b'fmt ':
            fmt = struct.unpack_from('<HHIIHH', chunk)
        elif data[cursor:cursor + 4] == b'data':
            payload = chunk
        cursor += 8 + size + (size & 1)
    if not fmt or fmt[0] != 3 or fmt[1] != 2 or fmt[5] != 32 or payload is None or len(payload) % 8:
        raise ValueError('Expected stereo float32 renderer output')
    values = struct.unpack('<' + 'f' * (len(payload) // 4), payload)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('Non-finite rendered sample')
    return fmt[2], values[::2], values[1::2]


def sha256(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--renderer', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New directory; no existing files replaced')
    parser.add_argument('--all-presets', action='store_true', help='Also render the other21 presets for engineering only')
    args = parser.parse_args()
    renderer = args.renderer.resolve(strict=True)
    output = args.output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    rate, count, fundamental = 44100, 4096, 509
    frames = rate * 2
    source = output / 'generated-coherent-tone.wav'
    write_float_wave(source, [.5 * math.sin(2 * math.pi * fundamental * n / count) for n in range(frames)], rate)
    dry_rate, dry_amplitude = rate, amplitude([.5 * math.sin(2 * math.pi * fundamental * n / count) for n in range(count)], fundamental)
    if abs(dry_amplitude - .5) > 1e-9:
        raise ValueError('DFT reference calibration failed')
    records = []
    analysis_presets = {4: 'Dry Bite (soft)', 14: 'Radio Bite (asymmetric)', 16: 'Broken Speaker (hard)'}
    presets = range(1, 25) if args.all_presets else analysis_presets
    for preset in presets:
        target = output / f'preset-{preset:02d}.wav'
        command = [str(renderer), '--preset', str(preset), '--input', str(source), '--output', str(target),
                   '--sample-rate', str(rate), '--block-size', '128', '--tail-seconds', '0']
        process = subprocess.run(command, capture_output=True, text=True, errors='replace', timeout=180, shell=False)
        (output / f'preset-{preset:02d}.log').write_text(process.stdout + '\n' + process.stderr, encoding='utf-8')
        if process.returncode:
            raise RuntimeError(f'Actual renderer failed for preset{preset}; see retained log')
        actual_rate, left, right = read_stereo_float(target)
        if actual_rate != dry_rate or len(left) != frames:
            raise ValueError('Actual render dimensions differ')
        record = {'preset': preset, 'command': command, 'exitCode': process.returncode,
                  'wavSha256': sha256(target), 'frames': len(left),
                  'samplePeak': max(max(map(abs, left)), max(map(abs, right))), 'listening': 'PENDING'}
        if preset in analysis_presets:
            steady = left[-count:]
            base = amplitude(steady, fundamental)
            bins = sorted({min((harmonic * fundamental) % count, count - (harmonic * fundamental) % count)
                           for harmonic in range(5, 65)})
            measured = [{'bin': k, 'frequencyHz': k * rate / count, 'amplitude': amplitude(steady, k)} for k in bins]
            ratio = math.sqrt(sum(item['amplitude'] ** 2 for item in measured)) / max(base, 1e-30)
            record.update(label=analysis_presets[preset], fundamentalAmplitude=base,
                          selectedFoldedBinsDbRelativeFundamental=20 * math.log10(max(ratio, 1e-30)), measuredBins=measured)
        records.append(record)
    report = {'schemaVersion': 1, 'state': 'TESTED', 'renderer': str(renderer), 'rendererSha256': sha256(renderer),
              'inputSha256': sha256(source), 'sampleRate': rate, 'toneHz': fundamental * rate / count,
              'inputPeak': .5, 'analysisFrames': count, 'dftCalibratedAmplitude': dry_amplitude,
              'method': 'Coherent2secondtone; last4096leftframes, rectangularDFT. Measure bins at folded harmonics5..64; first4harmonics lie belowNyquist. Whole factory presets including their filters/blend/echo, not isolated waveshapers.',
              'limits': 'Selected folded-bin energy is a limited alias indicator, not total alias power or an audibility/acceptance threshold. No oversampling reference. No level-matched vocal audition.',
              'formulaReference': 'https://numpy.org/doc/stable/reference/routines.fft.html',
              'listening': 'PENDING', 'aliasingAcceptability': 'PENDING', 'renders': records}
    (output / 'analysis.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'renders'}, indent=2))
    for record in records:
        if 'selectedFoldedBinsDbRelativeFundamental' in record:
            print(record['label'], record['selectedFoldedBinsDbRelativeFundamental'], 'dB selected folded bins; listening PENDING')


if __name__ == '__main__':
    main()
