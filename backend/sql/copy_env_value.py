"""
Copy one value from backend/.env to the clipboard WITHOUT showing it,
so you can paste it into a hosting dashboard (e.g. Render's Environment page).

    backend\\.venv\\Scripts\\python backend\\sql\\copy_env_value.py DATABASE_URL

Only these names are allowed: DATABASE_URL, SUPABASE_S3_ACCESS_KEY_ID,
SUPABASE_S3_SECRET_ACCESS_KEY. Paste in the browser with Ctrl+V, then run
the helper again with --clear to empty the clipboard.
"""
import re
import subprocess
import sys
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
ALLOWED = {"DATABASE_URL", "SUPABASE_S3_ACCESS_KEY_ID", "SUPABASE_S3_SECRET_ACCESS_KEY"}


def set_clipboard(text):
    subprocess.run(["clip"], input=text.encode("ascii"), check=True)


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: copy_env_value.py NAME   (or --clear)")
    name = sys.argv[1]
    if name == "--clear":
        set_clipboard(" ")
        print("Clipboard cleared.")
        return
    if name not in ALLOWED:
        sys.exit(f"Only these can be copied: {', '.join(sorted(ALLOWED))}")
    text = ENV_FILE.read_bytes().decode("utf-8")
    m = re.search(rf"^{re.escape(name)}=(.*)$", text, re.M)
    value = m.group(1).strip() if m else ""
    if not value:
        sys.exit(f"{name} is empty in backend/.env. Nothing was copied.")
    set_clipboard(value)
    print(f"{name} copied to the clipboard ({len(value)} characters, not shown). Paste it with Ctrl+V.")


if __name__ == "__main__":
    main()
