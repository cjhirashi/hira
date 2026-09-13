"""Request/response Pydantic de `POST /auth/login|refresh|logout` (`SRV-002-auth-rbac`).

Traducción exacta de `hira-server/docs/openapi.yaml#/components/schemas`
(Contract-First, `tasks.md` T-016, escrito antes que este módulo) — no se
introduce ningún campo que el contrato no declare.
"""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Body de `POST /auth/login` (RF-001, RF-002, RF-014)."""

    email: str
    password: str


class TokenResponse(BaseModel):
    """Respuesta 200 de `POST /auth/login` — par de tokens (RF-001)."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Body común de `POST /auth/refresh` y `POST /auth/logout`."""

    refresh_token: str


class AccessTokenResponse(BaseModel):
    """Respuesta 200 de `POST /auth/refresh` — nuevo access token (RF-011)."""

    access_token: str
    token_type: str = "bearer"
