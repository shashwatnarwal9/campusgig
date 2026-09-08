"""Password hashing and session token primitives.

Nothing in here logs or returns a secret. Callers get opaque strings back.
"""

import hashlib
import secrets
from functools import cache

import bcrypt

BCRYPT_ROUNDS = 12

# bcrypt rejects inputs longer than 72 bytes; request schemas cap password length
# to match so the limit is a validation error rather than a 500.
MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


@cache
def _dummy_hash() -> bytes:
    return bcrypt.hashpw(b"campusgig-timing-equaliser", bcrypt.gensalt(BCRYPT_ROUNDS))


def burn_password_cycles() -> None:
    """Spend the same time a real verify would, so a missing account and a wrong
    password are indistinguishable from the outside."""
    bcrypt.checkpw(b"campusgig-timing-equaliser", _dummy_hash())


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
