"""Configuración de arranque — RF-003 (`spec.md`).

`Settings` valida las variables de entorno requeridas al construirse
(`Settings()`), no en el primer acceso perezoso a un campo: si falta alguna,
`pydantic.ValidationError` nombra explícitamente el/los campo(s) faltante(s) —
sin arranque parcial.

Perfil único (PostgreSQL + TimescaleDB) — sin `HIRA_DEPLOY_MODE` (`E-ADR-001`,
retirado; no reintroducir).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables de entorno requeridas por el Walking Skeleton (`AC-SRV-01`)."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    database_url: str
    redis_url: str
    mqtt_broker_host: str
    mqtt_user: str
    mqtt_password: str
    secret_key: str
    cors_origins: str
    environment: str = "development"
    log_level: str = "INFO"

    # `SRV-002-auth-rbac`, T-026 — únicamente usadas por
    # `scripts/seed_admin_user.py`; opcionales aquí (default `None`) porque el
    # resto del backend arranca sin necesitar sembrar un usuario en cada
    # despliegue (el script ya valida por su cuenta que ambas estén presentes
    # antes de sembrar).
    seed_admin_email: str | None = None
    seed_admin_password: str | None = None

    # `SRV-003-bacnet-adapter` (`plan.md §0`/§1, Registro de decisiones) —
    # opcionales: `BAC0.lite(ip=None)` autodetecta la interfaz/IP local del
    # host (comportamiento correcto para un solo NIC on-premise, Art. 10 — no
    # anticipar una variable de entorno obligatoria sin caso de uso real de
    # multi-NIC). Fijarlas es un ajuste operativo excepcional.
    bacnet_ip: str | None = None
    bacnet_port: int | None = None

    # `SRV-006-simuladores` (`plan.md §2`) — primer puerto UDP del rango
    # efímero de los simuladores BACnet; distinto de `bacnet_port` (cliente de
    # escaneo) para no colisionar con él.
    bacnet_simulator_port_range_start: int = 47900
