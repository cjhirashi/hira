# nginx

Reverse proxy del compose (RF-001, `SRV-001-walking-skeleton` T-018).
`nginx.conf` — proxy mínimo `location / { proxy_pass http://backend:8000; }`
con las cabeceras estándar de forwarding (`Host`, `X-Real-IP`,
`X-Forwarded-For`, `X-Forwarded-Proto`).

> Nota de deuda ya documentada (no resolver aquí): `docs/hira-server/spec/
> implementation-guide/guia-backend.md` registra un cambio pendiente Nginx → Caddy
> global de infraestructura compartida. Este sprint (`RF-001`) sigue exigiendo `nginx`
> en el compose — la migración a Caddy es un sprint de infraestructura aparte.
