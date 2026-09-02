---
origen_vault: "7.2 - Hira Hub/7.2.8 - Despliegue.md"
título: Despliegue — Hira Hub
proyecto: Hira Hub
dominio: Productos de Software
fase: 08 — Despliegue
fecha_creación: 2026-07-24
última_actualización: 2026-07-24
tipo: Documento de Proyecto
status: pendiente
github: ""
tags: [proyecto, productos-software, hira-hub, despliegue]
ecosistema: Hira
relacionado_con: 7.1 - ÍNDICE - Hira
---

## Infraestructura

| Componente | Especificación |
|---|---|
| VPS | Mínimo 2 vCPU / 4 GB RAM / 40 GB SSD |
| Proveedor | Hetzner Cloud o DigitalOcean (Ubuntu 22.04 LTS) |
| Dominio | `hub.hira.cjhirashi.com` |
| SSL | Let's Encrypt via Certbot (renovación automática) |
| Costo estimado | $5–15/mes según proveedor |

---

## Arquitectura del VPS

```
VPS — hub.hira.cjhirashi.com
│
├── Nginx :80 (redirect a HTTPS)
├── Nginx :443 (TLS termination → proxy a backend)
│
├── Hub Backend (FastAPI)  :8001  [contenedor Docker]
├── PostgreSQL             :5432  [contenedor Docker, solo LAN interna]
└── Redis                  :6379  [contenedor Docker, solo LAN interna]
```

PostgreSQL y Redis NO están expuestos al exterior — solo accesibles dentro de la red Docker.

---

## Primer Despliegue (desde cero)

```bash
# 1. Preparar el servidor
apt update && apt upgrade -y
apt install -y docker.io docker-compose-plugin git certbot python3-certbot-nginx

# 2. Clonar repositorio
cd /opt
git clone https://github.com/cjhirashi/hira-hub.git
cd hira-hub

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con los valores reales:
# - POSTGRES_PASSWORD
# - REDIS_PASSWORD
# - SECRET_KEY (openssl rand -hex 32)
# - ADMIN_PASSWORD_HASH (generar con Python: bcrypt.hashpw(b"password", bcrypt.gensalt()).decode())

# 4. Obtener certificado SSL
certbot certonly --nginx -d hub.hira.cjhirashi.com --email cjhirashi@gmail.com --agree-tos

# 5. Activar configuración Nginx
cp nginx/hub.conf /etc/nginx/sites-available/hub
ln -s /etc/nginx/sites-available/hub /etc/nginx/sites-enabled/hub
nginx -t && systemctl reload nginx

# 6. Levantar contenedores
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 7. Verificar
curl https://hub.hira.cjhirashi.com/health
```

---

## Configuración Nginx

```nginx
# /etc/nginx/sites-available/hub
server {
    listen 80;
    server_name hub.hira.cjhirashi.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name hub.hira.cjhirashi.com;

    ssl_certificate /etc/letsencrypt/live/hub.hira.cjhirashi.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hub.hira.cjhirashi.com/privkey.pem;

    # Rate limiting — license validation
    limit_req_zone $binary_remote_addr zone=licenses:10m rate=10r/m;

    # Rate limiting — crash reports
    limit_req_zone $binary_remote_addr zone=crashreports:10m rate=100r/h;

    location /api/licenses/ {
        limit_req zone=licenses burst=5 nodelay;
        proxy_pass http://localhost:8001;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/crash-reports {
        limit_req zone=crashreports burst=10 nodelay;
        proxy_pass http://localhost:8001;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Actualización (versión nueva)

```bash
cd /opt/hira-hub
git pull origin main

# Si hay cambios en docker-compose.yml o Dockerfile:
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Si solo cambia código Python (sin cambios de imagen):
docker compose restart backend

# Verificar
curl https://hub.hira.cjhirashi.com/health
docker compose logs --tail=20 backend
```

---

## Backup de Base de Datos

### Manual

```bash
docker compose exec postgres pg_dump -U hub hubdb | gzip > /opt/backups/hub_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Automatizado (cron)

