from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import secrets

import jwt

from app.core.config import settings

PBKDF2_ITERATIONS = 600_000
PBKDF2_ALGORITHM = "sha256"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    derived_key = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return (
        f"pbkdf2_{PBKDF2_ALGORITHM}$"
        f"{PBKDF2_ITERATIONS}$"
        f"{salt}$"
        f"{derived_key.hex()}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    algorithm, iterations, salt, digest = stored_hash.split("$", maxsplit=3)
    if algorithm != f"pbkdf2_{PBKDF2_ALGORITHM}":
        return False

    derived_key = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    )
    return hmac.compare_digest(derived_key.hex(), digest)


def create_password_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_password_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(*, user_id: str, role: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_token_ttl_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
