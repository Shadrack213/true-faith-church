"""
Run the one-time Supabase setup for Django from this computer: no copying or pasting.

    backend\\.venv\\Scripts\\python backend\\sql\\run_supabase_setup.py            (read-only check)
    backend\\.venv\\Scripts\\python backend\\sql\\run_supabase_setup.py --apply    (make the change)

It asks for your Supabase DATABASE password (the one set when the project was
created; Supabase > Connect > "Reset database password" if you don't know it).
You type it in a hidden prompt; it is used once and never saved or shown.

Read-only check (default):
  - confirms the django_app password in backend/.env is in the right format
  - shows whether django_app / the django schema already exist
  - counts existing data (tables in public, Storage files, Auth users)
--apply:
  - runs supabase_django_setup.sql with the password's one-way hash filled in
    (all-or-nothing transaction), counts the existing data again and confirms
    it is unchanged, then logs in as django_app with the password from .env.
Nothing secret is ever printed.
"""
import argparse
import getpass
import os
import re
import sys
from pathlib import Path

import psycopg

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
PLACEHOLDER_LINE = "  verifier constant text := 'REPLACE_WITH_SCRAM_VERIFIER';"
sys.path.insert(0, str(HERE))
from make_password_verifier import scram_verifier  # noqa: E402

URL_RE = re.compile(r"postgresql://django_app\.([a-z0-9]+):([A-Za-z0-9]+)@([a-z0-9.-]+\.pooler\.supabase\.com):5432/postgres\?sslmode=require$")


def read_env_url():
    env = (BACKEND / ".env").read_text(encoding="utf-8")
    m = re.search(r"^DATABASE_URL=(.*)$", env, re.M)
    url = m.group(1).strip() if m else ""
    found = URL_RE.match(url)
    if not found:
        sys.exit("backend/.env has no DATABASE_URL in the expected form. Run prepare_supabase_setup.py first. Nothing was changed.")
    return found.groups()  # project_ref, django_app password, pooler host


def snapshot(conn):
    """Counts of existing data, read-only. Missing schemas count as None."""
    def one(sql):
        try:
            with conn.transaction():
                return conn.execute(sql).fetchone()[0]
        except psycopg.Error:
            return None
    tables = []
    try:
        with conn.transaction():
            tables = [r[0] for r in conn.execute(
                "select format('%I.%I', schemaname, tablename) from pg_tables where schemaname = 'public' order by 1")]
    except psycopg.Error:
        pass
    rows = sum(one(f"select count(*) from {t}") or 0 for t in tables)
    return {
        "tables in public": len(tables),
        "rows in public tables": rows,
        "Storage buckets": one("select count(*) from storage.buckets"),
        "Storage files": one("select count(*) from storage.objects"),
        "Auth users": one("select count(*) from auth.users"),
        "database roles": one("select count(*) from pg_roles where rolname <> 'django_app'"),
    }


def status(conn):
    return conn.execute("""
        select exists (select 1 from pg_roles where rolname = 'django_app'),
               exists (select 1 from pg_namespace where nspname = 'django')""").fetchone()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--apply", action="store_true", help="Run the setup (otherwise only a read-only check)")
    # Local testing only (a local PostgreSQL that imitates Supabase)
    p.add_argument("--test-host", help=argparse.SUPPRESS)
    p.add_argument("--test-port", help=argparse.SUPPRESS)
    p.add_argument("--test-db", help=argparse.SUPPRESS)
    p.add_argument("--test-admin", help=argparse.SUPPRESS)
    args = p.parse_args()

    ref, dj_password, pooler = read_env_url()
    print("backend/.env connection line: OK (django_app, session pooler, SSL required)")

    if args.test_host:
        admin_dsn = dict(host=args.test_host, port=args.test_port, dbname=args.test_db, user=args.test_admin)
        dj_dsn = dict(host=args.test_host, port=args.test_port, dbname=args.test_db, user="django_app")
    else:
        admin_dsn = dict(host=pooler, port=5432, dbname="postgres", user=f"postgres.{ref}", sslmode="require")
        dj_dsn = dict(host=pooler, port=5432, dbname="postgres", user=f"django_app.{ref}", sslmode="require")

    admin_password = os.environ.get("TFCI_ADMIN_PASSWORD_FOR_TESTS") if args.test_host else None
    if admin_password is None:
        admin_password = getpass.getpass("Supabase database password (hidden, not saved): ")
    try:
        conn = psycopg.connect(password=admin_password, connect_timeout=15, **admin_dsn)
    except psycopg.OperationalError as e:
        msg = str(e).lower()
        hint = ("The password was not accepted." if "password" in msg or "authentication" in msg
                else "Could not reach the database (check your internet connection).")
        sys.exit(f"{hint} Nothing was changed.")
    finally:
        admin_password = None
    conn.autocommit = True

    role_exists, schema_exists = status(conn)
    before = snapshot(conn)
    print(f"django_app login exists: {role_exists} | django schema exists: {schema_exists}")
    print("Existing data (read-only count):")
    for k, v in before.items():
        print(f"  {k}: {v if v is not None else 'n/a'}")

    if not args.apply:
        print("\nRead-only check finished. Nothing was changed.")
        return

    sql = (HERE / "supabase_django_setup.sql").read_text(encoding="utf-8").replace("\r\n", "\n")
    if sql.count(PLACEHOLDER_LINE) != 1:
        sys.exit("supabase_django_setup.sql is not in the expected form. Nothing was changed.")
    filled = sql.replace(PLACEHOLDER_LINE, f"  verifier constant text := '{scram_verifier(dj_password)}';")

    print("\nRunning the setup (all-or-nothing)...")
    try:
        cur = conn.execute(filled)
        row = None
        while True:
            try:
                row = cur.fetchone() or row
            except psycopg.ProgrammingError:
                pass
            if not cur.nextset():
                break
    except psycopg.Error as e:
        try:
            conn.execute("rollback")
        except psycopg.Error:
            pass
        first_line = str(e).splitlines()[0] if str(e) else type(e).__name__
        sys.exit(f"The setup stopped: {first_line}\nNothing was changed (the whole script is undone on any error).")
    filled = None

    expected = [True, True, False, False, False, ["search_path=django"]]
    print("Setup check row:", "as expected" if list(row) == expected else f"UNEXPECTED {list(row)}")

    after = snapshot(conn)
    unchanged = before == after
    print("Existing data unchanged:", unchanged)
    if not unchanged:
        for k in before:
            if before[k] != after[k]:
                print(f"  {k}: {before[k]} -> {after[k]}")
    conn.close()

    try:
        dj = psycopg.connect(password=dj_password, connect_timeout=15, **dj_dsn)
        who, path = dj.execute("select current_user, current_setting('search_path')").fetchone()
        dj.close()
        print(f"Django login test: OK (logged in as {who}, working area: {path})")
    except psycopg.Error as e:
        print("Django login test FAILED:", str(e).splitlines()[0])
        sys.exit(1)
    print("\nDone. Next step: Django migrations (ask before running them).")


if __name__ == "__main__":
    main()
