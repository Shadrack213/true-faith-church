"""
Save the Supabase Storage S3 access key into backend/.env (git ignores that file),
then check that the key can reach the event-flyers bucket.

    backend\\.venv\\Scripts\\python backend\\sql\\save_storage_keys.py

Where the values come from: Supabase > Storage > S3 Configuration > "New access key".
Supabase shows the "Access key ID" and the "Secret access key" ONCE.

Typing / pasting in this terminal:
  - Both values are read in a hidden prompt: nothing appears while you paste. That's normal.
  - Paste with a RIGHT-CLICK (or Ctrl+Shift+V). Do NOT press Ctrl+C here: in a terminal
    Ctrl+C means "stop", and the helper will cancel without changing anything.
  - Only the number of characters received is shown, never the values.

If Supabase says "Unable to copy to clipboard":
  The browser panel inside the Claude app can't use your clipboard. Open
  https://supabase.com/dashboard in your normal browser (Chrome or Edge), go to
  Storage > S3 Configuration, and create the key there: its Copy buttons work.
  If the secret window was closed before you saved it, delete that key in Supabase
  and create a new one (an unsaved key can't be recovered).

Only SUPABASE_S3_ACCESS_KEY_ID and SUPABASE_S3_SECRET_ACCESS_KEY are changed in
backend/.env; every other line is kept exactly as it is.
"""
import getpass
import os
import re
import sys
import tempfile
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
KEYS = ("SUPABASE_S3_ACCESS_KEY_ID", "SUPABASE_S3_SECRET_ACCESS_KEY")
KEY_ID_RE = re.compile(r"[A-Za-z0-9]{16,128}")
SECRET_RE = re.compile(r"[A-Za-z0-9+/=_-]{20,256}")
ATTEMPTS = 3


class Cancelled(Exception):
    pass


def clean(value):
    """Remove spaces, line breaks and surrounding quotes that sneak in when pasting."""
    return value.strip().strip("'\"").strip()


def ask_hidden(label, pattern, hint):
    for attempt in range(1, ATTEMPTS + 1):
        try:
            value = clean(getpass.getpass(f"{label} (hidden, right-click to paste, then Enter): "))
        except (KeyboardInterrupt, EOFError):
            raise Cancelled
        if pattern.fullmatch(value):
            print(f"  received {len(value)} characters")
            return value
        reason = "nothing was received" if not value else f"{len(value)} characters received, {hint}"
        print(f"  That doesn't look right ({reason}). Try again ({attempt}/{ATTEMPTS}).")
    raise Cancelled


def env_value(text, key):
    m = re.search(rf"^{re.escape(key)}=(.*)$", text, re.M)
    return m.group(1).strip() if m else ""


def set_env_values(text, values):
    """Replace KEY=... lines (or add them), keeping every other line and the line endings."""
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines()
    for key, value in values.items():
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                break
        else:
            lines.append(f"{key}={value}")
    return newline.join(lines) + newline


def write_atomically(path, text):
    """Write to a temporary file next to .env, then swap it in, so .env is never left half-written."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".env.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def check_bucket(text, key_id, secret):
    """Read-only check: can this key see the event-flyers bucket? (lists at most 1 file)"""
    ref = env_value(text, "SUPABASE_PROJECT_REF")
    bucket = env_value(text, "SUPABASE_STORAGE_BUCKET") or "event-flyers"
    region = env_value(text, "SUPABASE_STORAGE_REGION") or "us-east-1"
    if not ref:
        return "skipped (SUPABASE_PROJECT_REF is not set)"
    try:
        import boto3
        from botocore.config import Config
        s3 = boto3.client(
            "s3", endpoint_url=f"https://{ref}.storage.supabase.co/storage/v1/s3", region_name=region,
            aws_access_key_id=key_id, aws_secret_access_key=secret,
            config=Config(s3={"addressing_style": "path"}, connect_timeout=10, read_timeout=15, retries={"max_attempts": 1}),
        )
        s3.list_objects_v2(Bucket=bucket, MaxKeys=1)
        return f"OK: the key can reach the '{bucket}' bucket"
    except Exception as e:  # noqa: BLE001 - report the kind of failure only
        code = getattr(e, "response", {}).get("Error", {}).get("Code") if hasattr(e, "response") else None
        return f"FAILED ({code or type(e).__name__}). Check that you pasted the newest key."


def main():
    if not ENV_FILE.exists():
        sys.exit("backend/.env is missing. Nothing was changed.")
    text = ENV_FILE.read_bytes().decode("utf-8")  # exact bytes, so line endings are kept

    print("Paste with a RIGHT-CLICK (or Ctrl+Shift+V). Don't press Ctrl+C: it cancels.\n")
    try:
        if all(env_value(text, k) for k in KEYS):
            answer = input("backend/.env already has a storage key. Replace it? [y/N]: ").strip().lower()
            if answer != "y":
                print("Kept the existing key. Nothing was changed.")
                return
        key_id = ask_hidden("Access key ID", KEY_ID_RE, "expected letters and numbers only (usually 32)")
        secret = ask_hidden("Secret access key", SECRET_RE, "expected a long code (usually 64 characters)")
    except Cancelled:
        print("\nCancelled. backend/.env was not changed.")
        sys.exit(1)

    if key_id == secret:
        print("The two values are identical, so one was pasted twice. backend/.env was not changed.")
        sys.exit(1)

    write_atomically(ENV_FILE, set_env_values(text, dict(zip(KEYS, (key_id, secret)))))
    print("\nSaved both values in backend/.env (not shown). Other settings were left as they were.")
    print("Checking the key (read-only)...", check_bucket(text, key_id, secret))
    print("Restart Django to start using it.")


if __name__ == "__main__":
    main()
