import asyncio
import json
import pytest
from apps.api.tests.test_workbench import client
from apps.api.main import app


def rpc(client,name,command):
    r=client.post('/mcp',headers={'Accept':'application/json, text/event-stream'},json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':{'command':command}}})
    assert r.status_code==200,r.text
    return r.json()['result']


def test_mcp_studio_shared_services(client):
    result=rpc(client,'sonic_generate_midi',{'bars':4,'settings':{}})
    assert not result['isError']
    parent=json.loads(result['content'][0]['text'])
    assert parent['result']['engine']=='local_composition_v3'
    revision=rpc(client,'sonic_revise_midi',{'parent_run_id':parent['id'],'regenerate_tracks':['Drums'],'seed':194})
    assert not revision['isError']
    interpretation=rpc(client,'sonic_interpret_midi_prompt',{'prompt':'140 bpm'})
    assert not interpretation['isError']
    assert json.loads(interpretation['content'][0]['text'])['proposed_settings']['bpm']==140


def test_mcp_oauth_revision_guard(client,monkeypatch):
    from apps.api.integrations.gateway import build_mcp
    server=build_mcp(lambda:app.state.control_plane)
    monkeypatch.setenv('SONIC_PUBLIC_MCP_URL','https://sonic.example/mcp')
    from uuid import uuid4
    with pytest.raises(Exception,match='OAuth read scopes'):
        asyncio.run(server.call_tool('sonic_revise_midi',{'command':{'parent_run_id':str(uuid4()),'regenerate_tracks':['Drums']}}))
