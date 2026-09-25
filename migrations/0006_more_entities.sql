-- ============================================================================
-- Folio — Phase 3.5: more universal entities + extended profile (About/Contact/Resume)
-- Run AFTER 0001-0005. Safe to re-run.
-- ============================================================================

-- ---------- extend portfolio_profiles ----------
alter table public.portfolio_profiles add column if not exists tagline      text;
alter table public.portfolio_profiles add column if not exists pronouns     text;
alter table public.portfolio_profiles add column if not exists about        text;
alter table public.portfolio_profiles add column if not exists email        text;
alter table public.portfolio_profiles add column if not exists phone        text;
alter table public.portfolio_profiles add column if not exists website      text;
alter table public.portfolio_profiles add column if not exists availability text;
alter table public.portfolio_profiles add column if not exists resume_url   text;

-- ---------- services ----------
create table if not exists public.portfolio_services (
  id uuid primary key default gen_random_uuid(),
  portfolio_id uuid not null references public.portfolios(id) on delete cascade,
  title text not null,
  description text,
  price text,
  position integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ---------- certifications ----------
create table if not exists public.portfolio_certifications (
  id uuid primary key default gen_random_uuid(),
  portfolio_id uuid not null references public.portfolios(id) on delete cascade,
  name text not null,
  issuer text,
  issue_date text,
  credential_id text,
  url text,
  position integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ---------- achievements ----------
create table if not exists public.portfolio_achievements (
  id uuid primary key default gen_random_uuid(),
  portfolio_id uuid not null references public.portfolios(id) on delete cascade,
  title text not null,
  description text,
  date text,
  position integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ---------- testimonials ----------
create table if not exists public.portfolio_testimonials (
  id uuid primary key default gen_random_uuid(),
  portfolio_id uuid not null references public.portfolios(id) on delete cascade,
  author text not null,
  role text,
  quote text not null,
  avatar_url text,
  position integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ---------- publications / articles ----------
create table if not exists public.portfolio_publications (
  id uuid primary key default gen_random_uuid(),
  portfolio_id uuid not null references public.portfolios(id) on delete cascade,
  title text not null,
  publisher text,
  date text,
  url text,
  description text,
  position integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ---------- indexes + updated_at triggers + RLS ----------
do $$
declare t text;
begin
  foreach t in array array[
    'portfolio_services','portfolio_certifications','portfolio_achievements',
    'portfolio_testimonials','portfolio_publications'
  ] loop
    execute format('create index if not exists idx_%s_portfolio on public.%s(portfolio_id);', t, t);

    execute format('drop trigger if exists trg_%s_updated_at on public.%s;', t, t);
    execute format(
      'create trigger trg_%s_updated_at before update on public.%s
         for each row execute function public.set_updated_at();', t, t);

    execute format('alter table public.%s enable row level security;', t);

    execute format('drop policy if exists %s_owner_all on public.%s;', t, t);
    execute format(
      'create policy %s_owner_all on public.%s for all
         using (exists (select 1 from public.portfolios p where p.id = %s.portfolio_id and p.user_id = auth.uid()))
         with check (exists (select 1 from public.portfolios p where p.id = %s.portfolio_id and p.user_id = auth.uid()));',
      t, t, t, t);

    execute format('drop policy if exists %s_public_read on public.%s;', t, t);
    execute format(
      'create policy %s_public_read on public.%s for select
         using (exists (select 1 from public.portfolios p
                        where p.id = %s.portfolio_id and p.status = ''published'' and p.deleted_at is null));',
      t, t, t);
  end loop;
end $$;
