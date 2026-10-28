"""
Turn the django_app password into a PostgreSQL SCRAM-SHA-256 verifier
(a one-way hash) for backend/sql/supabase_django_setup.sql.

    python backend/sql/make_password_verifier.py

You type the password twice (it is not shown on screen). The script prints
only the verifier, which you paste in place of REPLACE_WITH_SCRAM_VERIFIER.
The real password then goes ONLY in backend/.env (inside DATABASE_URL).

Use letters and numbers only (no symbols), at least 32 characters, so it
works unchanged inside DATABASE_URL.
Nothing is sent anywhere and nothing is saved.
"""
import base64
import getpass
import hashlib
import hmac
import os
import sys

ITERATIONS = 4096  # PostgreSQL's default for SCRAM-SHA-256


def scram_verifier(password: str) -> str:
    salt = os.urandom(16)
    salted = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    client_key = hmac.new(salted, b"Client Key", hashlib.sha256).digest()
    stored_key = hashlib.sha256(client_key).digest()
    server_key = hmac.new(salted, b"Server Key", hashlib.sha256).digest()
    b64 = lambda b: base64.b64encode(b).decode("ascii")
    return f"SCRAM-SHA-256${ITERATIONS}:{b64(salt)}${b64(stored_key)}:{b64(server_key)}"


def main():
    password = getpass.getpass("django_app password (hidden): ")
    if getpass.getpass("Type it again: ") != password:
        sys.exit("The two passwords do not match. Nothing was printed.")
    if len(password) < 32 or not password.isascii() or not password.isalnum():
        sys.exit("Use at least 32 characters, letters and numbers only. Nothing was printed.")
    print()
    print("Paste this in place of REPLACE_WITH_SCRAM_VERIFIER (keep the single quotes around it):")
    print(scram_verifier(password))


if __name__ == "__main__":
    main()
