"""Real browser regressions for the independent MIDI Studio review findings."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import httpx
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]


def main():
    findings={}
    with tempfile.TemporaryDirectory(prefix='studio-review-') as temp:
        token='review-regression-token'
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        base=f'http://127.0.0.1:{port}'
        env={**os.environ,'SONIC_DATA_DIR':temp,'SONIC_DB_PATH':temp+'/sonic.db','SONIC_EVENT_DB':temp+'/events.db','SONIC_CONTROL_PLANE_TOKEN':token,'PYTHON_DOTENV_DISABLED':'1'}
        for key in ['SONIC_DESKTOP_MODE','SONIC_DESKTOP_TOKEN','SONIC_OAUTH_ISSUER','SONIC_PUBLIC_MCP_URL','SONIC_OAUTH_JWKS_URL','SONIC_OPENAI_API_KEY','OPENAI_API_KEY']:env.pop(key,None)
        proc=subprocess.Popen([sys.executable,'-m','uvicorn','apps.api.main:app','--host','127.0.0.1','--port',str(port)],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            with httpx.Client(base_url=base,headers={'Authorization':'Bearer '+token},trust_env=False) as api:
                deadline=time.monotonic()+30
                while True:
                    try:
                        if api.get('/health').status_code==200:break
                    except httpx.HTTPError:pass
                    assert time.monotonic()<deadline;time.sleep(.1)
                with sync_playwright() as pw:
                    browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
                    page=browser.new_page();errors=[]
                    page.on('pageerror',lambda e:errors.append(str(e)))
                    page.goto(base+'/workbench#token='+token)
                    page.wait_for_function("document.getElementById('connection-status').textContent.includes('ready')")
                    page.locator('nav button[data-view=midi]').click()
                    page.locator('#midi-form [name=bars]').select_option('4')
                    page.locator('#midi-form button[type=submit]').click()
                    page.locator('#midi-result [data-file="Quality_Report.json"]').wait_for()
                    page.locator('#busy').wait_for(state='hidden')
                    # Editing after proposal arrival must retain the newer value.
                    page.locator('#midi-form [name=prompt]').fill('150 bpm')
                    page.locator('#interpret-midi').click()
                    page.locator('#apply-midi-proposal').wait_for()
                    page.locator('#midi-form [name=bpm]').fill('170')
                    page.locator('#apply-midi-proposal').click()
                    findings['proposal_keeps_newer_bpm']=page.locator('#midi-form [name=bpm]').input_value()=='170'
                    # A deliberate revision seed is part of the saved generation state.
                    page.locator('#midi-result [data-reuse-midi]').click()
                    page.locator('#busy').wait_for(state='hidden')
                    page.locator('#midi-form [name=seed]').fill('98765')
                    page.locator('#midi-result [data-revise-track="Melody"]').check()
                    page.locator('#midi-result [data-revise]').click()
                    page.locator('#busy').wait_for(state='hidden')
                    run_id=page.locator('#midi-result [data-output-id]').get_attribute('data-output-id')
                    findings['revision_honors_displayed_seed']=api.get('/workbench/api/runs/'+run_id).json()['result']['seed']==98765
                    for kind,selector in [('midi/revise','[data-revise]'),('midi','[data-regenerate-midi]')]:
                        if kind=='midi/revise':
                            page.locator('#midi-form [name=seed]').fill('12345')
                            page.locator('#midi-result [data-revise-track="Melody"]').check()
                        intercepted=[]
                        def lost(route):
                            response=route.fetch();intercepted.append(response.json());route.abort('failed')
                        page.route(base+'/workbench/api/'+kind,lost)
                        page.locator('#midi-result '+selector).click()
                        page.locator('#error').wait_for(state='visible')
                        page.locator('#busy').wait_for(state='hidden')
                        page.unroute(base+'/workbench/api/'+kind,lost)
                        page.locator('#midi-result '+selector).click()
                        page.locator('#busy').wait_for(state='hidden')
                        findings['lost_response_retry_'+kind]=page.locator('#midi-result [data-output-id]').get_attribute('data-output-id')==intercepted[0]['id']
                    # Syntactically valid but malformed state cannot prevent startup.
                    errors.clear();page.evaluate("localStorage.setItem('sonic-inputs',JSON.stringify({'midi-form':null}))")
                    page.reload();page.wait_for_timeout(700)
                    findings['malformed_form_state_boots']=not errors and 'ready' in page.locator('#connection-status').inner_text()
                    page.evaluate("localStorage.removeItem('sonic-inputs')");page.reload()
                    page.wait_for_function("document.getElementById('connection-status').textContent.includes('ready')")
                    page.locator('nav button[data-view=midi]').click()
                    # A newly enabled track must be selectable for regeneration.
                    page.locator('#midi-form [name=engine_mode]').select_option('studio')
                    for track in ['Melody','Chords','Bass']:page.locator('#midi-form [name=track_'+track+']').uncheck()
                    page.locator('#midi-form button[type=submit]').click();page.locator('#busy').wait_for(state='hidden')
                    page.locator('#midi-result [data-reuse-midi]').click();page.locator('#busy').wait_for(state='hidden')
                    page.locator('#midi-form [name=track_Melody]').check()
                    findings['new_track_revision_selector']=page.locator('#midi-result [data-revise-track="Melody"]').count()==1
                    if findings['new_track_revision_selector']:
                        page.locator('#midi-result [data-revise-track="Melody"]').check()
                        page.locator('#midi-result [data-revise-track="Drums"]').check()
                        page.locator('#midi-result [data-revise]').click();page.locator('#busy').wait_for(state='hidden')
                        findings['new_track_revision_export']=page.locator('#midi-result [data-file="Melody.mid"]').count()==1
                    browser.close()
        finally:
            proc.terminate();proc.wait(timeout=10)
    print(json.dumps(findings,indent=2))
    assert all(findings.values()),findings


if __name__=='__main__':main()
