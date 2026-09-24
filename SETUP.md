# Folio — Setup (Phase 1)

Two apps: **folio-backend** (FastAPI → Render) and **folio-frontend** (Next.js → Vercel),
sharing one Supabase project (Auth + Postgres). Do this once.

---

## 1. Create the Supabase project
1. https://supabase.com → New project. Pick a region close to you.
2. Wait for it to finish provisioning.

## 2. Run the database migrations
Supabase Dashboard → **SQL Editor** → run these files **in order** (paste each, Run):
1. `folio-backend/migrations/0001_initial_schema.sql`
2. `folio-backend/migrations/0002_rls_policies.sql`
3. `folio-backend/migrations/0003_reserved_usernames_seed.sql`

Verify: **Table editor** should show `profiles`, `portfolios`, `portfolio_profiles`,
`username_history`, `reserved_usernames`, and RLS enabled (shield icon) on each.

## 3. Configure Supabase Auth
Dashboard → **Authentication → Providers → Email**: enable Email.
- Keep **"Confirm email"** ON (Phase 1 uses Supabase's email verification).
- **Authentication → URL Configuration**:
  - Site URL: `http://localhost:3000` (dev) — update to your Vercel URL in prod.
  - Redirect URLs: add `http://localhost:3000/auth/callback` and your prod `.../auth/callback`.

## 4. Collect the keys
Dashboard → **Project Settings → API**:
- `SUPABASE_URL`  = Project URL
- `SUPABASE_ANON_KEY` = anon public key
- `SUPABASE_SERVICE_ROLE_KEY` = service_role key (**server only**, never in the browser)
- `SUPABASE_JWT_SECRET` = JWT Settings → JWT Secret

Dashboard → **Project Settings → Database → Connection string → "Connection pooling"**
(Transaction mode, port 6543). Copy it as `DATABASE_URL`.

---

## 5. Backend env  (`folio-backend/.env`)
```
APP_ENV=development
APP_URL=http://localhost:3000
PUBLIC_PORTFOLIO_URL=http://localhost:3000
API_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000

SUPABASE_URL=https://YOUR_REF.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_JWT_SECRET=...
SUPABASE_SERVICE_ROLE_KEY=...

DATABASE_URL=postgresql://postgres.YOUR_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres
DB_SSL=true
```

## 6. Frontend env  (`folio-frontend/.env.local`)
```
NEXT_PUBLIC_SUPABASE_URL=https://YOUR_REF.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```
> Only the **anon** key goes in the frontend. Service role / JWT secret / DB URL stay backend-only.

---

## 7. Run both locally
Terminal A (backend):
```bash
cd folio-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Terminal B (frontend):
```bash
cd folio-frontend
npm install
npm run dev
```
Open http://localhost:3000 → Register → check email → confirm → land on `/dashboard`.

### Smoke test
- `GET http://localhost:8000/api/v1/health` → `{"status":"ok"}`
- `GET http://localhost:8000/api/v1/health/db` → `{"status":"ok","db":"ok"}` (confirms DB + pooler)
- Register a user → a `profiles` row + a draft `portfolios` row appear automatically.
- In the dashboard: pick a username, edit profile, hit Publish.

---

## 8. Deploy
### Backend → Render
- New **Web Service**, connect the repo, root dir `folio-backend` (or use `render.yaml`).
- Build: `pip install -r requirements.txt`  ·  Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Add all backend env vars. Set `APP_ENV=production`, `CORS_ORIGINS=https://your-vercel-app.vercel.app`,
  and the three URL vars to the deployed URLs. Health check path: `/api/v1/health`.

### Frontend → Vercel
- Import the repo, root dir `folio-frontend`.
- Add the `NEXT_PUBLIC_*` env vars; set `NEXT_PUBLIC_API_URL` to the Render URL.
- After deploy, update Supabase Auth **Site URL** + **Redirect URLs** to the Vercel domain.

---

## Notes / gotchas
- **pgbouncer transaction pooler**: the engine already sets `NullPool` + disables the asyncpg
  statement cache + uses unique prepared-statement names. Use the **pooler** string (6543), not the
  direct 5432 one, on Render.
- **Backend bypasses RLS** (it connects with the pooler role), so ownership is enforced in the
  service layer. RLS protects any direct `@supabase/supabase-js` table access from the browser.
- If email confirmation links point at the wrong host, fix Supabase Auth URL Configuration.
