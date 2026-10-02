"""Real Chromium clicks/downloads against a fresh local API. Requires playwright."""
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from zipfile import ZipFile

import httpx
import mido
import numpy as np
import soundfile as sf
from playwright.sync_api import sync_playwright

ROOT = Path(os.getenv("SONIC_VERIFY_ROOT", str(Path(__file__).resolve().parents[1]))).resolve()


def main():
    with tempfile.TemporaryDirectory(prefix="sonic-browser-proof-") as temp:
        data = Path(temp)
        token = "browser-fixture-token"
        with socket.socket() as socket_:
            socket_.bind(("127.0.0.1", 0))
            port = socket_.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        env = {**os.environ, "SONIC_DATA_DIR":str(data), "SONIC_DB_PATH":str(data / "sonic.db"),
               "SONIC_EVENT_DB":str(data / "events.db"), "SONIC_CONTROL_PLANE_TOKEN":token,
               "PYTHON_DOTENV_DISABLED":"1"}
        for name in ("SONIC_DESKTOP_MODE", "SONIC_DESKTOP_TOKEN", "SONIC_OAUTH_ISSUER", "SONIC_PUBLIC_MCP_URL", "SONIC_OAUTH_JWKS_URL", "SONIC_OPENAI_API_KEY", "OPENAI_API_KEY"):
            env.pop(name, None)
        process = subprocess.Popen([sys.executable,"-m","uvicorn","apps.api.main:app","--host","127.0.0.1","--port",str(port)],
                                    cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            with httpx.Client(base_url=base,trust_env=False,timeout=1) as api:
                deadline = time.monotonic()+30
                while True:
                    assert process.poll() is None, "API process exited"
                    try:
                        if api.get("/health").status_code==200:
                            break
                    except httpx.HTTPError:
                        pass
                    assert time.monotonic()<deadline,"API startup timeout"
                    time.sleep(.1)
            with sync_playwright() as pw:
                options={"headless":True,"args":["--no-sandbox","--autoplay-policy=no-user-gesture-required"]}
                if os.getenv("SONIC_TEST_BROWSER"):
                    options["executable_path"]=os.environ["SONIC_TEST_BROWSER"]
                browser=pw.chromium.launch(**options)
                page=browser.new_page(viewport={"width":1320,"height":950},accept_downloads=True)
                errors=[]
                page.on("pageerror",lambda error:errors.append(str(error)))
                page.goto(base+"/workbench#token="+token)
                page.wait_for_function("document.getElementById('connection-status').textContent.includes('ready')")
                assert "token" not in page.url
                screenshot=Path(os.getenv("SONIC_SCREENSHOT_DIR","/tmp/sonic-screenshots"))
                screenshot.mkdir(parents=True,exist_ok=True)
                page.screenshot(path=str(screenshot/"01-start.png"),full_page=True)
                page.locator("nav button[data-view=midi]").click()
                page.locator("#midi-form input[name=title]").fill("Browser Proof")
                page.locator("#midi-form select[name=bars]").select_option("4")
                page.locator("#midi-form button[type=submit]").click()
                page.locator("#midi-result [data-file='Melody.mid']").wait_for(timeout=30000)
                page.wait_for_function("document.querySelector('#midi-result audio')?.src.startsWith('blob:')")
                page.locator("#midi-result audio").evaluate("a => a.play()")
                page.wait_for_function("document.querySelector('#midi-result audio').currentTime > 0.1")
                page.locator("#midi-result audio").evaluate("a => a.pause()")
                with page.expect_download() as download:
                    page.locator("#midi-result [data-file='Melody.mid']").click()
                song=mido.MidiFile(download.value.path())
                assert any(m.type=="note_on" for t in song.tracks for m in t)
                page.screenshot(path=str(screenshot/"02-midi.png"),full_page=True)
                # Studio controls, proposals, immutable revisions and exports.
                page.locator("#midi-form [name=prompt]").fill("F# minor 140 bpm 4 bars trap")
                page.locator("#interpret-midi").click()
                page.locator("#apply-midi-proposal").wait_for()
                page.locator("#apply-midi-proposal").click()
                assert page.locator("#midi-form [name=bpm]").input_value()=="140"
                previous_id=page.locator("#midi-result [data-output-id]").get_attribute("data-output-id")
                page.locator("#midi-form button[type=submit]").click()
                page.wait_for_function("document.querySelector('#midi-result [data-output-id]')?.dataset.outputId !== "+json.dumps(previous_id))
                page.locator("#busy").wait_for(state="hidden")
                page.locator("#midi-result [data-file='Quality_Report.json']").wait_for(timeout=30000)
                parent_id=page.locator("#midi-result [data-output-id]").get_attribute("data-output-id")
                page.locator("#midi-result [data-revise-track='Melody']").check()
                page.locator("#midi-result [data-revise]").click()
                page.wait_for_function("document.querySelector('#midi-result [data-output-id]')?.dataset.outputId !== "+json.dumps(parent_id))
                page.locator("#busy").wait_for(state="hidden")
                assert parent_id[:8] in page.locator("#midi-result").inner_text()
                with page.expect_download() as download:
                    page.locator("#midi-result [data-file='Composition.json']").click()
                revision=json.loads(Path(download.value.path()).read_text())
                assert revision["parent_run_id"]==parent_id
                page.locator("#midi-result [data-reuse-midi]").click()
                assert page.locator("#midi-form [name=bpm]").input_value()=="140"
                page.screenshot(path=str(screenshot/"02-studio-revision.png"),full_page=True)

                page.locator("#midi-result [data-pack-midi]").click()
                page.locator("#pack-form input[name=title]").fill("Browser Pack")
                page.locator("#pack-form button[type=submit]").click()
                page.locator("#asset-result [data-file='Browser_Pack.zip']").wait_for(timeout=30000)
                with page.expect_download() as download:
                    page.locator("#asset-result [data-save-run]").click()
                with ZipFile(download.value.path()) as archive:
                    assert json.loads(archive.read("Manifest.json"))["asset_count"]==4
                page.locator("#asset-result [data-release-pack]").click()
                page.locator("#release-form button[type=submit]").click()
                page.locator("#release-result [data-file='Shopify_Draft.csv']").wait_for(timeout=30000)
                assert "4 midi files" in page.locator("#release-result").inner_text()
                page.screenshot(path=str(screenshot/"03-release.png"),full_page=True)
                page.locator("nav button[data-view=assets]").click()
                wave=io.BytesIO(); sf.write(wave,.4*np.sin(2*np.pi*440*np.arange(48000)/48000),48000,format="WAV",subtype="PCM_24")
                page.locator("#import-files").set_input_files({"name":"Fixture_Loop.wav","mimeType":"audio/wav","buffer":wave.getvalue()})
                page.locator("#asset-list [data-analyze]").wait_for(timeout=30000)
                page.locator("#asset-list [data-analyze]").click()
                page.locator("#asset-result [data-file='Audio_Report.json']").wait_for(timeout=30000)
                page.locator("nav button[data-view=focus]").click()
                page.locator("#focus-form select[name=minutes]").select_option("60")
                page.locator("#focus-form button[type=submit]").click()
                page.locator("#focus-result .timer").wait_for(timeout=30000)
                assert page.locator("#focus-result .timer").inner_text()=="15:00"
                page.locator("#focus-result [data-action=timer]").click()
                assert page.locator("#focus-result [data-action=timer]").inner_text()=="Pause timer"
                page.locator("#focus-result [data-action=timer]").click()
                assert page.locator("#focus-result [data-action=timer]").inner_text()=="Resume focus timer"
                page.reload()
                page.wait_for_function("document.getElementById('connection-status').textContent.includes('ready')")
                page.locator("nav button[data-view=history]").click()
                assert page.locator("#history-list .history-row").count()==7
                page.locator("#history-list [data-run]").last.click()
                page.locator("#history-result [data-file='Melody.mid']").wait_for()
                page.set_viewport_size({"width":390,"height":844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Mobile horizontal overflow"
                page.screenshot(path=str(screenshot/"04-mobile-history.png"),full_page=True)
                assert not errors,errors
                assert page.locator("#error").is_hidden(), page.locator("#error").inner_text()

                # Drum-only output, nested state persistence and safe prompt display.
                page.locator("nav button[data-view=midi]").click()
                for track in ["Melody","Chords","Bass"]:
                    page.locator(f"#midi-form [name=track_{track}]").uncheck()
                page.locator("#midi-form [name=prompt]").fill("<script>écho 謎</script>")
                page.locator("#midi-form details summary").click()
                page.locator("#midi-form [name='settings.swing']").fill("60")
                previous_id=page.locator("#midi-result [data-output-id]").get_attribute("data-output-id")
                page.locator("#midi-form button[type=submit]").click()
                page.wait_for_function("document.querySelector('#midi-result [data-output-id]')?.dataset.outputId !== "+json.dumps(previous_id))
                page.locator("#busy").wait_for(state="hidden")
                assert page.locator("#midi-result [data-file='Drums.mid']").count()==1
                assert page.locator("#midi-result [data-file='Melody.mid']").count()==0
                assert "<script>écho 謎</script>" in page.locator("#midi-result").inner_text()
                page.reload()
                page.wait_for_function("document.getElementById('connection-status').textContent.includes('ready')")
                page.locator("nav button[data-view=midi]").click()
                assert not page.locator("#midi-form [name=track_Melody]").is_checked()
                assert page.locator("#midi-form [name='settings.swing']").input_value()=="60"
                page.evaluate("localStorage.setItem('sonic-inputs', '{broken')")
                page.reload()
                page.wait_for_function("document.getElementById('connection-status').textContent.includes('ready')")
                assert not errors,errors
                page.locator("nav button[data-view=midi]").click()
                page.locator("#midi-form [name=seed]").fill("12345")
                intercepted=[]
                def lose_completed_response(route):
                    response=route.fetch()
                    intercepted.append(response.json())
                    route.abort("failed")
                page.route(base+"/workbench/api/midi",lose_completed_response)
                page.locator("#midi-form button[type=submit]").click()
                page.locator("#error").wait_for(state="visible")
                page.locator("#busy").wait_for(state="hidden")
                assert intercepted[0]["status"]=="succeeded"
                pending=page.evaluate("JSON.parse(localStorage.getItem('sonic-pending-midi'))")
                assert pending["id"]==intercepted[0]["request"]["request_id"]
                page.unroute(base+"/workbench/api/midi",lose_completed_response)
                page.locator("#midi-form button[type=submit]").click()
                page.locator("#busy").wait_for(state="hidden")
                assert page.locator("#midi-result [data-output-id]").get_attribute("data-output-id")==intercepted[0]["id"]
                assert page.evaluate("localStorage.getItem('sonic-pending-midi')") is None
                assert page.locator("#error").is_hidden()

                # Five-part controls, separately downloadable counter-melody and pack inventory.
                page.locator("#midi-form [name=track_Countermelody]").check()
                previous_id=page.locator("#midi-result [data-output-id]").get_attribute("data-output-id")
                page.locator("#midi-form button[type=submit]").click()
                page.wait_for_function("document.querySelector('#midi-result [data-output-id]')?.dataset.outputId !== "+json.dumps(previous_id))
                page.locator("#busy").wait_for(state="hidden")
                page.locator("#midi-result [data-file='Countermelody.mid']").wait_for()
                with page.expect_download() as download:
                    page.locator("#midi-result [data-file='Countermelody.mid']").click()
                counter=mido.MidiFile(download.value.path())
                assert any(m.type=="note_on" and m.channel==3 for t in counter.tracks for m in t)
                page.locator("#midi-result [data-pack-midi]").click()
                page.locator("#pack-form input[name=title]").fill("Five Part Pack")
                page.locator("#pack-form button[type=submit]").click()
                page.locator("#asset-result [data-file='Five_Part_Pack.zip']").wait_for()
                with page.expect_download() as download:
                    page.locator("#asset-result [data-save-run]").click()
                with ZipFile(download.value.path()) as archive:
                    assert json.loads(archive.read("Manifest.json"))["asset_count"]==5
                    assert "MIDI/Countermelody.mid" in archive.namelist()
                assert not errors,errors
                assert page.locator("#error").is_hidden(),page.locator("#error").inner_text()
                browser.close()
                proof={"passed":True,"checks":["automatic_token_bootstrap","generate_button","piano_roll","audition_decoding_playback","midi_download_parse","pack_zip_manifest","release_csv","audio_upload_analysis","energy_bounded_focus_timer","persisted_history_after_reload","mobile_no_overflow","zero_browser_exceptions","studio_prompt_apply","studio_revision_lineage","studio_reuse_settings","studio_drum_only","nested_form_persistence","unicode_prompt_escaping","corrupt_storage_recovery","lost_response_idempotent_retry","five_part_counter_download","five_part_pack_inventory"],"screenshots":str(screenshot)}
                print(json.dumps(proof,indent=2))
        finally:
            process.terminate()
            process.wait(timeout=10)


if __name__=="__main__":
    main()
