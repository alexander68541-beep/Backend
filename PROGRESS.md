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

## Phase 2 — Portfolio Data  🟡 (in progress)
- [x] projects, skills, experience, education, social_links — full CRUD (create/edit/delete), ownership-scoped, RLS
- [x] Dashboard editors for each (add/edit/delete, saves to DB)
- [x] services, certifications, achievements, testimonials, publications — full CRUD
- [x] extended profile: about, tagline, pronouns, contact (email/phone/website/availability), resume
- [x] subdomain routing ({username}.{domain}, dynamic — no hardcoded domain)
- [x] full dashboard sidebar (Main / Content / Connect / Optional)
- [ ] gallery, videos (media, Phase 5)

## Phase 3 — Template Engine + Public Page  🟡 (in progress)
- [x] Public API: GET /api/v1/public/{username} (published data, no auth)
- [x] Public portfolio page at /p/{username} (SSR, SEO metadata, 404 handling)
- [x] Template registry + 2 real templates (Minimal light, Bold dark)
- [x] Template selection in dashboard (live), template stored on portfolio
- [ ] More templates + section ordering (later)

## Phase 3 (old marker) — Template Engine  ⬜
## Phase 4 — Public Portfolio  ⬜
## Phase 5 — Media (Cloudinary, multi-account fallback)  ⬜
## Phase 6 — Dashboard editor + preview  ⬜  (MVP live after this)
## Phase 7 — Admin + roles  ⬜
## Phase 8 — Advanced security  ⬜  (production-complete after this)
## Phase 9 — Future expansion (domains, analytics, AI, billing, social...)  ⬜

## Phase 5 — Appearance + template polish  🟡
- [x] Accent colour per portfolio (applied across both templates)
- [x] Link chips with auto platform icons (GitHub/LinkedIn/website/…), clearly clickable
- [x] Click-to-zoom lightbox on images; gallery natural aspect (no crop)
- [x] Templates render tagline, pronouns, and every provided field

## Phase 10 — Plans + manual payments  🟡
- [x] free/pro plan; PRO templates unlock for pro (or admin)
- [x] admin-controlled settings: price, currency, pro features, BEP-20 / Nagad / bKash, note
- [x] user Upgrade page: methods, submit TxID + screenshot; admin approve/reject -> upgrades user

## Phase 11 — Template builder + Messaging  🟡
- [x] Admin builds custom templates (base + accent + category + plan) — appear for users by category
- [x] Users apply custom templates; PRO ones gated by plan
- [x] Messaging: user↔admin thread (custom-template requests etc.), admin inbox + reply, realtime polling

## Phase 11.1 — Code-defined templates
- [x] Templates are React components in src/templates + a registry; admin lists them
- [x] Admin listing: coded key + name + category + plan + active/inactive; DB-driven gating
- [x] See folio-frontend/src/templates/README.md for how to add a coded template

## Phase 11.2 — Preview + dynamic settings
- [x] Live template preview with demo data (/t/{key}); card live thumbnails + optional admin preview image
- [x] Settings dynamic: display name, change password, delete account (cascades)
- [x] Admin template Active/Inactive toggle clarified (status badge + Activate/Deactivate)

## Phase 12 — Link fix + SEO  🟡
- [x] External links without a scheme are auto-prefixed https:// (no more broken relative URLs)
- [x] Public pages: Open Graph + Twitter meta + canonical (per portfolio, avatar as image)
- [x] sitemap.xml (published portfolios) + robots.txt; SSR pages for Google

## Phase 12.1 — Analytics + real SEO + desktop preview
- [x] View analytics: per-portfolio daily views (beacon), dashboard chart (total/7d/today)
- [x] SEO page is real: per-portfolio meta title, description, og:image (overrides defaults)
- [x] Template thumbnails render the full desktop view (auto-fit), not a crop
