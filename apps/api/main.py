from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.routing import Route
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .workbench.router import router as workbench_router, WorkbenchAuth
from .workbench.service import recover_interrupted
from .events_router import router as events_router
from .shopify_webhooks import router as shopify_webhooks_router

from .integrations.auth import ControlPlaneAuth
from .integrations.config import ControlConfig
from .integrations.gateway import build_mcp, router as integrations_router
from .integrations.service import ControlPlane
from .integrations.store import EventStore
from .integrations.webhooks import router as webhook_router

from .routers import assets, chat, memory, projects, uploads, intelligence
from .version import APP_VERSION


@asynccontextmanager
async def lifespan(app):
    recover_interrupted()
    config = ControlConfig.from_env()
    app.state.control_plane = ControlPlane(config, EventStore(config.event_db), api_serving=True)
    mcp = build_mcp(lambda: app.state.control_plane)
    app.state.mcp_app = mcp.streamable_http_app()
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="Sonic AI API",
    version=APP_VERSION,
    description="Sonic AI V3 — Producer Operating System API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(assets.router)
app.include_router(uploads.router)
app.include_router(chat.router)
app.include_router(memory.router)
app.include_router(intelligence.router)
app.include_router(integrations_router)
app.include_router(webhook_router)
app.include_router(events_router)
app.include_router(shopify_webhooks_router)
app.include_router(workbench_router)
app.add_middleware(ControlPlaneAuth)
app.add_middleware(WorkbenchAuth)

WORKBENCH_STATIC = Path(__file__).resolve().parent / "workbench" / "static"
app.mount("/workbench/static", StaticFiles(directory=WORKBENCH_STATIC, check_dir=False), name="workbench_static")


@app.get("/workbench", include_in_schema=False)
@app.get("/workbench/", include_in_schema=False)
def production_workbench():
    return FileResponse(WORKBENCH_STATIC / "index.html", headers={"Cache-Control": "no-store"})


@app.get("/")
def root():
    return {
        "message": "Sonic AI API",
        "version": APP_VERSION,
    }


@app.get("/health")
def health():
    return {
        "healthy": True,
    }


@app.get("/.well-known/oauth-protected-resource/mcp")
def mcp_resource_metadata():
    config = ControlConfig.from_env()
    if not config.oauth_configured:
        raise HTTPException(404, "OAuth resource not configured")
    return {"resource": config.public_mcp_url, "authorization_servers": [config.oauth_issuer],
            "scopes_supported": ["sonic:read", "sonic:check"], "bearer_methods_supported": ["header"]}


@app.get("/dashboard")
def dashboard():
    from .repositories.chat_repository import chat_store
    from .repositories.project_repository import project_store
    from .services.asset_service import asset_service

    return {
        "projects": len(project_store.list_projects()),
        "assets": len(asset_service.list_assets()),
        "ai_jobs": len(chat_store.list_sessions()),
        "status": "Backend Online",
    }


class MCPGateway:
    async def __call__(self, scope, receive, send):
        await app.state.mcp_app(scope, receive, send)


# An exact ASGI route preserves FastAPI's existing trailing-slash redirects.
app.router.routes.append(Route("/mcp", endpoint=MCPGateway()))
