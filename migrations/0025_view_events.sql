-- Folio — Phase 19: advanced analytics (privacy-safe view events). Run AFTER 0024.
create table if not exists public.view_events (
  id           uuid primary key default gen_random_uuid(),
  portfolio_id uuid not null references public.portfolios(id) on delete cascade,
  day          date not null,
  visitor_hash text,   -- sha256(ip + day + salt), rotates daily; no raw IP stored
  referrer     text,   -- referring domain only
  device       text,   -- 'mobile' | 'desktop'
  country      text,   -- 2-letter code from edge header, if available
  created_at   timestamptz not null default now()
);
create index if not exists idx_view_events_portfolio on public.view_events(portfolio_id, day);
alter table public.view_events enable row level security;  -- backend-only
