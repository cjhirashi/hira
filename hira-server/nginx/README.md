# nginx

Reverse proxy del compose (RF-001). `nginx.conf` pendiente — batch posterior
(`tasks.md` T-018, requiere `docker-compose.yml`).

> Nota de deuda ya documentada (no resolver aquí): `docs/hira-server/spec/
> implementation-guide/guia-backend.md` registra un cambio pendiente Nginx → Caddy
> global de infraestructura compartida. Este sprint (`RF-001`) sigue exigiendo `nginx`
> en el compose — la migración a Caddy es un sprint de infraestructura aparte.
