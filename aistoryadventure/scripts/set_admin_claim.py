from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import initializes Firebase Admin through the app's existing settings.
import app.auth.firebase_auth  # noqa: F401
from firebase_admin import auth

DEFAULT_ADMIN_EMAIL = "caoban170106@gmail.com"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Grant Firebase custom claim admin=true to a user email."
    )
    parser.add_argument(
        "--email",
        default=DEFAULT_ADMIN_EMAIL,
        help=f"Firebase user email to promote. Default: {DEFAULT_ADMIN_EMAIL}",
    )
    parser.add_argument(
        "--revoke-refresh-tokens",
        action="store_true",
        help="Force existing sessions to refresh by revoking refresh tokens.",
    )
    args = parser.parse_args()

    email = args.email.strip().lower()
    if not email:
        raise SystemExit("Email is required.")

    user = auth.get_user_by_email(email)
    claims = dict(user.custom_claims or {})
    claims["admin"] = True

    auth.set_custom_user_claims(user.uid, claims)

    if args.revoke_refresh_tokens:
        auth.revoke_refresh_tokens(user.uid)

    print(f"Admin claim set for {email}")
    print(f"UID: {user.uid}")
    print("Sign out and sign in again so the browser receives a fresh ID token.")


if __name__ == "__main__":
    main()
