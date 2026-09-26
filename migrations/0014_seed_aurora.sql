-- Folio — seed the example Aurora template as an active listing. Run AFTER 0013.
insert into public.custom_templates (key, name, category, base, plan, is_published)
select 'aurora','Aurora','Creative','aurora','free',true
where not exists (select 1 from public.custom_templates ct where ct.key = 'aurora');
