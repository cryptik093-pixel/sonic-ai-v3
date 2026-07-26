from fastapi import FastAPI

from routers import projects
from routers import assets


app = FastAPI(
    title="Sonic AI API",
    version="0.1.0"
)


# Routers
app.include_router(projects.router)
app.include_router(assets.router)


@app.get("/")
def root():
    return {
        "message": "Sonic AI API"
    }


@app.get("/health")
def health():
    return {
        "healthy": True
    }


@app.get("/dashboard")
def dashboard():
    return {
        "projects": 12,
        "assets": 1284,
        "ai_jobs": 4,
        "status": "Backend Online"
    }