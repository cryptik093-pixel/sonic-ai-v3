from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import assets, chat, memory, projects, uploads, intelligence


app = FastAPI(
    title="Sonic AI API",
    version="0.3.0",
    description="Sonic AI V3 — Producer Operating System API",
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


@app.get("/")
def root():
    return {
        "message": "Sonic AI API",
        "version": "0.3.0",
    }


@app.get("/health")
def health():
    return {
        "healthy": True,
    }


@app.get("/dashboard")
def dashboard():
    from ..repositories.chat_repository import chat_store
    from ..repositories.project_repository import project_store
    from ..services.asset_service import asset_service

    return {
        "projects": len(project_store.list_projects()),
        "assets": len(asset_service.list_assets()),
        "ai_jobs": len(chat_store.list_sessions()),
        "status": "Backend Online",
    }
