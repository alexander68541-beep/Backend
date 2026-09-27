-- Folio — Phase 10.1: dynamic payment methods + admin storage config. Run AFTER 0010.
alter table public.platform_settings add column if not exists payment_methods jsonb not null default '[]';
alter table public.platform_settings add column if not exists cloudinary_cloud_name text;
alter table public.platform_settings add column if not exists cloudinary_api_key text;
alter table public.platform_settings add column if not exists cloudinary_api_secret text;
alter table public.platform_settings add column if not exists cloudinary_folder text default 'folio';
