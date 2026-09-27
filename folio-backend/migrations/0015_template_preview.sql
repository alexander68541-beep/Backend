-- Folio — template preview image (optional admin-uploaded). Run AFTER 0014.
alter table public.custom_templates add column if not exists preview_url text;
