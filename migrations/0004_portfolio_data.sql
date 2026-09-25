-- ============================================================================
-- Folio — Phase 2: Portfolio Data (universal entities)
-- Run AFTER 0001-0003. Safe to re-run.
-- Each entity belongs to a portfolio; template-independent, user-owned.
-- ============================================================================

-- ---------- projects ----------
create table if not exists public.portfolio_projects (
  id            uuid primary key default gen_random_uuid(),
  portfolio_id  uuid not null references public.portfolios(id) on delete cascade,
  title         text not null,
  role          text,
  description   text,
  url           text,
  image_url     text,
  tags          text[] not null default '{}',
  start_date    text,
  end_date      text,
  is_featured   boolean not null default false,
  position      integer not null default 0,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

-- ---------- skills ----------
create table if not exists public.portfolio_skills (
  id            uuid primary key default gen_random_uuid(),
  portfolio_id  uuid not null references public.portfolios(id) on delete cascade,
  name          text not null,
  category      text,
  level         integer check (level is null or (level between 1 and 5)),
  position      integer not null default 0,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

-- ---------- experience ----------
create table if not exists public.portfolio_experience (
  id            uuid primary key default gen_random_uuid(),
  portfolio_id  uuid not null references public.portfolios(id) on delete cascade,
  company       text not null,
  title         text,
  location      text,
  description   text,
  start_date    text,
  end_date      text,
  is_current    boolean not null default false,
  position      integer not null default 0,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

-- ---------- education ----------
create table if not exists public.portfolio_education (
  id            uuid primary key default gen_random_uuid(),
  portfolio_id  uuid not null references public.portfolios(id) on delete cascade,
  school        text not null,
  degree        text,
  field         text,
  start_date    text,
  end_date      text,
  description   text,
  position      integer not null default 0,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

-- ---------- social links ----------
create table if not exists public.portfolio_social_links (
  id            uuid primary key default gen_random_uuid(),
  portfolio_id  uuid not null references public.portfolios(id) on delete cascade,
  platform      text not null,
  url           text not null,
  label         text,
  position      integer not null default 0,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

-- ---------- indexes ----------
create index if not exists idx_pp_projects_portfolio   on public.portfolio_projects(portfolio_id);
create index if not exists idx_pp_skills_portfolio     on public.portfolio_skills(portfolio_id);
create index if not exists idx_pp_experience_portfolio on public.portfolio_experience(portfolio_id);
create index if not exists idx_pp_education_portfolio  on public.portfolio_education(portfolio_id);
create index if not exists idx_pp_links_portfolio      on public.portfolio_social_links(portfolio_id);

-- ---------- updated_at triggers ----------
do $$
declare t text;
begin
  foreach t in array array[
    'portfolio_projects','portfolio_skills','portfolio_experience',
    'portfolio_education','portfolio_social_links'
  ] loop
    execute format('drop trigger if exists trg_%s_updated_at on public.%s;', t, t);
    execute format(
      'create trigger trg_%s_updated_at before update on public.%s
         for each row execute function public.set_updated_at();', t, t);
  end loop;
end $$;

-- ---------- RLS: owner full access; public reads published ----------
do $$
declare t text;
begin
  foreach t in array array[
    'portfolio_projects','portfolio_skills','portfolio_experience',
    'portfolio_education','portfolio_social_links'
  ] loop
    execute format('alter table public.%s enable row level security;', t);

    execute format('drop policy if exists %s_owner_all on public.%s;', t, t);
    execute format(
      'create policy %s_owner_all on public.%s for all
         using (exists (select 1 from public.portfolios p
                        where p.id = %s.portfolio_id and p.user_id = auth.uid()))
         with check (exists (select 1 from public.portfolios p
                        where p.id = %s.portfolio_id and p.user_id = auth.uid()));',
      t, t, t, t);

    execute format('drop policy if exists %s_public_read on public.%s;', t, t);
    execute format(
      'create policy %s_public_read on public.%s for select
         using (exists (select 1 from public.portfolios p
                        where p.id = %s.portfolio_id
                          and p.status = ''published'' and p.deleted_at is null));',
      t, t, t);
  end loop;
end $$;
