-- Folio — Phase 5: appearance (accent color). Run AFTER 0001-0007.
alter table public.portfolios
  add column if not exists accent text not null default '#7c6cff';
