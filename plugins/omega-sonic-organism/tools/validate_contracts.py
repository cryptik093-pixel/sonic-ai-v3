"""Validate the portable product contracts without third-party packages."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
params = json.loads((ROOT / 'contracts/parameters.json').read_text())
presets = json.loads((ROOT / 'contracts/preset.schema.json').read_text())
anchors = json.loads((ROOT / 'contracts/identity_anchors.json').read_text())
assert params['schema_version'] == presets['properties']['schema_version']['const'] == anchors['schema_version'] == 1
ids = [p['id'] for p in params['parameters']]
keys = [p['key'] for p in params['parameters']]
assert len(ids) == len(set(ids)) and len(keys) == len(set(keys))
assert all(isinstance(i, int) and 0 <= i <= 0x7fffffff for i in ids)
assert set(keys) == set(presets['properties']['params']['properties'])
assert [round(a['morph'],2) for a in anchors['anchors']] == [0,0.25,0.5,0.75,1.0]
for p in params['parameters']:
    n = p['default_normalized']
    assert 0 <= n <= 1
    if p['kind'] == 'enumeration':
        options = len(p['choices']) - 1
        assert any(abs(n - k / options) < 1e-12 for k in range(options + 1))
        assert presets['properties']['params']['properties'][p['key']]['enum'] == [k/options for k in range(options + 1)]
print('Contracts valid: unique stable IDs; patch keys, enums and anchors aligned.')
