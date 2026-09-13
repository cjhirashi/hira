"""`POST /auth/login|refresh|logout` — adaptador de entrada HTTP (`SRV-002-auth-rbac`).

Contrato: `hira-server/docs/openapi.yaml#/paths/~1auth~1login` (+ `~1auth~1refresh`,
`~1auth~1logout`), escrito antes que este router (`tasks.md` T-016, Contract-First).

Inyecta `UserRepositoryPort`/`CachePort` vía `Depends(adapters.factory.*)` — nunca
instancia un adaptador concreto (`SRV-ADR-017`), mismo patrón que
`routers/monitor.py`. Delega toda la lógica de negocio a
`services/auth_service.py` — este router solo traduce HTTP <-> servicio y lee
`Settings().secret_key` para pasarlo explícito (`services/` no lee `Settings()`
internamente).

`POST /auth/logout` no valida autenticación aquí — la exige
`AuthenticationMiddleware` (`core/middleware.py`, T-019/T-020), que no está en el
*allowlist* público para esta ruta (a diferencia de `/auth/login`/`/auth/refresh`).
"""
from fastapi import APIRouter, Depends, Request, Response, status

from adapters.factory import get_cache_port, get_user_repository_port
from core.config import Settings
from core.ports.cache_port import CachePort
from core.ports.user_repository_port import UserRepositoryPort
from schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    users_repo: UserRepositoryPort = Depends(get_user_repository_port),
    cache: CachePort = Depends(get_cache_port),
) -> TokenResponse:
    """RF-001, RF-002, RF-014 — expone `services/auth_service.py::login` vía HTTP."""
    ip = request.client.host if request.client else "unknown"
    token_pair = await auth_service.login(
        payload.email,
        payload.password,
        ip,
        users_repo,
        cache,
        Settings().secret_key,
    )
    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    payload: RefreshRequest,
    users_repo: UserRepositoryPort = Depends(get_user_repository_port),
    cache: CachePort = Depends(get_cache_port),
) -> AccessTokenResponse:
    """RF-011, RF-013 — expone `services/auth_service.py::refresh` vía HTTP."""
    access_token = await auth_service.refresh(
        payload.refresh_token, cache, users_repo, Settings().secret_key
    )
    return AccessTokenResponse(access_token=access_token, token_type="bearer")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshRequest,
    cache: CachePort = Depends(get_cache_port),
) -> Response:
    """RF-010 — expone `services/auth_service.py::logout` vía HTTP.

    Requiere estar autenticado (`AuthenticationMiddleware`) — cierra su propia
    sesión; sin eso el 204 sería devuelto también a un cliente no autenticado.
    """
    await auth_service.logout(payload.refresh_token, cache, Settings().secret_key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
