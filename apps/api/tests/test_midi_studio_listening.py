import importlib.util
from pathlib import Path
import hashlib
import csv
import mido


def test_listening_script_exists_and_pairs(tmp_path):
    path=Path(__file__).resolve().parents[3]/'scripts/prepare-midi-studio-listening.py'
    assert path.exists(), 'listening preparation script missing'
    spec=importlib.util.spec_from_file_location('listening',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    manifest=module.prepare_pairs(tmp_path)
    assert len(manifest['pairs'])==6
    for pair in manifest['pairs']:
        assert pair['key']=='C' and pair['scale']=='minor' and pair['bpm']==130 and pair['bars']==8
        for side in ['legacy','studio']:
            path=tmp_path/pair[side]['path']
            assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==pair[side]['sha256']
            assert mido.MidiFile(path).length>0
    rows=list(csv.DictReader((tmp_path/'Listening_Scores.csv').open()))
    assert len(rows)==12 and all(r['harmonic_coherence']=='' for r in rows)
