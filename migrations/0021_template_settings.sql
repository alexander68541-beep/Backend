-- Folio — Phase 18: per-portfolio template settings (font, section visibility/order). Run AFTER 0020.
alter table public.portfolios add column if not exists settings jsonb not null default '{}';
