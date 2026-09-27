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

## Phase 14 — Contact + Notifications + Email
- [x] Public contact form on portfolios (honeypot + rate limit); owner gets a message inbox
- [x] In-app notifications (bell + unread count + notifications page); contact & payment events
- [x] Transactional email via Resend (admin-configured): contact received, payment approved
- [x] Fixed latent bug: /public/usernames & /view now import Portfolio (sitemap + analytics work)

## Phase 15 — Audit + Feature flags + Moderation + CORS fix
- [x] CORS now allows portfolio subdomains (regex from APP_URL) — contact/view work from *.domain
- [x] Audit logs for admin actions (suspend/delete/role/payment/template/report) + Audit tab (paginated)
- [x] Feature flags (enable_registration/public/contact) — admin toggles; contact form gated
- [x] Moderation: public Report link → reports queue; admin Suspend/Dismiss

## Phase 16 — Media multi-account + Email multi-account
- [x] Multiple Cloudinary accounts (admin list) with upload fallback A→B→C; media metadata table
- [x] Multiple email (Resend) accounts + master on/off toggle; send falls back through accounts
- [x] Email via HTTP API with browser UA (bypasses Cloudflare 1010); test-email surfaces real errors

## Phase 17 — Entitlements + limits + export + privacy + sessions
- [x] Centralised plan entitlements; free-plan content limits enforced on create (admin-overridable)
- [x] CrudSection shows count/limit and gates 'Add' with an Upgrade prompt at the cap
- [x] Data export: full portfolio JSON download
- [x] Privacy: public / unlisted / private (private hidden, only public in sitemap)
- [x] Sessions: sign out this device / all devices (global)

## Phase 18 (part 1) — Template settings: font + section visibility
- [x] Per-portfolio settings (JSONB): font choice + hidden sections
- [x] Customize page: pick a font, show/hide sections; applied on public pages
- [ ] TODO next: section ordering (drag), draft/publish snapshot, template versioning + admin migrate

## Phase 18 (part 2) — Section order + template fallback + admin migrate
- [x] Section ordering: reorder sections on the public page (Customize ↑/↓, applied via data-sec)
- [x] Template fallback: unknown template key safely renders Minimal (no crash)
- [x] Admin: migrate all portfolios from one template to another (audited)
- [ ] TODO final: draft vs published snapshot + template version numbers

## Multi-tier billing (Pro / Max + periods) + font fix + admin limits
- [x] Admin Plans catalog: tiers (Pro/Max/…), monthly/yearly/lifetime prices, advertised features
- [x] Upgrade page: plan cards + period toggle; payment carries plan+period; approve sets that tier
- [x] Pro & Max both unlock paid features; admin-editable free-plan limits
- [x] Font selection now applies across the whole public page (heading included)

## Phase 18 final — Draft vs Published + upgrade page
- [x] Publishing snapshots the portfolio; public page serves the last published version
- [x] Owner edits are a draft (Preview draft); 'Publish changes' updates the public snapshot
- [x] Upgrade page: only admin-configured periods shown, auto-default; single plan auto-selected

## Phase 19 — Advanced analytics
- [x] Privacy-safe view events (hashed visitor, referrer domain, device, country) — no PII
- [x] Analytics: unique visitors, top referrers, device split, top countries + daily series

## Phase 20 (part 1) — SEO/perf polish
- [x] JSON-LD Person structured data on public pages (Google rich results)
- [x] Per-portfolio favicon (avatar/OG image as tab icon)
- [x] Public pages cached with ISR (revalidate 60s) — fast, safe with the publish snapshot

## Phase 20 (part 2) — Observability
- [x] Backend Sentry error tracking (enabled only when SENTRY_DSN is set; captures unhandled errors)
- [x] Frontend error boundaries (error.tsx + global-error.tsx) — graceful recovery UI

## Phase 21 (part 1) — Discovery / Explore
- [x] Public /explore page: search portfolios by name, role, tagline, location, username
- [x] Privacy-respecting: only published + public portfolios appear (unlisted/private hidden)
- [ ] TODO: social (follow / like / collections) as a separate module

## Phase 21 (part 2) — Social (likes + saves)
- [x] Like a portfolio (public count; toggle when signed in) via a floating social bar
- [x] Save/bookmark portfolios; 'Saved' dashboard page lists them
- [x] Separate social module — never touches core portfolio data
