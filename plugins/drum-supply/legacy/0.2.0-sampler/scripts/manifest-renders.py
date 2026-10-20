"""Record exact test-render state and provenance; never edits any audio file."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import wave

root = Path(__file__).resolve().parents[1]
directory = root / 'evidence' / 'renders'
renderer = root / 'build' / 'DrumDspTests.exe'
names = ['Kick', 'Snare', 'Hi-Hat', 'Cymbal', 'Tom', 'Percussion', 'Clap']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if not renderer.is_file():
        raise RuntimeError('Build and execute the native DSP test renderer first')
    records = []
    for department, name in enumerate(names):
        variants = [('default', [.5, .5, .25])]
        for macro in range(3):
            for label, value in [('low', 0), ('high', 1)]:
                state = [.5, .5, .25]
                state[macro] = value
                variants.append((f'macro{macro}-{label}', state))
        for variant, state in variants:
            path = directory / f'{department}-{variant}.wav'
            with wave.open(str(path), 'rb') as audio:
                metadata = dict(sample_rate=audio.getframerate(), channels=audio.getnchannels(),
                                bit_depth=audio.getsampwidth()*8, frames=audio.getnframes())
            if metadata != dict(sample_rate=48000, channels=2, bit_depth=16, frames=144000):
                raise RuntimeError(f'Unexpected test-render format: {path.name}')
            records.append(dict(path=path.name, sha256=sha(path), department=name,
                                body=state[0], character=state[1], space=state[2],
                                velocity=.8, midi_note=45, seed=0x93a17+department*7919,
                                duration_seconds=3, asset_class='synthetic_test_excerpt',
                                complete_decay_capture=False, parent_asset=None, **metadata))
    binary = root / 'build/OmegaDrumSupply_artefacts/Release/VST3/Omega Drum Supply.vst3/Contents/x86_64-win/Omega Drum Supply.vst3'
    manifest = dict(mission='OHOS-SONIC-INTEGRATION-001', version='0.1.0',
                    recorded_at=datetime.now(timezone.utc).isoformat(),
                    renderer_sha256=sha(renderer), engine_sha256=sha(root/'Source/DrumEngine.h'),
                    test_source_sha256=sha(root/'Tests/DspTests.cpp'),
                    plugin_sha256=sha(binary) if binary.is_file() else None,
                    optional_sample_libraries=[], approval='NOT_APPROVED_FOR_RELEASE',
                    listening='NOT_TESTED', assets=records)
    destination = directory/'manifest.json'
    destination.write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(f'Recorded {len(records)} immutable-audio hashes and complete macro state: {destination}')


if __name__ == '__main__':
    main()
