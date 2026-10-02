"""Musical constraints plus independently decoded five-part export contracts."""
import copy
from itertools import product
from uuid import uuid4
import mido
import pytest
from apps.api.workbench import midi
from apps.api.workbench.schemas import MidiCommand, MidiRevisionCommand
from apps.api.workbench.midi_studio import compose_studio, ENGINE
from apps.api.workbench.midi_quality import validate_notes, measure_notes, export_studio
from apps.api.workbench.midi_revision import resolve_revision
from apps.api.workbench.harmony import harmonic_plan, chord_classes

TRACKS=['Melody','Chords','Bass','Drums','Countermelody']


@pytest.mark.parametrize('key,scale,style,density', list(product(['C','F#','B'],midi.SCALES,['cloud','trap','soul'],['sparse','balanced','busy'])))
def test_five_parts_coherent_and_reproducible(key,scale,style,density):
    p=MidiCommand(key=key,scale=scale,style=style,density=density,bars=16,
                  settings={'enabled_tracks':TRACKS,'timing_ms':0,'chord_spread_ms':0,'syncopation':0})
    notes=compose_studio(p)
    assert notes==compose_studio(p)
    validate_notes(notes,p)
    harmony=harmonic_plan(p)
    assert harmony[-1]==0
    for track in ['Melody','Bass','Countermelody']:
        part=[n for n in notes if n['track']==track]
        assert all(a['start']+a['duration']<=b['start']+1e-9 for a,b in zip(part,part[1:]))
        if track!='Bass':
            assert all(abs(a['pitch']-b['pitch'])<=p.settings.max_melodic_leap for a,b in zip(part,part[1:]))
    melody=[n for n in notes if n['track']=='Melody']
    for n in melody:
        if n['start']%4 in (0,2):
            assert n['pitch']%12 in chord_classes(p,harmony[int(n['start']//4)])
    assert melody[-1]['pitch']%12==midi.ROOTS[key]
    assert measure_notes(notes,p)['countermelody_lead_overlap_events']==0
    bass=[n['pitch']%12 for n in notes if n['track']=='Bass']
    assert len(set(bass))>1


def test_loop_preserves_custom_progression():
    p=MidiCommand(bars=8,settings={'progression':[1,4,5,7],'progression_rate':2,'cadence':'loop','phrase_ending':'open'})
    assert harmonic_plan(p)==[0,0,3,3,4,4,6,6]


def test_counter_roundtrip_exact_notes_and_channels(tmp_path):
    p=MidiCommand(bars=4,settings={'enabled_tracks':TRACKS})
    notes=compose_studio(p);export_studio(p,notes,tmp_path,{'run_id':'coherence-proof'})
    combined=next(f for f in tmp_path.glob('*.mid') if f.stem not in TRACKS)
    song=mido.MidiFile(combined)
    assert song.type==1 and len(song.tracks)==6
    for name,channel,_ in midi.TRACKS+midi.STUDIO_EXTRA_TRACKS:
        part=mido.MidiFile(tmp_path/f'{name}.mid')
        held={};decoded=[];tick=0
        for message in part.tracks[0]:
            tick+=message.time
            if message.type=='note_on':
                assert message.channel==channel
                held[message.note]=(tick,message.velocity)
            elif message.type=='note_off':
                start,velocity=held.pop(message.note)
                decoded.append((message.note,start,tick-start,velocity))
        expected=[(n['pitch'],round(n['start']*480),round(n['duration']*480),n['velocity']) for n in notes if n['track']==name]
        assert sorted(decoded)==sorted(expected) and not held and tick==4*4*480


def test_counter_revision_uses_actual_locked_lead():
    p=MidiCommand(settings={'enabled_tracks':TRACKS})
    parent={'id':str(uuid4()),'owner_id':'local-producer','workspace_id':'omega-house-studio','project_id':None,
            'kind':'midi','status':'succeeded','request':p.model_dump(mode='json'),
            'result':{'engine':ENGINE,'notes':compose_studio(p)}}
    saved=copy.deepcopy(parent)
    q,notes,meta=resolve_revision(parent,MidiRevisionCommand(parent_run_id=parent['id'],regenerate_tracks=['Countermelody'],seed=194))
    assert parent==saved
    assert [n for n in notes if n['track']!='Countermelody']==[n for n in parent['result']['notes'] if n['track']!='Countermelody']
    assert measure_notes(notes,q)['countermelody_lead_overlap_events']==0
    assert meta['track_generation_state']['Countermelody']['engine']==ENGINE
    with pytest.raises(ValueError,match='response lead'):
        resolve_revision(parent,MidiRevisionCommand(parent_run_id=parent['id'],regenerate_tracks=['Melody'],seed=194))
    with pytest.raises(ValueError,match='Unlock'):
        resolve_revision(parent,MidiRevisionCommand(parent_run_id=parent['id'],regenerate_tracks=['Countermelody'],settings_patch={'settings':{'cadence':'loop'}}))


def test_counter_only_and_parallel_mode():
    for mode in ['response','parallel']:
        p=MidiCommand(settings={'enabled_tracks':['Countermelody'],'counter_mode':mode})
        assert {n['track'] for n in compose_studio(p)}=={'Countermelody'}


def test_older_studio_revision_keeps_harmonic_timeline():
    p=MidiCommand(settings={})
    settings=p.model_dump(mode='json');settings['settings'].pop('cadence')
    parent={'id':str(uuid4()),'owner_id':'local-producer','workspace_id':'omega-house-studio','project_id':None,
            'kind':'midi','status':'succeeded','request':settings,'result':{'engine':'local_composition_v2','notes':compose_studio(p)}}
    q,_,_=resolve_revision(parent,MidiRevisionCommand(parent_run_id=parent['id'],regenerate_tracks=['Melody']))
    assert q.settings.cadence=='loop'
