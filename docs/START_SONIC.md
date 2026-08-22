Developer Startup — Sonic AI V3

This file documents repeatable developer commands to start, test, build, and reset the local Sonic development environment.

Prerequisites
- Python 3.11+ (Windows: use virtualenv or the included `venv`)
- Node.js + pnpm for the frontend
- (Optional) `SONIC_OPENAI_API_KEY` environment variable to enable LLM functionality

Start the backend (development):

```powershell
cd apps/api
# Activate venv if present
.\.venv\Scripts\Activate.ps1  # PowerShell
python -m uvicorn main:app --reload --port 8000
```

Start the frontend (development):

```bash
cd apps/web
pnpm install
pnpm dev
# Open http://localhost:3000
```

Run backend tests:

```powershell
cd "c:/Users/david someone/Desktop/SONIC AI V3/sonic-ai-v3"
python -m pytest apps/api/tests -q
```

Reset local SQLite DB (wipe data):

```powershell
cd apps/api
python -c "from database import DB_PATH; import os; os.remove(DB_PATH) if DB_PATH.exists() else None; print('DB removed')"
# Restart the API (it will recreate tables)
```

Health checks:
- API health: `http://127.0.0.1:8000/health`
- Dashboard summary: `http://127.0.0.1:8000/dashboard`

Run backend+frontend together (recommended):

```bash
# From repository root
pnpm run dev:all
# or on Windows PowerShell
.\dev.ps1
```

Notes:
- The API uses `apps/api/.env` for optional configuration (OpenAI key, model, base URL). See `apps/api/.env.example`.
- If you want the frontend to talk to a different host/port, update `apps/web/services/api.ts`.

If you'd like, I can also add a single `dev` script at the repository root that simultaneously starts backend and frontend using `concurrently` or `pnpm` tasks.