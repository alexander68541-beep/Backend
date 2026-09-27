-- Folio — admin contact details (shown on the public Contact page). Run AFTER 0027.
alter table public.platform_settings add column if not exists contact_email text;
alter table public.platform_settings add column if not exists contact_phone text;
alter table public.platform_settings add column if not exists contact_whatsapp text;
alter table public.platform_settings add column if not exists contact_address text;
alter table public.platform_settings add column if not exists contact_note text;
