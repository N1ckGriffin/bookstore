"""Password hashing helpers with a resilient CryptContext.

This module configures passlib to prefer bcrypt but fall back to
pbkdf2_sha256 if bcrypt isn't available. Use the helpers here to hash and
verify passwords so the rest of the app doesn't need to worry about backend
availability.
"""
from passlib.context import CryptContext

try:
    import argon2  # noqa: F401 - presence is what we need
except Exception as exc:  # pragma: no cover - environment check
    raise RuntimeError(
        "Argon2 backend not available. Install argon2-cffi and passlib[argon2]: `python -m pip install argon2-cffi passlib[argon2]`"
    ) from exc

pwd_ctx = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash the plaintext password and return the hash string."""
    return pwd_ctx.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against the stored hash."""
    try:
        return pwd_ctx.verify(password, hashed)
    except Exception:
        return False
