-- Folio — Phase 14: contact form + notifications + email config. Run AFTER 0016.
create table if not exists public.contact_submissions (
  id           uuid primary key default gen_random_uuid(),
  portfolio_id uuid not null references public.portfolios(id) on delete cascade,
  name         text,
  email        text,
  message      text not null,
  ip           text,
  read         boolean not null default false,
  created_at   timestamptz not null default now()
);
create index if not exists idx_contact_portfolio on public.contact_submissions(portfolio_id, created_at);

create table if not exists public.notifications (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references public.profiles(id) on delete cascade,
  type       text not null default 'system',
  title      text not null,
  body       text,
  read       boolean not null default false,
  created_at timestamptz not null default now()
);
create index if not exists idx_notifications_user on public.notifications(user_id, created_at);

-- admin-configurable email (Resend) settings
alter table public.platform_settings add column if not exists resend_api_key text;
alter table public.platform_settings add column if not exists email_from text;

-- RLS (backend uses pooler; these protect direct client access)
alter table public.contact_submissions enable row level security;
drop policy if exists contact_owner_read on public.contact_submissions;
create policy contact_owner_read on public.contact_submissions for select
  using (exists (select 1 from public.portfolios p where p.id = contact_submissions.portfolio_id and p.user_id = auth.uid()));

alter table public.notifications enable row level security;
drop policy if exists notif_owner on public.notifications;
create policy notif_owner on public.notifications for select using (auth.uid() = user_id);
