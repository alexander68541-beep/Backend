-- Folio — Phase 17: content limits + privacy. Run AFTER 0019.
alter table public.portfolios add column if not exists visibility text not null default 'public'
  check (visibility in ('public','unlisted','private'));
alter table public.platform_settings add column if not exists plan_limits jsonb not null default '{}';
