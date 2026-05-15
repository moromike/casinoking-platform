import argparse
import os
import sys

from app.modules.auth.service import AuthValidationError, ensure_local_admin

DEFAULT_LOCAL_ADMIN_EMAIL = "codex.agent@example.com"
PROTECTED_HUMAN_ADMIN_EMAIL = "admin@example.com"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create or promote the technical local CasinoKing admin user. "
            "Do not use this tool for human/local user accounts."
        )
    )
    parser.add_argument(
        "--email",
        default=os.getenv("LOCAL_ADMIN_EMAIL", DEFAULT_LOCAL_ADMIN_EMAIL),
        help=(
            "Technical admin email. Defaults to LOCAL_ADMIN_EMAIL or "
            f"{DEFAULT_LOCAL_ADMIN_EMAIL}."
        ),
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
    if args.email.strip().lower() == PROTECTED_HUMAN_ADMIN_EMAIL:
        parser.error(
            f"{PROTECTED_HUMAN_ADMIN_EMAIL} is a protected human/local account; "
            f"use {DEFAULT_LOCAL_ADMIN_EMAIL} for technical smoke tests"
        )

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
