-- Folio — Phase 11: custom templates (admin presets) + messaging. Run AFTER 0011.
create table if not exists public.custom_templates (
  id           uuid primary key default gen_random_uuid(),
  name         text not null,
  category     text not null default 'Custom',
  base         text not null default 'minimal',
  accent       text not null default '#7c6cff',
  plan         text not null default 'free' check (plan in ('free','pro')),
  is_published boolean not null default true,
  position     integer not null default 0,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

create table if not exists public.messages (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references public.profiles(id) on delete cascade,
  sender     text not null check (sender in ('user','admin')),
  body       text not null,
  read       boolean not null default false,
  created_at timestamptz not null default now()
);
create index if not exists idx_messages_user on public.messages(user_id, created_at);

drop trigger if exists trg_custom_templates_updated_at on public.custom_templates;
create trigger trg_custom_templates_updated_at before update on public.custom_templates
  for each row execute function public.set_updated_at();

alter table public.custom_templates enable row level security;
drop policy if exists custom_templates_read on public.custom_templates;
create policy custom_templates_read on public.custom_templates for select to authenticated using (is_published = true);

alter table public.messages enable row level security;
drop policy if exists messages_owner on public.messages;
create policy messages_owner on public.messages for select using (auth.uid() = user_id);
drop policy if exists messages_insert_own on public.messages;
create policy messages_insert_own on public.messages for insert with check (auth.uid() = user_id and sender = 'user');
