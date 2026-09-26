-- Folio — Phase 16: multi-Cloudinary + media metadata; multi email accounts + toggle. Run AFTER 0018.
alter table public.platform_settings add column if not exists email_enabled boolean not null default true;
alter table public.platform_settings add column if not exists email_accounts jsonb not null default '[]';
alter table public.platform_settings add column if not exists cloudinary_accounts jsonb not null default '[]';

create table if not exists public.media (
  id           uuid primary key default gen_random_uuid(),
  portfolio_id uuid references public.portfolios(id) on delete set null,
  user_id      uuid references public.profiles(id) on delete cascade,
  account      text,
  public_id    text,
  url          text,
  format       text,
  width        integer,
  height       integer,
  bytes        integer,
  created_at   timestamptz not null default now()
);
create index if not exists idx_media_user on public.media(user_id, created_at);
alter table public.media enable row level security;
drop policy if exists media_owner on public.media;
create policy media_owner on public.media for select using (auth.uid() = user_id);
