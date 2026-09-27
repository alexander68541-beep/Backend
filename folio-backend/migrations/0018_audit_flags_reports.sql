-- Folio — Phase 15: audit logs + feature flags + moderation reports. Run AFTER 0017.
create table if not exists public.audit_logs (
  id          uuid primary key default gen_random_uuid(),
  actor_email text,
  action      text not null,
  target      text,
  meta        jsonb not null default '{}',
  created_at  timestamptz not null default now()
);
create index if not exists idx_audit_created on public.audit_logs(created_at desc);

create table if not exists public.reports (
  id           uuid primary key default gen_random_uuid(),
  portfolio_id uuid references public.portfolios(id) on delete set null,
  username     text,
  reason       text not null,
  detail       text,
  status       text not null default 'pending' check (status in ('pending','dismissed','actioned')),
  created_at   timestamptz not null default now()
);
create index if not exists idx_reports_status on public.reports(status, created_at desc);

alter table public.platform_settings add column if not exists flags jsonb not null default '{}';

alter table public.audit_logs enable row level security;   -- admin-only via backend (no policies)
alter table public.reports enable row level security;      -- admin-only via backend (no policies)
