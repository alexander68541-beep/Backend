-- Folio — Phase 10: plans + manual payments (admin-controlled). Run AFTER 0001-0009.
alter table public.profiles
  add column if not exists plan text not null default 'free' check (plan in ('free','pro'));

-- single-row platform settings (admin editable)
create table if not exists public.platform_settings (
  id             integer primary key default 1,
  pro_price      text default '10',
  currency       text default 'USD',
  pro_features   text[] not null default '{}',
  bep20_address  text,
  nagad_number   text,
  bkash_number   text,
  payment_note   text,
  updated_at     timestamptz not null default now(),
  constraint platform_settings_singleton check (id = 1)
);
insert into public.platform_settings (id) values (1) on conflict (id) do nothing;

-- manual payment submissions
create table if not exists public.payment_requests (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null references public.profiles(id) on delete cascade,
  method         text not null,
  amount         text,
  tx_id          text,
  screenshot_url text,
  status         text not null default 'pending' check (status in ('pending','approved','rejected')),
  note           text,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);
create index if not exists idx_payment_user on public.payment_requests(user_id);

drop trigger if exists trg_payment_updated_at on public.payment_requests;
create trigger trg_payment_updated_at before update on public.payment_requests
  for each row execute function public.set_updated_at();
drop trigger if exists trg_settings_updated_at on public.platform_settings;
create trigger trg_settings_updated_at before update on public.platform_settings
  for each row execute function public.set_updated_at();

-- RLS (defense in depth; backend uses pooler role)
alter table public.payment_requests enable row level security;
drop policy if exists payment_owner on public.payment_requests;
create policy payment_owner on public.payment_requests for select using (auth.uid() = user_id);
alter table public.platform_settings enable row level security;
drop policy if exists settings_read on public.platform_settings;
create policy settings_read on public.platform_settings for select to authenticated using (true);
