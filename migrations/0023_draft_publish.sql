-- Folio — Phase 18 final: draft vs published snapshot. Run AFTER 0022.
alter table public.portfolios add column if not exists published_data jsonb;
alter table public.portfolios add column if not exists published_at timestamptz;
