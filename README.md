# Folio API (backend)

FastAPI + async SQLAlchemy + Supabase (Auth + Postgres) — Phase 1: Foundation.

## Run locally
```bash
cd folio-backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # then fill in the values (see ../SETUP.md)
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs

## Key endpoints (all under `/api/v1`)
| Method | Path                | Auth | Purpose                                  |
|--------|---------------------|------|------------------------------------------|
| GET    | `/health`           | no   | liveness                                 |
| GET    | `/health/db`        | no   | DB connectivity                          |
| GET    | `/me`               | yes  | account identity (profiles row)          |
| GET    | `/portfolio`        | yes  | current user's primary portfolio         |
| PATCH  | `/portfolio/profile`| yes  | update universal profile section         |
| PUT    | `/portfolio/username`| yes | set/change username (validated + cooldown)|
| PATCH  | `/portfolio/status` | yes  | draft / published / unpublished          |
| GET    | `/username/check`   | yes  | availability + suggestions               |

Auth = send `Authorization: Bearer <supabase access token>`.

## Deploy (Render) — the two things people miss
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`  (or `python start.py`). Never `--reload`, never a hardcoded port — Render needs `0.0.0.0:$PORT`.
- **Env vars:** set every var from `.env.example` in the Render dashboard (including `PYTHON_VERSION=3.12.7` and `DATABASE_URL`). Missing `DATABASE_URL` crashes boot.

Full setup (Supabase project, SQL migrations, env for both apps): see **SETUP.md**.
