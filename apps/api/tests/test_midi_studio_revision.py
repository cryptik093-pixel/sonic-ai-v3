import copy
import importlib.util
from uuid import uuid4
import pytest
from apps.api.workbench import midi
from apps.api.workbench.schemas import MidiCommand,MidiRevisionCommand


def test_revision_module_exists():
    assert importlib.util.find_spec('apps.api.workbench.midi_revision'), 'revision module missing'


def parent(legacy=False):
    from apps.api.workbench.midi_studio import compose_studio
    p=MidiCommand(settings=None if legacy else {})
    return {'id':str(uuid4()),'owner_id':'local-producer','workspace_id':'omega-house-studio','project_id':None,'kind':'midi','status':'succeeded',
            'request':p.model_dump(mode='json'),'result':{'notes':midi.compose(p) if legacy else compose_studio(p)}}


def resolve(p,**kw):
    from apps.api.workbench.midi_revision import resolve_revision
    return resolve_revision(p,MidiRevisionCommand(parent_run_id=p['id'],regenerate_tracks=['Melody'],seed=194,**kw))


def test_locked_tracks_exact_parent_immutable():
    p=parent();saved=copy.deepcopy(p)
    command,notes,meta=resolve(p,settings_patch={'settings':{'contour':'ascending'}})
    assert [n for n in notes if n['track']!='Melody']==[n for n in p['result']['notes'] if n['track']!='Melody']
    assert [n for n in notes if n['track']=='Melody']!=[n for n in p['result']['notes'] if n['track']=='Melody']
    assert p==saved and meta['parent_run_id']==p['id']


@pytest.mark.parametrize('patch',[{'key':'D'},{'scale':'major'},{'bpm':140},{'bars':16},{'settings':{'enabled_tracks':['Melody']}}, {'settings':{'bass_velocity':50}}, {'project_id':123}, {'unrecognized':True}])
def test_unsafe_or_invalid_patches_reject(patch):
    with pytest.raises(ValueError):resolve(parent(),settings_patch=patch)


@pytest.mark.parametrize('field,value',[('status','failed'),('kind','pack'),('owner_id','other'),('workspace_id','other')])
def test_invalid_parents_reject(field,value):
    p=parent();p[field]=value
    with pytest.raises(ValueError):resolve(p)


def test_legacy_requires_explicit_upgrade_preserves_locked_notes():
    p=parent(True)
    with pytest.raises(ValueError,match='v2'):resolve(p)
    _,notes,_=resolve(p,settings_patch={'settings':{'version':2}})
    assert [n for n in notes if n['track']!='Melody']==[n for n in p['result']['notes'] if n['track']!='Melody']


def test_new_enabled_track_must_be_regenerated():
    from apps.api.workbench.midi_studio import compose_studio
    from apps.api.workbench.midi_revision import resolve_revision
    p=parent()
    c=MidiCommand(settings={'enabled_tracks':['Drums']})
    p['request']=c.model_dump(mode='json');p['result']['notes']=compose_studio(c)
    cmd=MidiRevisionCommand(parent_run_id=p['id'],regenerate_tracks=['Drums'],settings_patch={'settings':{'enabled_tracks':['Drums','Melody']}})
    with pytest.raises(ValueError,match='newly enabled'):resolve_revision(p,cmd)


def test_null_enabled_tracks_is_validation_error():
    with pytest.raises(ValueError):resolve(parent(),settings_patch={'settings':{'enabled_tracks':None}})


def test_locked_track_parameters_must_remain_truthful():
    with pytest.raises(ValueError,match='Chords'):
        resolve(parent(),settings_patch={'settings':{'chord_type':'seventh'}})
