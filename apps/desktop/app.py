"""Native window, supervised API lifecycle, OS credential storage and file dialogs."""
import argparse
import json
import logging
import os
import secrets
import shutil
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path
from uuid import UUID


def data_directory():
    if os.getenv("SONIC_DATA_DIR"):
        return Path(os.environ["SONIC_DATA_DIR"]).resolve()
    if sys.platform == "win32":
        return Path(os.getenv("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "OmegaHouse" / "Sonic"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "OmegaHouse" / "Sonic"
    return Path(os.getenv("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / "omega-house" / "sonic"


def configure(directory):
    directory.mkdir(parents=True, exist_ok=True)
    os.environ["SONIC_DATA_DIR"] = str(directory)
    os.environ["SONIC_DB_PATH"] = str(directory / "sonic_ai.db")
    os.environ["SONIC_EVENT_DB"] = str(directory / "events.db")
    os.environ["SONIC_DESKTOP_MODE"] = "1"
    token_file = directory / "mcp-token"
    if not token_file.exists():
        # Exclusive creation: two launches cannot replace each other's credentials.
        try:
            fd = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(secrets.token_urlsafe(36))
        except FileExistsError:
            pass
    os.environ["SONIC_CONTROL_PLANE_TOKEN"] = token_file.read_text().strip()
    os.environ["SONIC_DESKTOP_TOKEN"] = secrets.token_urlsafe(36)
    try:
        import keyring
        key = keyring.get_password("OmegaHouse.Sonic", "openai_api_key")
        if key:
            os.environ["SONIC_OPENAI_API_KEY"] = key
    except Exception:
        pass  # Local composition/analysis remains usable without a keychain.
    settings = directory / "preferences.json"
    if settings.exists():
        try:
            model = json.loads(settings.read_text()).get("model")
            if isinstance(model, str) and model:
                os.environ["SONIC_OPENAI_MODEL"] = model
        except (ValueError, OSError):
            pass


class DesktopBridge:
    def __init__(self, directory, base):
        self._directory, self._base, self._window = directory, base, None

    def _choose_folder(self):
        import webview
        result = self._window.create_file_dialog(webview.FileDialog.FOLDER)
        return Path(result[0]) if result else None

    def save_artifact(self, run_id, filename):
        from apps.api.workbench.service import artifact_path
        try:
            source = artifact_path(str(UUID(run_id)), filename)
            destination = self._choose_folder()
            if destination is None:
                return {"cancelled": True}
            target = destination / source.name
            # Never silently overwrite an existing user file.
            index = 1
            while target.exists():
                target = destination / f"{source.stem}_{index}{source.suffix}"
                index += 1
            with target.open("xb") as out, source.open("rb") as inp:
                shutil.copyfileobj(inp, out)
            return {"saved": True}
        except (ValueError, OSError):
            return {"error": "Could not export the file. Choose a writable folder and try again."}

    def save_run(self, run_id):
        from apps.api.workbench.service import artifact_path, get_run
        from apps.api.workbench.midi import slug
        try:
            run = get_run(str(UUID(run_id)))
            if run["status"] != "succeeded":
                return {"error": "This run has not completed."}
            destination = self._choose_folder()
            if destination is None:
                return {"cancelled": True}
            target = destination / f"{slug(run['result']['title'])}_{run['id'][:8]}"
            index = 1
            while target.exists():
                target = destination / f"{slug(run['result']['title'])}_{run['id'][:8]}_{index}"
                index += 1
            target.mkdir()
            for artifact in run["result"].get("artifacts", []):
                shutil.copy2(artifact_path(run_id, artifact["name"]), target / artifact["name"])
            return {"saved": True}
        except (ValueError, OSError):
            return {"error": "Export could not finish. Original outputs remain saved in Sonic; choose another folder and retry."}

    def configure_ai(self, api_key, model):
        if not isinstance(api_key, str) or not 10 <= len(api_key) <= 300 or any(c.isspace() for c in api_key):
            return {"error": "Enter a valid API key without spaces."}
        if not isinstance(model, str) or not model.strip() or len(model) > 100 or any(c.isspace() for c in model):
            return {"error": "Enter a model ID, such as gpt-4o."}
        os.environ["SONIC_OPENAI_API_KEY"] = api_key
        os.environ["SONIC_OPENAI_MODEL"] = model
        message = "AI configured for this session; use Get a grounded insight on an output to verify it."
        try:
            import keyring
            keyring.set_password("OmegaHouse.Sonic", "openai_api_key", api_key)
            (self._directory / "preferences.json").write_text(json.dumps({"model": model}), encoding="utf-8")
            message = "AI credential saved in the OS credential store; use Get a grounded insight on an output to verify it."
        except Exception:
            message += " The OS credential store was unavailable, so the key was not saved to disk."
        return {"message": message}

    def save_mcp_config(self):
        try:
            destination = self._choose_folder()
            if destination is None:
                return {"cancelled": True}
            payload = {"mcpServers": {"sonic": {"url": self._base + "/mcp",
                        "headers": {"Authorization": "Bearer " + os.environ["SONIC_CONTROL_PLANE_TOKEN"]}}}}
            target = destination / "sonic-mcp.private.json"
            fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            return {"saved": True}
        except OSError:
            return {"error": "The private connection file already exists or the folder is not writable. Choose another folder."}


def smoke_test(base, output):
    """Exercise the packaged executable's actual HTTP/file boundary without requiring a display."""
    import io
    import httpx
    import mido
    from zipfile import ZipFile
    headers = {"Authorization": "Bearer " + os.environ["SONIC_DESKTOP_TOKEN"]}
    with httpx.Client(base_url=base, headers=headers, timeout=60, trust_env=False) as client:
        assert client.get("/workbench").status_code == 200
        assert client.get("/workbench/static/app.js").status_code == 200
        assert client.get("/workbench/api/status").json()["local_engine"] == "ready"
        response = client.post("/workbench/api/midi", json={"title": "Packaged smoke", "bars":4})
        response.raise_for_status()
        run = response.json()
        assert run["status"] == "succeeded", run.get("error")
        data = client.get(f"/workbench/api/runs/{run['id']}/files/Melody.mid").content
        song = mido.MidiFile(file=io.BytesIO(data))
        assert sum(m.type == "note_on" for t in song.tracks for m in t) > 0
        archive = client.get(f"/workbench/api/runs/{run['id']}/archive")
        assert "Melody.mid" in ZipFile(io.BytesIO(archive.content)).namelist()
        unauthorized = httpx.get(base + "/workbench/api/status", trust_env=False)
        assert unauthorized.status_code == 401
        output.write_text(json.dumps({"passed": True, "run_id": run["id"], "artifacts": len(run["result"]["artifacts"]),
                                      "checks": ["packaged_http_boot", "bundled_ui_assets", "midi_parse", "download_zip", "authorization"]}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-test", type=Path)
    parser.add_argument("--ui-smoke-test", type=Path)
    args = parser.parse_args()
    temporary = tempfile.TemporaryDirectory(prefix="sonic-desktop-smoke-") if args.smoke_test or args.ui_smoke_test else None
    directory = Path(temporary.name) if temporary else data_directory()
    configure(directory)
    # One process owns this workspace; a second launch must not interrupt live jobs.
    instance_lock = (directory / "instance.lock").open("a+b")
    instance_lock.seek(0)
    if instance_lock.read(1) == b"":
        instance_lock.write(b"0")
        instance_lock.flush()
    instance_lock.seek(0)
    try:
        if sys.platform == "win32":
            import msvcrt
            msvcrt.locking(instance_lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(instance_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        instance_lock.close()
        raise RuntimeError("Sonic is already running. Open its existing window.") from None
    logging.basicConfig(filename=directory / "sonic.log", level=logging.WARNING,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    # Static import lets PyInstaller discover the complete shared API and its models.
    from apps.api.main import app
    import uvicorn
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", 0 if temporary else 8000))
    except OSError:
        sock.bind(("127.0.0.1", 0))
    sock.listen(128)
    port = sock.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_config=None, access_log=False, loop="asyncio", http="h11", ws="none"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    deadline = time.monotonic() + 30
    try:
        while not server.started:
            if not thread.is_alive() or time.monotonic() > deadline:
                raise RuntimeError("Sonic's local engine could not start. See sonic.log in your Sonic data folder.")
            time.sleep(.05)
        if args.smoke_test:
            smoke_test(base, args.smoke_test)
            return
        import webview
        bridge = DesktopBridge(directory, base)
        url = base + "/workbench#token=" + os.environ["SONIC_DESKTOP_TOKEN"]
        window = webview.create_window("Sonic — Omega House Production Workbench", url=url, js_api=bridge,
                                      width=1320, height=900, min_size=(900, 650), background_color="#101214")
        bridge._window = window
        ui_error = []
        def verify_ui():
            try:
                until = time.monotonic()+40
                while not window.evaluate_js("document.getElementById('connection-status')?.textContent.includes('ready')"):
                    if time.monotonic() > until:
                        raise RuntimeError("Native window did not connect to its engine.")
                    time.sleep(.2)
                window.evaluate_js("document.querySelector('button[data-view=midi]').click(); document.getElementById('midi-form').requestSubmit();")
                until = time.monotonic()+60
                while not window.evaluate_js("!!document.querySelector('#midi-result audio[src]')"):
                    if time.monotonic() > until:
                        raise RuntimeError("Native UI MIDI generation did not finish.")
                    time.sleep(.2)
                args.ui_smoke_test.write_text(json.dumps({"passed":True,"checks":["native_window_boot","automatic_connection","generate_button","audition_audio_loaded"]},indent=2))
            except Exception as exc:
                ui_error.append(str(exc))
                args.ui_smoke_test.write_text(json.dumps({"passed":False,"error":str(exc)}))
            finally:
                window.destroy()
        if args.ui_smoke_test:
            window.events.loaded += verify_ui
        webview.start(gui="edgechromium" if sys.platform == "win32" else None, debug=False)
        if ui_error:
            raise RuntimeError(ui_error[0])
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        sock.close()
        instance_lock.close()
        if temporary:
            from apps.api.database import engine
            engine.dispose()
            logging.shutdown()  # Windows cannot remove an open log file.
            temporary.cleanup()


if __name__ == "__main__":
    main()
