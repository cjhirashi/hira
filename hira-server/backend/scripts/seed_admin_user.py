"""`seed_admin_user.py` — único mecanismo de creación de usuarios de este sprint
(`SRV-002-auth-rbac`, T-026, `spec.md §2`: sin CRUD de usuarios más allá de esto).

Script standalone e **idempotente**: si `SEED_ADMIN_EMAIL` ya existe en `users`,
no falla, no reinserta, no sobreescribe el `password_hash` — solo informa y
termina en éxito (permite correr el mismo `docker compose exec` en cada
despliegue sin condicionales externos).

Lee `SEED_ADMIN_EMAIL`/`SEED_ADMIN_PASSWORD` de variables de entorno
(`.env.example`, sin valores reales) — hashea con
`core/security/passwords.py::hash_password` (bcrypt factor 12) antes de
insertar; el password en claro nunca se persiste ni se loguea. La conexión a
Postgres usa `core/config.py::Settings().database_url` (mismo origen que el
resto del backend) — este script se ejecuta dentro del contenedor `backend`
(con el `.env` real ya cargado), no contra `localhost` como los tests de
integración.

El usuario sembrado es `rol=admin`, `scope=global`, `project_id=None` — necesita
poder operar cualquier proyecto desde el primer login (`SRV-ADR-020`).

Uso:
    docker compose exec backend python -m scripts.seed_admin_user

Local (contra Postgres expuesto por `docker-compose.dev.yml`):
    cd hira-server/backend
    set -a && source ../.env && set +a
    python -m scripts.seed_admin_user
"""
import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from core.config import Settings
from core.security.passwords import hash_password
from models.user_model import users_table


async def seed_admin_user() -> int:
    """Retorna el código de salida del script (`0` éxito, `1` variables
    faltantes) — separado de `main()` para poder probarlo sin `sys.exit`."""
    settings = Settings()
    email = settings.seed_admin_email
    password = settings.seed_admin_password

    if not email or not password:
        print(
            "SEED_ADMIN_EMAIL/SEED_ADMIN_PASSWORD no están definidas — nada que "
            "sembrar.",
            file=sys.stderr,
        )
        return 1

    engine = create_async_engine(settings.database_url)
    try:
        async with engine.begin() as connection:
            existing = await connection.execute(
                select(users_table.c.id).where(users_table.c.email == email)
            )
            if existing.first() is not None:
                print(f"Usuario '{email}' ya existe — nada que hacer (idempotente).")
                return 0

            await connection.execute(
                users_table.insert().values(
                    email=email,
                    password_hash=hash_password(password),
                    rol="admin",
                    scope="global",
                    project_id=None,
                    activo=True,
                )
            )
        print(f"Usuario admin '{email}' creado.")
        return 0
    finally:
        await engine.dispose()


def main() -> None:
    sys.exit(asyncio.run(seed_admin_user()))


if __name__ == "__main__":
    main()
