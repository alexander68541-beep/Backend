-- Folio — admin-controlled branding + SEO. Run AFTER 0026.
alter table public.platform_settings add column if not exists site_name text;
alter table public.platform_settings add column if not exists logo_url text;
alter table public.platform_settings add column if not exists favicon_url text;
alter table public.platform_settings add column if not exists google_site_verification text;
alter table public.platform_settings add column if not exists seo_keywords text;
alter table public.platform_settings add column if not exists seo_description text;
alter table public.platform_settings add column if not exists footer_text text;
