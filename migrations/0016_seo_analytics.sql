-- Folio — Phase 12: per-portfolio SEO + view analytics. Run AFTER 0015.
alter table public.portfolios add column if not exists seo_title text;
alter table public.portfolios add column if not exists seo_description text;
alter table public.portfolios add column if not exists seo_image text;

create table if not exists public.portfolio_view_daily (
  portfolio_id uuid not null references public.portfolios(id) on delete cascade,
  day date not null,
  count integer not null default 0,
  primary key (portfolio_id, day)
);
create index if not exists idx_view_daily_portfolio on public.portfolio_view_daily(portfolio_id, day);

alter table public.portfolio_view_daily enable row level security;  -- backend-only (pooler bypasses); no policies = no direct access
