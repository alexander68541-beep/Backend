-- Folio — password-protected private links. Run AFTER 0030.
alter table public.portfolios add column if not exists access_password text;
