-- ============================================================================
-- Folio — Phase 3: template selection
-- Run AFTER 0001-0004. Safe to re-run.
-- ============================================================================
alter table public.portfolios
  add column if not exists template text not null default 'minimal';
