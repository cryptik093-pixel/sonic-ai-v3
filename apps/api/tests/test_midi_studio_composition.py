import pytest
from apps.api.workbench import midi, schemas


def compose(p):
    from apps.api.workbench.midi_studio import compose_studio
    return compose_studio(p)


def test_composer_exists():
    import importlib.util
    assert importlib.util.find_spec('apps.api.workbench.midi_studio'), 'v2 composer missing'


@pytest.mark.parametrize('style',['cloud','trap','soul'])
@pytest.mark.parametrize('scale',list(midi.SCALES))
@pytest.mark.parametrize('bars',[4,8,16,32])
def test_reproducible_in_key_with_valid_boundaries(style,scale,bars):
    p=schemas.MidiCommand(style=style,scale=scale,bars=bars,key='F#',settings={})
    notes=compose(p)
    assert notes==compose(p)
    assert notes!=compose(p.model_copy(update={'seed':194}))
    for n in notes:
        assert 0 <= n['start'] < bars*4 and n['duration'] > 0
        assert n['start']+n['duration'] <= bars*4+0.00001
        assert 1 <= n['velocity'] <= 127
        if n['track']!='Drums':
            r=getattr(p.settings,n['track'].lower()+'_range')
            assert r.low <= n['pitch'] <= r.high
            assert (n['pitch']-6)%12 in midi.SCALES[scale]


def test_track_streams_do_not_couple_and_selection():
    p=schemas.MidiCommand(settings={})
    q=p.model_copy(update={'settings':p.settings.model_copy(update={'drum_feel':'backbeat','hat_subdivision':'sixteenth'})})
    assert [n for n in compose(p) if n['track']!='Drums']==[n for n in compose(q) if n['track']!='Drums']
    assert {n['track'] for n in compose(schemas.MidiCommand(settings={'enabled_tracks':['Drums']}))}=={'Drums'}


def test_narrow_impossible_ranges_and_voicing():
    with pytest.raises(ValueError,match='voicing'):
        compose(schemas.MidiCommand(settings={'chord_type':'ninth','chords_range':{'low':60,'high':62}}))
    for chord_type,size in [('triad',3),('seventh',4),('ninth',5)]:
        notes=compose(schemas.MidiCommand(settings={'chord_type':chord_type,'timing_ms':0,'chord_spread_ms':0}))
        assert len([n for n in notes if n['track']=='Chords' and n['start']==0])==size


@pytest.mark.parametrize('change',[
 {'swing':67},{'timing_ms':30},{'velocity_variation':0},{'motif_variation':100},{'syncopation':100},
 {'contour':'ascending'},{'contour':'descending'},{'contour':'arch'}, {'voicing':'open'},
 {'smooth_voice_leading':False},{'chord_spread_ms':40},{'bass_mode':'sustained'},
 {'drum_feel':'backbeat'},{'hat_subdivision':'sixteenth'},{'phrase_ending':'open'},
 {'progression':[1,4,5,1]},{'progression_rate':4},
 {'melody_velocity':100},{'chords_velocity':100},{'bass_velocity':100},{'drums_velocity':100},
 {'melody_range':{'low':72,'high':84}}, {'chords_range':{'low':60,'high':90}}, {'bass_range':{'low':36,'high':59}},
])
def test_each_control_has_observable_effect(change):
    assert compose(schemas.MidiCommand(settings={})) != compose(schemas.MidiCommand(settings=change))


def test_zero_jitter_and_extreme_seeds():
    for seed in [0,93,2147483647]:
        p=schemas.MidiCommand(seed=seed,settings={'timing_ms':0,'chord_spread_ms':0,'velocity_variation':0,'swing':50,'syncopation':0})
        for n in compose(p):
            assert n['start']*4==round(n['start']*4)

@pytest.mark.parametrize('density',['sparse','balanced','busy'])
@pytest.mark.parametrize('bars',[4,8,16,32])
def test_tonic_ending_resolves_last_emitted_note(density,bars):
    notes=compose(schemas.MidiCommand(density=density,bars=bars,settings={'timing_ms':0,'phrase_ending':'tonic'}))
    last=max((n for n in notes if n['track']=='Melody'),key=lambda n:n['start'])
    assert last['pitch']%12==0
