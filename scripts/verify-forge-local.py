"""Reproducible disposable local Forge HTTP smoke; no provider/network mutations.

Run with the API environment: python scripts/verify-forge-local.py
Keeps synthetic fixtures, private local database and JSON evidence in output/forge.
Use --serve for a browser walkthrough, Ctrl+C to stop that disposable server.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4
import wave
import zipfile

import httpx

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "forge"
BASE = "http://127.0.0.1:18765"
API = BASE + "/workbench/api/forge"
# Disposable test credential, never a real operator secret or provider token.
AUTH = {"Authorization": "Bearer forge-disposable-smoke"}


def fixture():
    stream = io.BytesIO()
    with wave.open(stream, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\0\0" * 800)
    path = OUT / "synthetic-pack.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("Synthetic/Drums/kick.wav", stream.getvalue())
        archive.writestr("Synthetic/LICENSE.txt", "Synthetic smoke fixture; generated locally. No commercial sound claims.")
    return path


def smoke(client, source):
    raw = source.read_bytes()
    def checked(response):
        response.raise_for_status()
        return response.json()
    pack = checked(client.post(API + "/packs", params={"title": "Forge synthetic smoke", "taxonomy": "test / drums", "request_id": str(uuid4())}, content=raw, headers={"Content-Type": "application/zip"}))
    def command(action, extra=None):
        response = client.request("PATCH" if action == "review" else "POST", API + f"/packs/{pack['id']}/{action}", json={
            "request_id": str(uuid4()), "expected_revision": pack["manifest_revision"], **(extra or {})})
        return checked(response)
    pack = command("review", {"updates": {a["asset_id"]: {"rights_state": "cleared", "proposed_path": "REVIEWED/" + a["original_path"]} for a in pack["manifest"]["assets"]}})
    pack = command("approve")
    result = command("export")
    artifact = result["artifact"]
    response = client.get(API + "/exports/" + artifact["id"])
    response.raise_for_status()
    exported = response.content
    assert hashlib.sha256(exported).hexdigest() == artifact["sha256"]
    with zipfile.ZipFile(io.BytesIO(exported)) as archive, zipfile.ZipFile(source) as original:
        manifest = json.loads(archive.read("manifest.json"))
        for asset in manifest["assets"]:
            assert archive.read(asset["proposed_path"]) == original.read(asset["original_path"])
    assert source.read_bytes() == raw
    assert httpx.get(API + "/exports/" + artifact["id"]).status_code == 401
    (OUT / "reviewed-pack.zip").write_bytes(exported)
    evidence = {"base": BASE, "pack_id": pack["id"], "manifest_revision": pack["manifest_revision"],
        "source_sha256": hashlib.sha256(raw).hexdigest(), "export_sha256": artifact["sha256"],
        "asset_count": len(pack["manifest"]["assets"]), "byte_roundtrip": "passed", "anonymous_download": "rejected",
        "fixture": "locally generated synthetic WAV and text only", "musical_estimation": "not_measured"}
    (OUT / "http-smoke.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    for key in list(env):
        if key.startswith(("SONIC_OAUTH", "SONIC_SHOPIFY", "SONIC_OPENAI")) or key in {"OPENAI_API_KEY", "SONIC_PUBLIC_MCP_URL", "SONIC_DESKTOP_MODE", "SONIC_DESKTOP_TOKEN"}:
            env.pop(key, None)
    env.update(PYTHON_DOTENV_DISABLED="1", SONIC_DB_PATH=str(OUT / "app.db"),
        SONIC_EVENT_DB=str(OUT / "events.db"), SONIC_DATA_DIR=str(OUT),
        SONIC_CONTROL_PLANE_TOKEN="forge-disposable-smoke")
    # Refuse to reuse an unrelated listener or mutate its database.
    import socket
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 18765))
    with (OUT / "server.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen([sys.executable, "-m", "uvicorn", "apps.api.main:app", "--host", "127.0.0.1", "--port", "18765"], cwd=ROOT, env=env, stdout=log, stderr=log)
        try:
            with httpx.Client(headers=AUTH, timeout=30, trust_env=False) as client:
                deadline = time.monotonic() + 60
                while True:
                    try:
                        if client.get(BASE + "/health").status_code == 200:
                            break
                    except httpx.ConnectError:
                        pass
                    if process.poll() is not None or time.monotonic() >= deadline:
                        raise RuntimeError("Disposable API did not become ready; inspect output/forge/server.log")
                    time.sleep(0.25)
                smoke(client, fixture())
            if args.serve:
                print("Disposable browser smoke server ready at " + BASE + "/workbench", flush=True)
                while process.poll() is None:
                    time.sleep(1)
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    main()
