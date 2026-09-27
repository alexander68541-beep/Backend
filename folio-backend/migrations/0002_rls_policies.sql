-- ============================================================================
-- Folio — Phase 1 Row Level Security
-- The FastAPI backend uses the pooler role (bypasses RLS) and enforces ownership
-- itself. These policies protect any DIRECT access via @supabase/supabase-js.
-- ============================================================================

alter table public.profiles            enable row level security;
alter table public.portfolios          enable row level security;
alter table public.portfolio_profiles  enable row level security;
alter table public.username_history    enable row level security;
alter table public.reserved_usernames  enable row level security;

-- ---------- profiles: a user sees/edits only their own account row ----------
drop policy if exists profiles_select_own on public.profiles;
create policy profiles_select_own on public.profiles
  for select using (auth.uid() = id);

drop policy if exists profiles_update_own on public.profiles;
create policy profiles_update_own on public.profiles
  for update using (auth.uid() = id) with check (auth.uid() = id);

-- ---------- portfolios: owner full access; public reads published ----------
drop policy if exists portfolios_owner_all on public.portfolios;
create policy portfolios_owner_all on public.portfolios
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists portfolios_public_read on public.portfolios;
create policy portfolios_public_read on public.portfolios
  for select using (status = 'published' and deleted_at is null);

-- ---------- portfolio_profiles: via portfolio ownership; public reads published ----------
drop policy if exists pportfolio_profiles_owner_all on public.portfolio_profiles;
create policy pportfolio_profiles_owner_all on public.portfolio_profiles
  for all
  using (exists (
    select 1 from public.portfolios p
    where p.id = portfolio_profiles.portfolio_id and p.user_id = auth.uid()
  ))
  with check (exists (
    select 1 from public.portfolios p
    where p.id = portfolio_profiles.portfolio_id and p.user_id = auth.uid()
  ));

drop policy if exists portfolio_profiles_public_read on public.portfolio_profiles;
create policy portfolio_profiles_public_read on public.portfolio_profiles
  for select using (exists (
    select 1 from public.portfolios p
    where p.id = portfolio_profiles.portfolio_id
      and p.status = 'published' and p.deleted_at is null
  ));

-- ---------- username_history: owner reads only ----------
drop policy if exists username_history_owner_read on public.username_history;
create policy username_history_owner_read on public.username_history
  for select using (exists (
    select 1 from public.portfolios p
    where p.id = username_history.portfolio_id and p.user_id = auth.uid()
  ));

-- ---------- reserved_usernames: readable by authenticated users; no client writes ----------
drop policy if exists reserved_usernames_read on public.reserved_usernames;
create policy reserved_usernames_read on public.reserved_usernames
  for select to authenticated using (true);
