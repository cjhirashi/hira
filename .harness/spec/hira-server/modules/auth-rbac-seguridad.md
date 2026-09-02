---
origen_vault: "7.1 - Hira Server/7.1.5 - Diseño por Módulo/7.1.5.4 - Autenticación, RBAC y Seguridad.md"
título: Autenticación, RBAC y Seguridad — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Diseño por Módulo
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, autenticación, rbac, seguridad]
---

## Autenticación y Autorización

- JWT con firma HS256, access token de corta duración (15 min), refresh token (7 días) almacenado en Redis con posibilidad de revocación
- RBAC evaluado en cada request — middleware en FastAPI, con caché de permisos en Redis (`rbac:{user_id}`, TTL igual al refresh token) para no consultar la base de datos en cada request
- Al modificar un rol, se invalida la entrada Redis del usuario afectado
- Alcance de roles (ver SRV-ADR-020): roles de operación (Operador, Visor, roles de instalación) son `scope=project` — el usuario solo actúa dentro de un proyecto. Roles de integrador son `scope=global` — el usuario accede a todos los proyectos de la instancia
- Superusuario es el único que puede modificar roles y permisos

## Ejecución de scripts Python

- **RestrictedPython** como sandbox — los scripts (lógica y pruebas) solo tienen acceso al objeto `hira` (API interna: `read`, `write`, `subscribe`, `wait`)
- Sin acceso a filesystem, red, subprocess ni imports arbitrarios
- Recursos limitados por worker de Celery (memoria, tiempo de ejecución)
- Toda escritura a un punto pasa por RBAC y por el `access_mode` de la asociación del punto (ver SRV-ADR-019) — un script no puede escribir un punto `read`-only ni un punto candidato sin asociar

## Datos sensibles

- API keys de IA cifradas en base de datos con clave de entorno (`AI_ENCRYPTION_KEY`)
- License key almacenada como hash — nunca en texto plano
- Passwords con bcrypt (factor 12)
- Secrets nunca en código ni en repositorio

## Red

- Nginx como único punto de entrada externo
- Backend y base de datos no exponen puertos fuera de la red Docker
- CORS configurado explícitamente
- Mosquitto sin conexiones anónimas — `allow_anonymous false` + `password_file`, credenciales vía `MQTT_USER`/`MQTT_PASSWORD`
- Rate limiting en Nginx: `limit_req_zone` por IP para REST (100 req/s), `limit_conn_zone` para WebSocket (10 conexiones/IP)

## Backup y portabilidad

- El paquete `.hira` nunca contiene SQL ejecutable — se serializa como JSON estructurado por el ORM y se importa con queries parametrizadas y validación de esquema Pydantic antes de tocar la base de datos
- Ver `.harness/spec/hira-server/modules/backup-y-portabilidad.md` para el formato completo del paquete

## Variables de entorno requeridas

```
DATABASE_URL          # PostgreSQL o SQLite connection string
REDIS_URL             # Redis connection string
SECRET_KEY            # JWT signing key
LICENSE_KEY           # License key de la instalación
CORS_ORIGINS          # Orígenes permitidos para el frontend
MQTT_BROKER_HOST      # Host de Mosquitto
AI_ENCRYPTION_KEY     # Clave para cifrar API keys de IA en BD
```

---

## Gate de Salida

- [x] Estrategia de autenticación y RBAC definida, con alcance por proyecto/global (SRV-ADR-020)
- [x] Sandboxing de scripts documentado
- [x] Reglas de red y rate limiting documentadas
- [ ] Revisado y aprobado por Charlie
