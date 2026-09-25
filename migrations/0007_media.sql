-- ============================================================================
-- Folio — Phase 4: Media (gallery images + videos). Run AFTER 0001-0006.
-- ============================================================================
create table if not exists public.portfolio_gallery (
  id uuid primary key default gen_random_uuid(),
  portfolio_id uuid not null references public.portfolios(id) on delete cascade,
  image_url text not null,
  caption text,
  position integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.portfolio_videos (
  id uuid primary key default gen_random_uuid(),
  portfolio_id uuid not null references public.portfolios(id) on delete cascade,
  title text,
  url text not null,
  position integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

do $$
declare t text;
begin
  foreach t in array array['portfolio_gallery','portfolio_videos'] loop
    execute format('create index if not exists idx_%s_portfolio on public.%s(portfolio_id);', t, t);
    execute format('drop trigger if exists trg_%s_updated_at on public.%s;', t, t);
    execute format('create trigger trg_%s_updated_at before update on public.%s
      for each row execute function public.set_updated_at();', t, t);
    execute format('alter table public.%s enable row level security;', t);
    execute format('drop policy if exists %s_owner_all on public.%s;', t, t);
    execute format('create policy %s_owner_all on public.%s for all
      using (exists (select 1 from public.portfolios p where p.id = %s.portfolio_id and p.user_id = auth.uid()))
      with check (exists (select 1 from public.portfolios p where p.id = %s.portfolio_id and p.user_id = auth.uid()));',
      t, t, t, t);
    execute format('drop policy if exists %s_public_read on public.%s;', t, t);
    execute format('create policy %s_public_read on public.%s for select
      using (exists (select 1 from public.portfolios p where p.id = %s.portfolio_id and p.status = ''published'' and p.deleted_at is null));',
      t, t, t);
  end loop;
end $$;
