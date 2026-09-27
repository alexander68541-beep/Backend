-- Folio — multi-tier billing (Pro/Max + monthly/yearly/lifetime + admin plans). Run AFTER 0021.
alter table public.payment_requests add column if not exists plan text not null default 'pro';
alter table public.payment_requests add column if not exists period text not null default 'lifetime';
alter table public.platform_settings add column if not exists plans jsonb not null default '[]';
