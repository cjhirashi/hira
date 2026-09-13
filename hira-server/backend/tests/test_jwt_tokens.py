"""Núcleo — tokens JWT (access/refresh). Sin I/O, sin mocks, `PyJWT` real.

Cubre RF-001 (TTL de access/refresh), RF-003 (rechazo de token expirado/inválido
en rutas protegidas), RF-011 (refresh emite nuevo access), RF-013 (rechazo de
refresh vencido/inválido) — `spec.md`.
"""
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from core.security.jwt import (
    ACCESS_TOKEN_TTL_MINUTES,
    REFRESH_TOKEN_TTL_DAYS,
    TokenExpiredError,
    TokenInvalidError,
    create_access_token,
    create_refresh_token,
    decode_token,
)

SECRET_KEY = "test-secret-key-no-usar-en-produccion"
USER_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
JTI = "b0e1c2d3-1111-2222-3333-444455556666"


def test_create_access_token_ttl_15_minutos():
    token = create_access_token(
        user_id=USER_ID, rol="admin", scope="global", project_id=None, secret_key=SECRET_KEY
    )

    claims = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    ttl_seconds = claims["exp"] - claims["iat"]

    assert ttl_seconds == ACCESS_TOKEN_TTL_MINUTES * 60
    assert claims["type"] == "access"
    assert claims["sub"] == USER_ID
    assert claims["rol"] == "admin"
    assert claims["scope"] == "global"
    assert claims["project_id"] is None


def test_create_refresh_token_ttl_7_dias():
    token = create_refresh_token(user_id=USER_ID, jti=JTI, secret_key=SECRET_KEY)

    claims = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    ttl_seconds = claims["exp"] - claims["iat"]

    assert ttl_seconds == REFRESH_TOKEN_TTL_DAYS * 24 * 60 * 60
    assert claims["type"] == "refresh"
    assert claims["sub"] == USER_ID
    assert claims["jti"] == JTI


def test_decode_token_access_valido_retorna_claims():
    token = create_access_token(
        user_id=USER_ID, rol="operador", scope="project", project_id="proj-1", secret_key=SECRET_KEY
    )

    claims = decode_token(token, expected_type="access", secret_key=SECRET_KEY)

    assert claims.sub == USER_ID
    assert claims.rol == "operador"
    assert claims.scope == "project"
    assert claims.project_id == "proj-1"
    assert claims.type == "access"


def test_decode_token_refresh_valido_retorna_claims():
    token = create_refresh_token(user_id=USER_ID, jti=JTI, secret_key=SECRET_KEY)

    claims = decode_token(token, expected_type="refresh", secret_key=SECRET_KEY)

    assert claims.sub == USER_ID
    assert claims.jti == JTI
    assert claims.type == "refresh"


def test_decode_token_expirado_lanza_token_expired_error():
    # `exp` fijado manualmente en el pasado — sin `time.sleep`.
    now = datetime.now(timezone.utc)
    payload = {
        "sub": USER_ID,
        "rol": "admin",
        "scope": "global",
        "project_id": None,
        "type": "access",
        "iat": now - timedelta(minutes=20),
        "exp": now - timedelta(minutes=5),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    with pytest.raises(TokenExpiredError):
        decode_token(token, expected_type="access", secret_key=SECRET_KEY)


def test_decode_token_firma_alterada_lanza_token_invalid_error():
    token = create_access_token(
        user_id=USER_ID, rol="admin", scope="global", project_id=None, secret_key=SECRET_KEY
    )

    with pytest.raises(TokenInvalidError):
        decode_token(token, expected_type="access", secret_key="otra-secret-key-distinta")


def test_decode_token_type_incorrecto_lanza_token_invalid_error():
    # Un refresh token no debe pasar como si fuera un access token.
    token = create_refresh_token(user_id=USER_ID, jti=JTI, secret_key=SECRET_KEY)

    with pytest.raises(TokenInvalidError):
        decode_token(token, expected_type="access", secret_key=SECRET_KEY)


def test_decode_token_malformado_lanza_token_invalid_error():
    with pytest.raises(TokenInvalidError):
        decode_token("esto-no-es-un-jwt", expected_type="access", secret_key=SECRET_KEY)
