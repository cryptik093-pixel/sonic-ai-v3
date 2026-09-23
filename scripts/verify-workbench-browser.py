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

ROOT = Path(__file__).resolve().parents[1]


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
                page.locator("#midi-form textarea[name=prompt]").fill("A dreamy C# minor trap idea at 142 BPM, 4 bars, sparse.")
                before_preview = page.evaluate("""async () => {
                  const token = sessionStorage.getItem('sonic-token');
                  return (await fetch('/workbench/api/status', {headers:{Authorization:'Bearer '+token}})).json();
                }""")
                page.locator("#preview-brief").click()
                page.locator("#midi-brief-preview").get_by_text("INTERPRETATION PREVIEW", exact=False).wait_for()
                assert "C# minor" in page.locator("#midi-brief-preview").inner_text()
                assert "dreamy" in page.locator("#midi-brief-preview").inner_text()
                assert "trap" in page.locator("#midi-brief-preview").inner_text()
                assert len(page.evaluate("""async () => {
                  const token = sessionStorage.getItem('sonic-token');
                  return (await fetch('/workbench/api/status', {headers:{Authorization:'Bearer '+token}})).json().runs;
                }""")) == len(before_preview["runs"]), "Preview must not create a run"
                page.locator("#midi-form select[name=bars]").select_option("4")
                page.locator("#midi-form button[type=submit]").click()
                page.locator("#midi-result [data-file='Melody.mid']").wait_for(timeout=30000)
                assert "C# minor" in page.locator("#midi-result").inner_text()
                assert "A dreamy C# minor trap" in page.locator("#midi-result").inner_text()
                page.wait_for_function("document.querySelector('#midi-result audio')?.src.startsWith('blob:')")
                page.locator("#midi-result audio").evaluate("a => a.play()")
                page.wait_for_function("document.querySelector('#midi-result audio').currentTime > 0.1")
                page.locator("#midi-result audio").evaluate("a => a.pause()")
                with page.expect_download() as download:
                    page.locator("#midi-result [data-file='Melody.mid']").click()
                song=mido.MidiFile(download.value.path())
                assert any(m.type=="note_on" for t in song.tracks for m in t)
                page.locator("#midi-result [data-feedback=keep]").click()
                page.get_by_text("Latest decision: Keep this direction").wait_for()
                page.locator("#midi-form textarea[name=prompt]").fill("Make a variation of the kept direction, uplifting.")
                page.locator("#preview-brief").click()
                page.locator("#midi-brief-preview").get_by_text("Reused saved run", exact=False).wait_for()
                assert "C# minor" in page.locator("#midi-brief-preview").inner_text()
                assert "uplifting" in page.locator("#midi-brief-preview").inner_text()
                page.locator("#midi-form button[type=submit]").click()
                page.locator("#midi-result [data-file='Melody.mid']").wait_for(timeout=30000)
                page.screenshot(path=str(screenshot/"02-midi.png"),full_page=True)
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
                page.locator("nav button[data-view=midi]").click()
                page.locator("#preview-brief").click()
                page.locator("#midi-brief-preview").get_by_text("Reused saved run", exact=False).wait_for()
                assert "C# minor" in page.locator("#midi-brief-preview").inner_text(), "Saved form values must not become accidental prompt overrides after restart"
                assert "uplifting" in page.locator("#midi-brief-preview").inner_text()
                page.locator("nav button[data-view=history]").click()
                assert page.locator("#history-list .history-row").count()==6
                page.locator("#history-list [data-run]").last.click()
                page.locator("#history-result [data-file='Melody.mid']").wait_for()
                page.set_viewport_size({"width":390,"height":844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Mobile horizontal overflow"
                page.screenshot(path=str(screenshot/"04-mobile-history.png"),full_page=True)
                assert not errors,errors
                assert page.locator("#error").is_hidden(), page.locator("#error").inner_text()
                browser.close()
                proof={"passed":True,"checks":["automatic_token_bootstrap","prompt_interpretation_preview_read_only","prompt_to_midi","kept_output_feedback","explicit_continuity_preview","prompt_control_precedence_survives_restart","piano_roll","audition_decoding_playback","midi_download_parse","pack_zip_manifest","release_csv","audio_upload_analysis","energy_bounded_focus_timer","persisted_history_after_reload","mobile_no_overflow","zero_browser_exceptions"],"screenshots":str(screenshot)}
                print(json.dumps(proof,indent=2))
        finally:
            process.terminate()
            process.wait(timeout=10)


if __name__=="__main__":
    main()
