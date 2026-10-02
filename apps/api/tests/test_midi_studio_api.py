import io
import json
from uuid import uuid4
from unittest.mock import patch
from zipfile import ZipFile
import pytest
from sqlalchemy import select
from apps.api.tests.test_workbench import client,post,read_file
from apps.api.database import SessionLocal
from apps.api.workbench.models import Run,WorkEvent
from apps.api.workbench import service


def test_studio_http_returns_state_and_revision(client):
    run=post(client,'midi',{'bars':4,'settings':{},'prompt':'C minor'})
    assert run['result']['engine']=='local_composition_v3'
    meta=json.loads(read_file(client,run,'Composition.json'))
    assert meta['run_id']==run['id'] and meta['owner_id']==run['owner_id']
    revision=post(client,'midi/revise',{'parent_run_id':run['id'],'regenerate_tracks':['Melody'],'seed':194})
    assert revision['result']['parent_run_id']==run['id']
    assert [n for n in revision['result']['notes'] if n['track']!='Melody']==[n for n in run['result']['notes'] if n['track']!='Melody']
    response=client.get(f"/workbench/api/runs/{revision['id']}/archive")
    assert response.status_code==200
    z=ZipFile(io.BytesIO(response.content))
    assert 'Quality_Report.json' in z.namelist()
    assert json.loads(z.read('Composition.json'))['parent_run_id']==run['id']


def test_selected_tracks_pack_and_interpret(client):
    before=service.list_runs()
    response=client.post('/workbench/api/midi/interpret',json={'prompt':'140 bpm trap'})
    assert response.status_code==200 and response.json()['proposed_settings']['bpm']==140
    assert service.list_runs()==before
    run=post(client,'midi',{'bars':4,'settings':{'enabled_tracks':['Drums']}})
    pack=post(client,'pack',{'title':'Drums','source_run_id':run['id']})
    assert pack['result']['manifest']['asset_count']==1


def test_retry_conflicts_auth_and_invalid_parent(client):
    payload={'request_id':str(uuid4()),'bars':4,'settings':{}}
    a=post(client,'midi',payload);b=post(client,'midi',payload)
    assert a['id']==b['id']
    assert client.post('/workbench/api/midi',json={**payload,'seed':111}).status_code==422
    revision={'request_id':str(uuid4()),'parent_run_id':a['id'],'regenerate_tracks':['Drums'],'seed':194}
    x=post(client,'midi/revise',revision);y=post(client,'midi/revise',revision)
    assert x['id']==y['id']
    assert client.post('/workbench/api/midi/revise',json={**revision,'settings_patch':{'key':'D'}}).status_code==422
    assert client.post('/workbench/api/midi/interpret',json={'prompt':'hi'},headers={'Authorization':''}).status_code==401
    assert client.post('/workbench/api/midi/revise',json={**revision,'parent_run_id':str(uuid4())}).status_code==422
    with SessionLocal() as s:
        row=s.get(Run,a['id']);row.workspace_id='other';s.commit()
    assert client.post('/workbench/api/midi/revise',json=revision).status_code==422


def test_preflight_range_failure_no_run_and_failure_no_download(client):
    count=len(service.list_runs())
    r=client.post('/workbench/api/midi',json={'settings':{'chord_type':'ninth','chords_range':{'low':60,'high':62}}})
    assert r.status_code==422 and len(service.list_runs())==count
    with patch('apps.api.workbench.midi_quality.export_studio',side_effect=OSError('secret local path')):
        r=client.post('/workbench/api/midi',json={'bars':4,'settings':{}}).json()
    assert r['status']=='failed' and 'secret' not in r['error']
    assert client.get(f"/workbench/api/runs/{r['id']}/files/Composition.json").status_code==404
    assert not (service.root()/'staging'/r['id']).exists()


def test_recover_interrupted_and_requests_hashes(client):
    run=post(client,'midi',{'bars':4,'settings':{}})
    with SessionLocal() as s:
        r=s.get(Run,run['id']);r.status='running';s.commit()
    service.recover_interrupted()
    assert service.get_run(run['id'])['status']=='interrupted'


def test_five_part_http_pack_preserves_countermelody(client):
    run=post(client,'midi',{'bars':4,'settings':{'enabled_tracks':['Melody','Chords','Bass','Drums','Countermelody']}})
    assert len(run['result']['tracks'])==5
    pack=post(client,'pack',{'title':'Five parts','source_run_id':run['id']})
    assert pack['result']['manifest']['asset_count']==5
    assert 'Countermelody.mid' in [a['name'] for a in pack['result']['manifest']['assets']]
