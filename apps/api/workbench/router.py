import hmac
import os
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from starlette.datastructures import Headers
from starlette.responses import JSONResponse

from ..config import Settings
from . import service
from .schemas import AnalyzeCommand, CoachCommand, FocusCommand, MidiCommand, PackCommand, ReleaseCommand

router = APIRouter(prefix="/workbench/api", tags=["Production Workbench"])


class WorkbenchAuth:
    """The desktop is a single local operator; never silently expose its files on a network."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path = scope.get("path", "")
        desktop = os.getenv("SONIC_DESKTOP_MODE") == "1"
        protected = path.startswith("/workbench/api") or (desktop and not (path in {"/health", "/workbench", "/workbench/"} or path.startswith("/workbench/static/")))
        if not protected or path == "/mcp" or path.startswith("/integrations"):
            return await self.app(scope, receive, send)
        token = os.getenv("SONIC_DESKTOP_TOKEN") or os.getenv("SONIC_CONTROL_PLANE_TOKEN", "")
        if not token:
            return await JSONResponse({"detail": "Start Sonic Desktop to initialize the local connection."}, 503)(scope, receive, send)
        headers = Headers(scope=scope)
        provided = headers.get("authorization", "")
        if not hmac.compare_digest(provided.encode(), f"Bearer {token}".encode()):
            return await JSONResponse({"detail": "Sonic connection expired. Reopen the desktop app."}, 401)(scope, receive, send)
        host = headers.get("host", "").split(":")[0]
        if host not in {"localhost", "127.0.0.1", "testserver"}:
            return await JSONResponse({"detail": "Desktop access is local only."}, 403)(scope, receive, send)
        origin = headers.get("origin")
        if origin and origin not in {f"http://{headers.get('host')}", "http://localhost:3000", "http://127.0.0.1:3000"}:
            return await JSONResponse({"detail": "Origin is not allowed."}, 403)(scope, receive, send)
        await self.app(scope, receive, send)


def call(fn, payload):
    try:
        return fn(payload)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None


@router.get("/status")
def status():
    configured = bool(Settings.from_env().openai_api_key)
    return {"version": "0.5.0", "owner_id": service.OWNER, "workspace_id": service.WORKSPACE,
            "local_engine": "ready", "cloud_ai": "configured_not_verified" if configured else "not_configured",
            "capabilities": ["midi", "analysis", "pack", "release", "focus", "coach"],
            "mcp_url": "http://127.0.0.1:8000/mcp", "runs": service.list_runs(), "assets": service.list_assets()}


@router.get("/runs/{run_id}")
def get_run(run_id: UUID):
    return call(service.get_run, run_id)


@router.get("/runs/{run_id}/files/{filename}")
def download(run_id: UUID, filename: str):
    try:
        path = service.artifact_path(run_id, filename)
        return FileResponse(path, filename=path.name)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from None


@router.post("/imports")
def import_asset(file: UploadFile = File(...)):
    try:
        return service.import_asset(file.filename or "upload", file.file)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    finally:
        file.file.close()


@router.get("/runs/{run_id}/archive")
def archive(run_id: UUID):
    try:
        run = service.get_run(run_id)
        if run["status"] != "succeeded":
            raise ValueError("This run has not completed.")
        if run["kind"] == "pack":
            name = next(f["name"] for f in run["result"]["artifacts"] if f["name"].endswith(".zip"))
            return FileResponse(service.artifact_path(run_id, name), filename=name)
        output = tempfile.SpooledTemporaryFile(max_size=8*1024*1024)
        try:
            with ZipFile(output, "w", ZIP_DEFLATED) as z:
                for artifact in run["result"].get("artifacts", []):
                    z.write(service.artifact_path(run_id, artifact["name"]), artifact["name"])
            output.seek(0)
        except Exception:
            output.close()
            raise
        def chunks():
            try:
                while block := output.read(65536):
                    yield block
            finally:
                output.close()
        return StreamingResponse(chunks(), media_type="application/zip", headers={"Content-Disposition": 'attachment; filename="Sonic_Output.zip"'})
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from None


@router.post("/midi")
def generate_midi(payload: MidiCommand):
    return call(service.generate_midi, payload)


@router.post("/analysis")
def analyze(payload: AnalyzeCommand):
    return call(service.analyze_audio, payload)


@router.post("/pack")
def pack(payload: PackCommand):
    return call(service.build_pack, payload)


@router.post("/release")
def release(payload: ReleaseCommand):
    return call(service.release_draft, payload)


@router.post("/focus")
def focus(payload: FocusCommand):
    return call(service.focus_session, payload)


@router.post("/coach")
def coach(payload: CoachCommand):
    return call(service.coach, payload)
