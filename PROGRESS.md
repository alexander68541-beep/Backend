# Folio — Build Progress

Stack: Next.js (Vercel) + FastAPI (Render) + Supabase (Auth + Postgres + RLS) + Cloudinary (Phase 5).

## Phase 1 — Foundation  ✅ (this delivery)
- [x] Backend project structure (modular, async, service layer)
- [x] Environment configuration (pydantic-settings, no secrets in code)
- [x] Supabase Postgres connection (asyncpg, NullPool + statement-cache off for pgbouncer)
- [x] Auth: verify Supabase JWT (HS256), `current_user` dependency, no trust of client IDs
- [x] DB schema: profiles, portfolios, portfolio_profiles, username_history, reserved_usernames
- [x] Signup trigger: auto-create account + primary draft portfolio
- [x] Row Level Security on all Phase-1 tables (+ public read for published)
- [x] Base security: CORS, security headers, safe error handling, rate limiting (login-adjacent)
- [x] Username system: validation, reserved check, profanity seed, change cooldown + history
- [x] User profile (account) + portfolio entity endpoints (ownership / IDOR enforced)
- [x] Frontend: Supabase Auth (register / verify / login / forgot / reset), protected dashboard
- [x] Frontend: username picker, profile section editor, publish/unpublish, base design system

## Phase 2 — Portfolio Data  ⬜ (next)
social_links, skills, projects, experience, education, services, testimonials, gallery, videos, contact, resume — as universal entities.

## Phase 3 — Template Engine  ⬜
## Phase 4 — Public Portfolio  ⬜
## Phase 5 — Media (Cloudinary, multi-account fallback)  ⬜
## Phase 6 — Dashboard editor + preview  ⬜  (MVP live after this)
## Phase 7 — Admin + roles  ⬜
## Phase 8 — Advanced security  ⬜  (production-complete after this)
## Phase 9 — Future expansion (domains, analytics, AI, billing, social...)  ⬜
