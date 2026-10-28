"""
Prepare the one-time Supabase setup for Django, without anyone having to
handle a password by hand.

    backend\\.venv\\Scripts\\python backend\\sql\\prepare_supabase_setup.py

What it does (all on this computer; it never connects to Supabase):
  1. Creates a strong random password for the django_app database login
     (40 letters and numbers). It is never printed.
  2. Saves the connection line (DATABASE_URL) with that password in
     backend/.env, which git ignores.
  3. Copies supabase_django_setup.sql to the clipboard with the password's
     one-way hash (SCRAM verifier) already filled in, ready to paste into
     Supabase's SQL Editor. The file on disk is not changed.

It refuses to replace an existing DATABASE_URL (so a working connection is
never overwritten) unless you add --replace.
"""
import argparse
import re
import secrets
import string
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
ENV_FILE = BACKEND / ".env"
SQL_FILE = HERE / "supabase_django_setup.sql"
PLACEHOLDER_LINE = "  verifier constant text := 'REPLACE_WITH_SCRAM_VERIFIER';"

sys.path.insert(0, str(HERE))
from make_password_verifier import scram_verifier  # noqa: E402


def set_env_values(text, values):
    """Replace KEY=... lines (or append them), keeping every other line as it is."""
    lines = text.splitlines()
    for key, value in values.items():
        pattern = re.compile(rf"^{re.escape(key)}=")
        for i, line in enumerate(lines):
            if pattern.match(line):
                lines[i] = f"{key}={value}"
                break
        else:
            lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"


def copy_to_clipboard(text):
    # clip.exe ships with Windows; the SQL is plain ASCII
    subprocess.run(["clip"], input=text.encode("ascii"), check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project-ref", required=True, help="Supabase project reference, e.g. abcdefghijklmnop")
    parser.add_argument("--pooler-host", required=True, help="Session pooler host from Supabase > Connect")
    parser.add_argument("--region", default="", help="Project region for Storage, e.g. eu-west-3")
    parser.add_argument("--replace", action="store_true", help="Replace an existing DATABASE_URL in backend/.env")
    args = parser.parse_args()

    if not re.fullmatch(r"[a-z0-9]{10,40}", args.project_ref):
        sys.exit("The project reference looks wrong. Nothing was changed.")
    if not re.fullmatch(r"[a-z0-9.-]+\.pooler\.supabase\.com", args.pooler_host):
        sys.exit("The pooler host should end in .pooler.supabase.com. Nothing was changed.")
    if not ENV_FILE.exists():
        sys.exit("backend/.env is missing. Copy backend/.env.example to backend/.env first. Nothing was changed.")

    env_text = ENV_FILE.read_text(encoding="utf-8")
    current = re.search(r"^DATABASE_URL=(.*)$", env_text, re.M)
    if current and current.group(1).strip() and not args.replace:
        sys.exit("backend/.env already has a DATABASE_URL. Re-run with --replace only if you are sure. Nothing was changed.")

    sql = SQL_FILE.read_text(encoding="utf-8").replace("\r\n", "\n")
    if sql.count(PLACEHOLDER_LINE) != 1:
        sys.exit("supabase_django_setup.sql does not contain the expected placeholder line. Nothing was changed.")

    password = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(40))
    filled_sql = sql.replace(PLACEHOLDER_LINE, f"  verifier constant text := '{scram_verifier(password)}';")

    database_url = (f"postgresql://django_app.{args.project_ref}:{password}"
                    f"@{args.pooler_host}:5432/postgres?sslmode=require")
    values = {"DATABASE_URL": database_url, "SUPABASE_PROJECT_REF": args.project_ref}
    if args.region:
        values["SUPABASE_STORAGE_REGION"] = args.region

    copy_to_clipboard(filled_sql)
    ENV_FILE.write_text(set_env_values(env_text, values), encoding="utf-8")

    print("Done. Nothing was sent to Supabase.")
    print("  - A new django_app password was created and saved in backend/.env (not shown).")
    print("  - The setup SQL, with the password's one-way hash filled in, is on your clipboard.")
    print("Next: in Supabase SQL Editor, click in the editor, press Ctrl+A then Ctrl+V, then click Run.")


if __name__ == "__main__":
    main()
