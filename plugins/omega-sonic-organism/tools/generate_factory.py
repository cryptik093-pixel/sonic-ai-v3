"""Build the embedded resource from versioned JSON patches, or seed the specified bank.
Seeding is explicit and refuses to overwrite patches. Rebuilding preserves calibration.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--seed', action='store_true')
args = parser.parse_args()
bank = ROOT / 'presets' / 'factory-v1'
bank.mkdir(parents=True, exist_ok=True)
if args.seed:
    contract = json.loads((ROOT / 'contracts/parameters.json').read_text())
    # The contract generator defines defaults in normalized coordinates.
    defaults = dict(morph=0, energy=.5, motion=.25, material=.5, space=0,
                    output=.6, attack_scale=.5, release_scale=.5, glide_ms=0,
                    polyphony=2/3, quality=0, bend_range=0, lfo_sync=1,
                    lfo_rate=.56525, mono_legato=0)
    for line in (ROOT / 'docs/FACTORY_PRESET_SPEC.md').read_text(encoding='utf-8').splitlines():
        fields = [s.strip() for s in line.strip('|').split('|')]
        if len(fields) != 8 or len(fields[0]) != 3 or not fields[0][1:].isdigit():
            continue
        code, name = fields[:2]
        values = defaults | dict(zip(('morph', 'energy', 'motion', 'material', 'space'), map(float, fields[2:7])))
        family = dict(B='bass', E='bells', L='lead', S='synth', P='percussion', X='transition')[code[0]]
        if code[0] == 'B':
            values.update(polyphony=0, mono_legato=1, glide_ms=.025, release_scale=.38)
        if code[0] == 'L':
            values.update(polyphony=0, mono_legato=1, glide_ms=.045 if code=='L05' else .012)
        if code[0] == 'S':
            values.update(attack_scale=.76 if code in ('S01','S04') else .5, release_scale=.64)
        if code[0] == 'P':
            values.update(attack_scale=.25, release_scale=.28, polyphony=1/3)
        if code == 'B04':
            values.update(mono_legato=0, release_scale=.18)
        patch = dict(schema_version=1, instrument='omega-sonic-organism', name=name,
                     author='Omega House Studio LLC', description=fields[7], tags=[family, code], params=values)
        path = bank / f'{code}-{name.replace(" ", "-")}.json'
        with path.open('x', encoding='utf-8', newline='\n') as out:
            json.dump(patch, out, indent=2, ensure_ascii=False)
            out.write('\n')

patches = sorted(bank.glob('*.json'))
assert len(patches)==30, f'Expected 30 patches, found {len(patches)}'
out = ['// Generated from presets/factory-v1/*.json by tools/generate_factory.py.',
       '#pragma once', '#include <array>', 'namespace omega {',
       'inline constexpr std::array<const char*,30> factoryDocuments{{']
for path in patches:
    document = json.dumps(json.loads(path.read_text(encoding='utf-8')), ensure_ascii=False, separators=(',', ':'))
    assert ')OSOPATCH"' not in document
    out.append('R"OSOPATCH('+document+')OSOPATCH",')
out += ['}};', '}']
(ROOT / 'core/include/omega/FactoryBank.h').write_text('\n'.join(out)+'\n', encoding='utf-8')
print('Embedded 30 versioned JSON patches; sound review is a separate gate.')
