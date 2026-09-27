-- Folio — SAFETY: ensure every column the app models expect exists.
-- Idempotent (IF NOT EXISTS). Safe to run anytime; run this if you see
-- "Couldn't load settings" or "column ... does not exist".

-- platform_settings
alter table public.platform_settings add column if not exists pro_price text;
alter table public.platform_settings add column if not exists currency text;
alter table public.platform_settings add column if not exists pro_features text[] not null default '{}';
alter table public.platform_settings add column if not exists payment_note text;
alter table public.platform_settings add column if not exists payment_methods jsonb not null default '[]';
alter table public.platform_settings add column if not exists cloudinary_cloud_name text;
alter table public.platform_settings add column if not exists cloudinary_api_key text;
alter table public.platform_settings add column if not exists cloudinary_api_secret text;
alter table public.platform_settings add column if not exists cloudinary_folder text;
alter table public.platform_settings add column if not exists resend_api_key text;
alter table public.platform_settings add column if not exists email_from text;
alter table public.platform_settings add column if not exists flags jsonb not null default '{}';
alter table public.platform_settings add column if not exists email_enabled boolean not null default true;
alter table public.platform_settings add column if not exists email_accounts jsonb not null default '[]';
alter table public.platform_settings add column if not exists cloudinary_accounts jsonb not null default '[]';
alter table public.platform_settings add column if not exists plan_limits jsonb not null default '{}';
alter table public.platform_settings add column if not exists plans jsonb not null default '[]';
alter table public.platform_settings add column if not exists site_name text;
alter table public.platform_settings add column if not exists logo_url text;
alter table public.platform_settings add column if not exists favicon_url text;
alter table public.platform_settings add column if not exists google_site_verification text;
alter table public.platform_settings add column if not exists seo_keywords text;
alter table public.platform_settings add column if not exists seo_description text;
alter table public.platform_settings add column if not exists footer_text text;
alter table public.platform_settings add column if not exists contact_email text;
alter table public.platform_settings add column if not exists contact_phone text;
alter table public.platform_settings add column if not exists contact_whatsapp text;
alter table public.platform_settings add column if not exists contact_address text;
alter table public.platform_settings add column if not exists contact_note text;

-- portfolios
alter table public.portfolios add column if not exists seo_title text;
alter table public.portfolios add column if not exists seo_description text;
alter table public.portfolios add column if not exists seo_image text;
alter table public.portfolios add column if not exists visibility text not null default 'public';
alter table public.portfolios add column if not exists settings jsonb not null default '{}';
alter table public.portfolios add column if not exists published_data jsonb;
alter table public.portfolios add column if not exists published_at timestamptz;

-- payment_requests
alter table public.payment_requests add column if not exists plan text not null default 'pro';
alter table public.payment_requests add column if not exists period text not null default 'lifetime';

-- custom_templates
alter table public.custom_templates add column if not exists preview_url text;

-- ensure the singleton settings row exists
insert into public.platform_settings (id) values (1) on conflict (id) do nothing;
