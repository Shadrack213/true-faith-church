-- =====================================================================
-- One-time setup of the Supabase database for Django
-- Run in Supabase: SQL Editor -> New query -> paste -> Run.
--
-- Creates (and changes nothing else):
--   * schema "django"   : an empty area where ALL Django tables will live
--   * role "django_app" : the only login Django uses (not the postgres user)
--
-- Why a separate schema: Supabase publishes the "public" schema through its
-- Data API to anyone holding the publishable key. The "django" schema is not
-- published and the API roles get no access to it, so Django's tables
-- (including user password hashes) can never be read through that API.
-- Visitors only get data through Django's /api/.
--
-- It does NOT touch: existing tables in "public", Storage (event flyers),
-- Supabase Auth users, or any existing role other than django_app.
-- It contains no DROP, DELETE, TRUNCATE or UPDATE statements.
-- Safe to run again: an existing django_app keeps its password.
--
-- BEFORE RUNNING: replace  REPLACE_WITH_SCRAM_VERIFIER  below with the line
-- printed by:   python backend/sql/make_password_verifier.py
-- That is a one-way hash of your django_app password, so the password itself
-- is never sent to Supabase or kept in its query history or logs.
-- Do not save this file with the value filled in, and never commit it.
-- =====================================================================

begin;

create schema if not exists django;

do $setup$
declare
  verifier constant text := 'REPLACE_WITH_SCRAM_VERIFIER';
begin
  if not exists (select 1 from pg_roles where rolname = 'django_app') then
    if verifier !~ '^SCRAM-SHA-256\$4096:[A-Za-z0-9+/=]+\$[A-Za-z0-9+/=]+:[A-Za-z0-9+/=]+$' then
      raise exception 'Replace REPLACE_WITH_SCRAM_VERIFIER with the output of make_password_verifier.py first. Nothing was changed.';
    end if;
    execute format(
      'create role django_app with login nosuperuser nocreatedb nocreaterole noreplication '
      'connection limit 20 password %L', verifier);
    raise notice 'Created role django_app.';
  else
    -- Leave the existing role and its password alone, but stop if it has more power than Django needs
    if exists (select 1 from pg_roles where rolname = 'django_app'
               and (rolsuper or rolcreaterole or rolcreatedb or rolreplication or rolbypassrls or not rolcanlogin)) then
      raise exception 'Role django_app already exists with unexpected settings (superuser/createrole/createdb/replication/bypassrls or no login). Nothing was changed; ask for help before continuing.';
    end if;
    raise notice 'Role django_app already exists: its password was NOT changed.';
  end if;
end
$setup$;

-- Django may create and manage tables only in its own schema
grant usage, create on schema django to django_app;
-- Every Django connection works inside "django" (no need to set it in DATABASE_URL)
alter role django_app set search_path = django;

-- Make sure the Supabase API roles cannot reach Django's schema
revoke all on schema django from public;
do $revoke$
declare
  r text;
begin
  foreach r in array array['anon', 'authenticated', 'service_role'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      execute format('revoke all on schema django from %I', r);
    end if;
  end loop;
end
$revoke$;

commit;

-- Check (read-only). Expected: true, true, false, false, false, {search_path=django}
select
  has_schema_privilege('django_app', 'django', 'usage')                 as django_usage,
  has_schema_privilege('django_app', 'django', 'create')                as django_create,
  (select rolsuper from pg_roles where rolname = 'django_app')          as is_superuser,
  has_schema_privilege('anon', 'django', 'usage')                       as anon_can_see_django,
  has_schema_privilege('authenticated', 'django', 'usage')              as authenticated_can_see_django,
  (select setconfig from pg_db_role_setting s join pg_roles r on r.oid = s.setrole
    where r.rolname = 'django_app' and s.setdatabase = 0)               as role_settings;
