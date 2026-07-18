from fastapi import FastAPI

from routers.projects import router as projects_router

app = FastAPI(title="Sonic AI API")

app.include_router(projects_router)


@app.get("/")
def root():
    return {"message": "Sonic AI API"}


@app.get("/health")
def health():
    return {"healthy": True}


@app.get("/dashboard")
def dashboard():
    return {
        "projects": 12,
        "assets": 1284,
        "ai_jobs": 4,
        "status": "Backend Online",
    }