```bash
# /opt/hira-hub/scripts/backup.sh
#!/bin/bash
BACKUP_DIR=/opt/backups
mkdir -p $BACKUP_DIR
docker compose -f /opt/hira-hub/docker-compose.yml exec -T postgres \
    pg_dump -U hub hubdb | gzip > $BACKUP_DIR/hub_$(date +%Y%m%d_%H%M%S).sql.gz
# Eliminar backups con más de 7 días
find $BACKUP_DIR -name "hub_*.sql.gz" -mtime +7 -delete
```

```cron
# crontab -e
0 3 * * * /opt/hira-hub/scripts/backup.sh >> /var/log/hira-hub-backup.log 2>&1
```

---

## Variables de Entorno Requeridas

Las siguientes 4 variables NUNCA tienen valor por defecto — deben configurarse manualmente:

| Variable | Cómo generarla |
|---|---|
| `POSTGRES_PASSWORD` | `openssl rand -hex 16` |
| `REDIS_PASSWORD` | `openssl rand -hex 16` |
| `SECRET_KEY` | `openssl rand -hex 32` |
| `ADMIN_PASSWORD_HASH` | `python3 -c "import bcrypt; print(bcrypt.hashpw(b'TU_PASSWORD', bcrypt.gensalt()).decode())"` |

---

## Monitoreo

| Herramienta | Configuración |
|---|---|
| UptimeRobot | Monitor HTTP — `https://hub.hira.cjhirashi.com/health` — alerta a cjhirashi@gmail.com |
| Docker healthcheck | Definido en `docker-compose.prod.yml` para postgres y redis |

---

## Endpoints v0.1 en Producción

| Endpoint | Acceso | Rate Limit |
|---|---|---|
| `POST /api/licenses/validate` | Público (desde Servers) | 10 req/min por IP |
| `POST /api/licenses/activate` | Público (desde Servers) | 10 req/min por IP |
| `GET /api/updates/latest` | Público (desde Servers y Studios) | Sin límite |
| `POST /api/crash-reports` | Público (desde Servers y Studios) | 100 req/hora por IP |
| `GET /health` | Público | Sin límite |
| `/admin/*` | Solo cjhirashi (JWT) | N/A |

---

## Costos

| Concepto | Costo |
|---|---|
| VPS (Hetzner CX21 — 2 vCPU / 4 GB) | ~$5/mes |
| SSL Let's Encrypt | $0 |
| Email transaccional Resend (free tier) | $0 hasta 3,000 emails/mes |
| GitHub Actions (repositorio privado) | $0 (2,000 min/mes free) |
| UptimeRobot | $0 (free tier) |
| **Total mensual fijo** | **~$5–15/mes** |

---

## Nota de infraestructura — Servidor local de Charlie (2026-08-12)

Este documento describe el despliegue de producción de Hira Hub en un VPS externo (Hetzner/DigitalOcean) con Nginx + Certbot. Ese flujo es correcto para producción.

Sin embargo, cuando Hira Hub se pruebe en el **servidor local de Charlie** (`192.168.100.200`), aplica un modelo diferente:

- **No usar Nginx propio** — el servidor local tiene un **Caddy global compartido** (`~/infraestructura/`) que gestiona todos los proyectos
- El backend de Hira Hub se expone solo en red Docker interna
- Caddy enruta por subdominio y gestiona Let's Encrypt automáticamente (sin certbot)
- Los datos persistentes van en `~/hira-hub-data/` (solo en pruebas — el servidor local no es producción para Hira Hub)

Referencia: `1.1.6.2 - Entorno de Desarrollo` del proyecto Synapse documenta la arquitectura de infraestructura compartida del servidor.

## Gate de Salida

- [x] Infraestructura VPS definida
- [x] Proceso de primer despliegue documentado
- [x] Configuración Nginx completa
- [x] Flujo de actualización documentado
- [x] Backup automatizado definido
- [x] Monitoreo configurado
- [ ] Revisado y aprobado por Charlie
- [ ] Pendiente: documentar flujo de prueba en servidor local con Caddy compartido (cuando aplique)
