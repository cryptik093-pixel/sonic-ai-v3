"""Read back a staged archive and verify every manifest member and checksum."""
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

archive = Path(sys.argv[1])
with zipfile.ZipFile(archive) as package:
    assert package.testzip() is None, 'ZIP integrity failure'
    manifests = [n for n in package.namelist() if n.endswith('/manifest.json')]
    assert len(manifests) == 1
    name = manifests[0]
    prefix = name[:-len('manifest.json')]
    manifest = json.loads(package.read(name).decode('utf-8-sig'))
    assert re.fullmatch(r'\d+\.\d+\.\d+-alpha',manifest['version']) and manifest['commercialReady'] is False
    expected = {prefix+f['path']: f for f in manifest['files']}
    actual = {n for n in package.namelist() if not n.endswith('/') and n != name}
    assert actual == set(expected), f'Manifest mismatch: {actual ^ set(expected)}'
    for member, info in expected.items():
        data = package.read(member)
        assert len(data) == info['bytes']
        assert hashlib.sha256(data).hexdigest() == info['sha256'], member
    binaries = [n for n in expected if n.endswith('/Contents/x86_64-win/OmegaSonicOrganism.vst3')]
    validations = [n for n in expected if '/validator-' in n and n.endswith('/result.json')]
    assert len(binaries) == len(validations) == 1
    result = json.loads(package.read(validations[0]).decode('utf-8-sig'))
    if 'pluginVersion' in result:
        assert result['pluginVersion'] == manifest['version']
    assert result['binarySha256'].lower() == expected[binaries[0]]['sha256']
    assert result['standardExit'] == result['extensiveExit'] == result['pluginvalExit'] == 0
    print(f'PASS ZIP integrity, {len(expected)} manifest files, hashes and matching validator binary.')
print('Archive SHA-256:', hashlib.sha256(archive.read_bytes()).hexdigest())
