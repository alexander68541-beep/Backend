-- ============================================================================
-- Folio — Phase 1 schema
-- Run this in the Supabase SQL editor (order: 0001 -> 0002 -> 0003).
-- Principle: account identity (profiles) is separate from portfolio presentation.
-- ============================================================================

create extension if not exists citext;
create extension if not exists pgcrypto;  -- gen_random_uuid()

-- ---------- updated_at helper ----------
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- ---------- profiles (account identity, 1:1 with auth.users) ----------
create table if not exists public.profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  email       text,
  full_name   text,
  role        text not null default 'user'
              check (role in ('user','admin','moderator','support','content_manager','finance')),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

drop trigger if exists trg_profiles_updated_at on public.profiles;
create trigger trg_profiles_updated_at before update on public.profiles
  for each row execute function public.set_updated_at();

-- ---------- portfolios (owned entity; public handle lives here) ----------
create table if not exists public.portfolios (
  id                     uuid primary key default gen_random_uuid(),
  user_id                uuid not null references public.profiles(id) on delete cascade,
  username               citext unique,
  status                 text not null default 'draft'
                         check (status in ('draft','published','unpublished','suspended','archived')),
  is_primary             boolean not null default true,
  username_changed_at    timestamptz,
  username_change_count  integer not null default 0,
  created_at             timestamptz not null default now(),
  updated_at             timestamptz not null default now(),
  deleted_at             timestamptz,
  -- username format guard (mirrors server-side validation); allows NULL
  constraint portfolios_username_format
    check (username is null or username ~ '^[a-z0-9]+(-[a-z0-9]+)*$')
);

create index if not exists idx_portfolios_user_id on public.portfolios(user_id);
-- fast public lookup of a published portfolio by handle
create index if not exists idx_portfolios_pub_username
  on public.portfolios(username) where status = 'published' and deleted_at is null;

drop trigger if exists trg_portfolios_updated_at on public.portfolios;
create trigger trg_portfolios_updated_at before update on public.portfolios
  for each row execute function public.set_updated_at();

-- ---------- portfolio_profiles (universal "profile" section) ----------
create table if not exists public.portfolio_profiles (
  portfolio_id  uuid primary key references public.portfolios(id) on delete cascade,
  display_name  text,
  title         text,
  bio           text,
  location      text,
  avatar_url    text,
  updated_at    timestamptz not null default now()
);

drop trigger if exists trg_portfolio_profiles_updated_at on public.portfolio_profiles;
create trigger trg_portfolio_profiles_updated_at before update on public.portfolio_profiles
  for each row execute function public.set_updated_at();

-- ---------- username_history ----------
create table if not exists public.username_history (
  id            uuid primary key default gen_random_uuid(),
  portfolio_id  uuid not null references public.portfolios(id) on delete cascade,
  old_username  citext,
  new_username  citext,
  changed_at    timestamptz not null default now()
);
create index if not exists idx_username_history_portfolio on public.username_history(portfolio_id);

-- ---------- reserved_usernames ----------
create table if not exists public.reserved_usernames (
  name        citext primary key,
  note        text,
  created_at  timestamptz not null default now()
);

-- ---------- signup handler: create account + primary draft portfolio ----------
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
declare
  new_portfolio_id uuid;
begin
  insert into public.profiles (id, email)
  values (new.id, new.email)
  on conflict (id) do nothing;

  insert into public.portfolios (user_id, is_primary, status)
  values (new.id, true, 'draft')
  returning id into new_portfolio_id;

  insert into public.portfolio_profiles (portfolio_id)
  values (new_portfolio_id)
  on conflict (portfolio_id) do nothing;

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
