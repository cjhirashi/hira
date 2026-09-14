"""Configuración de arranque — RF-003 (`spec.md`).

`Settings` valida las variables de entorno requeridas al construirse
(`Settings()`), no en el primer acceso perezoso a un campo: si falta alguna,
`pydantic.ValidationError` nombra explícitamente el/los campo(s) faltante(s) —
sin arranque parcial.

Variables de este sprint (`HUB-001-walking-skeleton`, `plan.md §2`): solo las
de infraestructura que este walking skeleton consume de verdad
(`DATABASE_URL`, `POSTGRES_*`, `REDIS_URL`, `REDIS_PASSWORD`, `ENVIRONMENT`,
`LOG_LEVEL`) — **sin** `SECRET_KEY` ni `ADMIN_PASSWORD_HASH` (`VUL-HUB-03`),
que pertenecen al Panel Admin de H1 y no tienen consumidor real todavía
(Constitución Art. 10, no anticipar).

Perfil único (cloud single-tenant) — sin `HIRA_DEPLOY_MODE` (ese concepto ni
existe en Hub).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables de entorno requeridas por el Walking Skeleton de Hira Hub."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    database_url: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    redis_url: str
    redis_password: str
    environment: str
    log_level: str
