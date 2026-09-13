"""Hashing de contraseñas — RF-012 (`spec.md`).

Núcleo puro: sin I/O, sin `Settings()`, sin dependencia de FastAPI/`core/ports/`
(`plan.md §2`). `bcrypt` con factor 12 fijo — nunca se persiste texto plano.
"""
import bcrypt

BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    """Retorna el hash bcrypt (factor 12) de `password`.

    Cada llamada usa un salt aleatorio nuevo (`bcrypt.gensalt()`) — dos hashes
    del mismo password nunca son iguales en texto.
    """
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Retorna `True` si `password` corresponde a `password_hash` (bcrypt)."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
