"""Tokens JWT (access/refresh) — RF-001, RF-003, RF-011, RF-013 (`spec.md`).

Núcleo puro: `HS256`, recibe `secret_key` como parámetro explícito — nunca lee
`Settings()` internamente (mantiene el módulo sin I/O, `plan.md §2`). No depende
de FastAPI; `TokenExpiredError`/`TokenInvalidError` se definen aquí.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt

ALGORITHM = "HS256"
ACCESS_TOKEN_TTL_MINUTES = 15
REFRESH_TOKEN_TTL_DAYS = 7

TokenType = Literal["access", "refresh"]


class TokenExpiredError(Exception):
    """El JWT es válido en firma/forma pero su `exp` ya venció."""


class TokenInvalidError(Exception):
    """El JWT está malformado, tiene firma inválida, o `type` no coincide."""


@dataclass(frozen=True)
class TokenClaims:
    """Claims decodificados de un JWT de este dominio (access o refresh)."""

    sub: str
    type: TokenType
    rol: str | None = None
    scope: str | None = None
    project_id: str | None = None
    jti: str | None = None


def create_access_token(
    user_id: str, rol: str, scope: str, project_id: str | None, secret_key: str
) -> str:
    """Emite un JWT access (`type=access`, `exp` = 15 min) — RF-001."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "rol": rol,
        "scope": scope,
        "project_id": project_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_TTL_MINUTES),
    }
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def create_refresh_token(user_id: str, jti: str, secret_key: str) -> str:
    """Emite un JWT refresh (`type=refresh`, `exp` = 7 días) — RF-001."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "jti": jti,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_TTL_DAYS),
    }
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def decode_token(token: str, expected_type: TokenType, secret_key: str) -> TokenClaims:
    """Decodifica y valida `token` — RF-003, RF-011, RF-013.

    Lanza `TokenExpiredError` si `exp` venció, `TokenInvalidError` si la firma es
    inválida, el token está malformado, o `type` no coincide con `expected_type`.
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError("El token JWT expiró") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenInvalidError("El token JWT es inválido") from exc

    if payload.get("type") != expected_type:
        raise TokenInvalidError(
            f"Se esperaba un token de tipo '{expected_type}', se recibió "
            f"'{payload.get('type')}'"
        )

    return TokenClaims(
        sub=payload["sub"],
        type=payload["type"],
        rol=payload.get("rol"),
        scope=payload.get("scope"),
        project_id=payload.get("project_id"),
        jti=payload.get("jti"),
    )
