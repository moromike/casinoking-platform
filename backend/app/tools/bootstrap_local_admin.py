import argparse
import os
import sys

from app.modules.auth.service import AuthValidationError, ensure_local_admin


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or promote a local CasinoKing admin user."
    )
    parser.add_argument(
        "--email",
        default=os.getenv("LOCAL_ADMIN_EMAIL"),
        help="Admin email. Falls back to LOCAL_ADMIN_EMAIL if present.",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("LOCAL_ADMIN_PASSWORD"),
        help="Admin password. Falls back to LOCAL_ADMIN_PASSWORD if present.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.email or not args.password:
        parser.error("email and password are required")

    try:
        result = ensure_local_admin(email=args.email, password=args.password)
    except AuthValidationError as exc:
        print(f"Admin bootstrap failed: {exc}", file=sys.stderr)
        return 1

    mode = "created" if result["created"] else "promoted"
    password_note = "reset" if result["password_reset"] else "kept"
    print(
        "Local admin ready:"
        f" email={result['email']}"
        f" user_id={result['user_id']}"
        f" role={result['role']}"
        f" mode={mode}"
        f" password={password_note}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
