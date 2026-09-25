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
- `GET https://<render-url>/api/v1/health` → `{"status":"ok"}` (app up, port bound)
- `GET https://<render-url>/api/v1/health/db` → `{"status":"ok","db":"ok"}` (DB + pooler)
- `GET https://<render-url>/api/v1/health/status` → **one-glance diagnostics**: database
  reachable, all 5 tables present, reserved usernames seeded, auth configured. Open it in a
  browser (mobile is fine) to see exactly what's still missing — it leaks no secrets or data.
- Register a user → a `profiles` row + a draft `portfolios` row appear automatically.
- In the dashboard: pick a username, edit profile, hit Publish.

---

## 8. Deploy
### Backend → Render
- New **Web Service**, connect the repo, root dir `folio-backend` (or use `render.yaml`).
- **Start Command (must be exactly this):** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  — or, simplest and foolproof: `python start.py`. Do **NOT** use `--reload` and do **NOT**
  hardcode a port; Render injects `$PORT` and the app must listen on `0.0.0.0`, or Render reports
  "No open ports detected" and the deploy fails.
- **Build Command:** `pip install -r requirements.txt`  ·  **Health Check Path:** `/api/v1/health`
- **Environment variables — add ALL of these** (Environment tab). Without `DATABASE_URL` the app
  crashes on boot with `RuntimeError: DATABASE_URL is not set`:
  `PYTHON_VERSION=3.12.7`, `APP_ENV=production`, `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`,
  `SUPABASE_JWT_SECRET`, `SUPABASE_SERVICE_ROLE_KEY`, `CORS_ORIGINS=https://your-vercel-app.vercel.app`,
  `APP_URL`, `PUBLIC_PORTFOLIO_URL`, `API_URL` (the last three = your deployed URLs).
- After saving env vars, **Manual Deploy → Clear build cache & deploy**.

### Frontend → Vercel
- Import the repo, root dir `folio-frontend`.
- Add the `NEXT_PUBLIC_*` env vars; set `NEXT_PUBLIC_API_URL` to the Render URL.
- After deploy, update Supabase Auth **Site URL** + **Redirect URLs** to the Vercel domain.

---

## Notes / gotchas
- **Render Python version (REQUIRED — do this or the build fails).** Render is defaulting to
  Python **3.14**, where `pydantic-core` has no prebuilt wheel, so it tries to compile Rust on a
  read-only filesystem and dies. Pin it to **3.12.7**. The surest way (works no matter how the
  service was created) is the dashboard env var:
    1. Render → your `folio-api` service → **Environment** → **Add Environment Variable**
    2. Key `PYTHON_VERSION`, Value `3.12.7` → **Save changes**
    3. **Manual Deploy → Clear build cache & deploy**
  The build log should then show `python3.12`, and `pydantic-core` installs from a wheel (no Rust).
  This repo also ships `.python-version` (`3.12.7`), `runtime.txt`, and `PYTHON_VERSION` in
  `render.yaml`, but a **manually-created** service ignores `render.yaml`, and `.python-version`
  is only read when it sits at the service's root directory — so set the env var to be safe.
- **pgbouncer transaction pooler**: the engine already sets `NullPool` + disables the asyncpg
  statement cache + uses unique prepared-statement names. Use the **pooler** string (6543), not the
  direct 5432 one, on Render.
- **Backend bypasses RLS** (it connects with the pooler role), so ownership is enforced in the
  service layer. RLS protects any direct `@supabase/supabase-js` table access from the browser.
- **Auth tokens (HS256 or asymmetric).** The backend verifies Supabase access tokens with
  either the legacy HS256 secret (`SUPABASE_JWT_SECRET`) or the project's JWKS
  (asymmetric ES256/RS256, used by the new `sb_publishable_...` key system) — whichever the
  token uses. For HS256, set `SUPABASE_JWT_SECRET`. For asymmetric, just make sure
  `SUPABASE_URL` is correct (JWKS is fetched from it). A wrong/empty value shows up as
  `401 Invalid token` on `/me`.
- If email confirmation links point at the wrong host, fix Supabase Auth URL Configuration.

## Repo layout / Render Root Directory (IMPORTANT)
`requirements.txt` and the `app/` folder must sit at the SAME level, and Render's
**Root Directory** must point at that level. Two valid setups:
- Repo has a `folio-backend/` subfolder (app/, requirements.txt inside) → set Render
  **Settings → Root Directory = `folio-backend`**.
- Repo root directly contains `app/`, `requirements.txt`, `start.py` → leave Root Directory blank.
Symptom of a mismatch: build succeeds (`pip install` finds requirements.txt) but the app
crashes at start with `ModuleNotFoundError: No module named 'app'` (uvicorn's CWD has no `app/`).

## Media uploads (Cloudinary — Phase 4)
Direct browser->Cloudinary uploads with a server-side signature (API secret stays on the backend).
1. Create a free Cloudinary account -> Dashboard shows **Cloud name**, **API Key**, **API Secret**.
2. Add these backend env vars (Render): `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`,
   `CLOUDINARY_API_SECRET`, and optionally `CLOUDINARY_UPLOAD_FOLDER` (default `folio`).
3. Redeploy. In the dashboard, image fields (avatar, project cover, gallery, testimonial photo)
   now show an **Upload** button. Until configured, you can still paste image URLs.
No frontend key needed — the browser fetches a one-time signature from `/api/v1/media/sign`.

## Admin access (Phase 8)
Roles live in the `profiles.role` column. To make a user an admin, run in Supabase SQL:
```sql
update public.profiles set role = 'admin' where email = 'you@example.com';
```
Admins see an **Admin** item in the dashboard sidebar (platform stats + all portfolios) and can
use PRO templates (e.g. **Studio**). Regular users see the free templates only.

## Billing / plans (Phase 10)
Run migration `0010_billing.sql`. Admins set price, pro features and payment details
(USDT BEP-20 address, Nagad, bKash) in **Dashboard -> Admin -> Billing settings**. Users
pay manually, submit TxID + screenshot on **Dashboard -> Upgrade**, and an admin approves
the payment (which flips the user's plan to `pro`, unlocking PRO templates).

## Troubleshooting the exact errors
- **`RuntimeError: DATABASE_URL is not set` / "No open ports detected"** → the Render env vars
  aren't set and/or the Start Command is wrong. Fix both as in "Backend → Render" above. The app
  now boots even without `DATABASE_URL` so `/api/v1/health` responds and the port opens; check
  `/api/v1/health/db` — it returns `503 db_unavailable` until `DATABASE_URL` is set correctly.
- **Vercel still installs `next@15.1.3` ("Detected Next.js version: 15.1.3")** → your repo's
  `package.json` still pins the old version, or a committed `package-lock.json` locks it. In
  `folio-frontend`: make sure `package.json` has `"next": "^15.5.9"`, then
  `rm -f package-lock.json && rm -rf node_modules && npm install` to regenerate the lockfile at the
  patched version, commit **both** files, and push. Vercel blocks the vulnerable 15.1.3 (CVE-2025-66478).
