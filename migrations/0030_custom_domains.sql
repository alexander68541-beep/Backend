-- Folio — Phase 13: custom domains. Run AFTER 0029.
create table if not exists public.domains (
  id           uuid primary key default gen_random_uuid(),
  portfolio_id uuid not null references public.portfolios(id) on delete cascade,
  user_id      uuid not null references public.profiles(id) on delete cascade,
  username     text,                 -- denormalised for fast host->username resolution
  domain       text not null unique,
  verified     boolean not null default false,
  verification jsonb not null default '[]',
  created_at   timestamptz not null default now()
);
create index if not exists idx_domains_domain on public.domains(lower(domain));
alter table public.domains enable row level security;
drop policy if exists domains_owner on public.domains;
create policy domains_owner on public.domains for select using (auth.uid() = user_id);
