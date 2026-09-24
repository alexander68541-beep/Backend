-- ============================================================================
-- Folio — reserved usernames seed (system routes + sensitive words).
-- Admin can add/remove these later (Phase 7). Safe to re-run.
-- ============================================================================
insert into public.reserved_usernames (name, note) values
  ('admin','system'), ('administrator','system'), ('root','system'),
  ('api','route'), ('auth','route'), ('login','route'), ('logout','route'),
  ('register','route'), ('signup','route'), ('signin','route'),
  ('dashboard','route'), ('settings','route'), ('account','route'),
  ('support','route'), ('help','route'), ('about','route'), ('pricing','route'),
  ('blog','route'), ('docs','route'), ('assets','route'), ('static','route'),
  ('public','route'), ('www','route'), ('app','route'), ('system','route'),
  ('security','route'), ('p','route'), ('u','route'), ('profile','route'),
  ('explore','route'), ('discover','route'), ('search','route'), ('feed','route'),
  ('notifications','route'), ('messages','route'), ('billing','route'),
  ('terms','route'), ('privacy','route'), ('legal','route'), ('contact','route'),
  ('status','route'), ('health','route'), ('cdn','route'), ('media','route'),
  ('files','route'), ('images','route'), ('img','route'), ('avatar','route'),
  ('folio','brand'), ('assetprim','brand'), ('official','brand'), ('team','brand'),
  ('mail','route'), ('email','route'), ('webhook','route'), ('webhooks','route'),
  ('oauth','route'), ('callback','route'), ('verify','route'), ('reset','route')
on conflict (name) do nothing;
