import importlib.util
import json
from pathlib import Path
import pytest
import mido
from apps.api.workbench.schemas import MidiCommand


def test_exporter_exists():
    assert importlib.util.find_spec('apps.api.workbench.midi_quality'), 'quality/export missing'


def export(p,folder):
    from apps.api.workbench.midi_studio import compose_studio
    from apps.api.workbench.midi_quality import export_studio
    return export_studio(p,compose_studio(p),folder,{'run_id':'run-fixture','owner_id':'local-producer','workspace_id':'omega-house-studio','project_id':None})


@pytest.mark.parametrize('tracks',[['Melody','Chords','Bass','Drums'],['Drums'],['Melody']])
@pytest.mark.parametrize('bars',[4,32])
def test_exports_note_lifecycles_hashable_and_selected(tmp_path,tracks,bars):
    p=MidiCommand(bars=bars,settings={'enabled_tracks':tracks},density='busy')
    result=export(p,tmp_path)
    for name in ['Melody','Chords','Bass','Drums']:
        assert (tmp_path/f'{name}.mid').exists()==(name in tracks)
    for path in tmp_path.glob('*.mid'):
        song=mido.MidiFile(path)
        assert song.length==pytest.approx(bars*4*60/p.bpm,abs=.001)
        for track in song.tracks:
            held=set();tick=0
            for msg in track:
                assert msg.time>=0
                tick+=msg.time
                if msg.type=='note_on' and msg.velocity:
                    key=(msg.channel,msg.note)
                    assert key not in held
                    held.add(key)
                    assert tick<bars*4*480
                elif msg.type=='note_off':
                    held.remove((msg.channel,msg.note))
            assert not held and tick==bars*4*480
    metadata=json.loads((tmp_path/'Composition.json').read_text())
    assert metadata['schema_version']=='2.0' and metadata['run_id']=='run-fixture'
    assert metadata['instrument_state']=='unspecified'
    assert result['quality']['technical']['passed']
    assert result['decision_record']['status']=='proposed'
    other=tmp_path/'other';other.mkdir();export(p,other)
    for path in tmp_path.glob('*.mid'):
        assert path.read_bytes()==(other/path.name).read_bytes()


def test_invalid_notes_rejected_and_metrics():
    from apps.api.workbench.midi_quality import validate_notes,measure_notes
    p=MidiCommand(settings={})
    with pytest.raises(ValueError):
        validate_notes([{'track':'Melody','pitch':61,'start':0,'duration':1,'velocity':80}],p)
    notes=[{'track':'Melody','pitch':60,'start':0,'duration':1,'velocity':80}, {'track':'Melody','pitch':72,'start':2,'duration':1,'velocity':80}]
    m=measure_notes(notes,p)
    assert m['note_count']==2 and m['max_melodic_leap_semitones']==12


def test_repeated_same_tick_off_on_lifecycle(tmp_path):
    from apps.api.workbench.midi_quality import export_studio
    p=MidiCommand(bars=4,settings={'enabled_tracks':['Melody']})
    notes=[{'track':'Melody','pitch':60,'start':i,'duration':1,'velocity':80} for i in range(16)]
    export_studio(p,notes,tmp_path,{})
    held=set()
    for m in mido.MidiFile(tmp_path/'Melody.mid').tracks[0]:
        if m.type=='note_on':
            assert m.note not in held;held.add(m.note)
        if m.type=='note_off':held.remove(m.note)
    assert not held


def test_same_chord_jitter_does_not_invent_voice_movement():
    from apps.api.workbench.midi_studio import compose_studio
    from apps.api.workbench.midi_quality import measure_notes
    p=MidiCommand(bars=4,settings={'enabled_tracks':['Chords'],'progression':[1],'chord_spread_ms':0,'timing_ms':8})
    assert measure_notes(compose_studio(p),p)['adjacent_chord_movement_semitones']==[0,0,0]


def test_enabled_track_without_notes_rejected():
    from apps.api.workbench.midi_studio import compose_studio
    from apps.api.workbench.midi_quality import validate_notes
    p=MidiCommand(settings={'enabled_tracks':['Drums']})
    notes=compose_studio(p)
    with pytest.raises(ValueError,match='enabled track'):
        validate_notes(notes,MidiCommand(settings={'enabled_tracks':['Drums','Melody']}))
