-- Folio — Phase 11.1: code-defined templates + DB listing/activation. Run AFTER 0012.
-- 'key' maps a listing to a coded template component in the frontend registry.
alter table public.custom_templates add column if not exists key text;
update public.custom_templates set key = base where key is null or key = '';

-- seed the built-in coded templates as manageable listings (idempotent by key)
insert into public.custom_templates (key, name, category, base, plan, is_published)
select v.key, v.name, v.category, v.base, v.plan, true
from (values
  ('minimal','Minimal','Simple','minimal','free'),
  ('bold','Bold','Statement','bold','free'),
  ('editorial','Editorial','Structured','editorial','free'),
  ('studio','Studio','Premium','studio','pro')
) as v(key,name,category,base,plan)
where not exists (select 1 from public.custom_templates ct where ct.key = v.key);
