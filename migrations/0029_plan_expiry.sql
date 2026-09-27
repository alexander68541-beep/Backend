-- Folio — subscription expiry. Run AFTER 0028.
alter table public.profiles add column if not exists plan_expires_at timestamptz;
