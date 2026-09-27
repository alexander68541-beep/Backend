-- Folio — Phase 21 part 2: social (likes + saves). Run AFTER 0025.
create table if not exists public.portfolio_likes (
  user_id      uuid not null references public.profiles(id) on delete cascade,
  portfolio_id uuid not null references public.portfolios(id) on delete cascade,
  created_at   timestamptz not null default now(),
  primary key (user_id, portfolio_id)
);
create index if not exists idx_likes_portfolio on public.portfolio_likes(portfolio_id);

create table if not exists public.portfolio_saves (
  user_id      uuid not null references public.profiles(id) on delete cascade,
  portfolio_id uuid not null references public.portfolios(id) on delete cascade,
  created_at   timestamptz not null default now(),
  primary key (user_id, portfolio_id)
);
create index if not exists idx_saves_user on public.portfolio_saves(user_id, created_at);

alter table public.portfolio_likes enable row level security;
alter table public.portfolio_saves enable row level security;
