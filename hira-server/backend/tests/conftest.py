"""Fixtures compartidas de la suite de `hira-server/backend` (`pytest.ini`).

`services/rbac_service.py::_default_local_cache` (T-035, `plan.md §10`,
resolución de RNF-001) es un singleton de módulo — pensado para persistir
dentro del proceso real de producción (esa persistencia es exactamente lo que
resuelve RNF-001). Pero la misma persistencia lo vuelve un vector de
contaminación **entre tests** si distintos tests reutilizan el mismo `user_id`
(p. ej. `"user-1"`, convención ya establecida en varios archivos de esta suite:
`test_authentication_middleware.py`, `test_auth_router.py`) sin pasar un
`LocalPermissionsCache` explícito — que es exactamente el caso normal: código
de producción como `AuthenticationMiddleware` nunca pasa uno explícito, usa el
*default* a propósito (`resolve_permissions(claims.sub, ...)`, sin
`local_cache=`).

Este fixture `autouse` resetea el singleton a una instancia nueva antes de
**cada** test de la suite — sin esto, un test que puebla `"user-1"` con un
`rol`/`activo` concreto podría "filtrarse" a otro test que reutiliza el mismo
`user_id` con datos distintos, dando un resultado *cache-hit* local
incorrecto (falso positivo/negativo) sin que el test lo esté ejerciendo.

Los tests de `test_rbac_service.py` no dependen de este fixture (siempre pasan
`local_cache=` explícito, instancias frescas por test) — el reset es
puramente defensivo para el resto de la suite, que ejercita el singleton
*default* de forma indirecta a través del middleware/router reales.
"""
import pytest

import services.rbac_service as rbac_service_module


@pytest.fixture(autouse=True)
def _reset_default_local_permissions_cache():
    rbac_service_module._default_local_cache = rbac_service_module.LocalPermissionsCache()
    yield
