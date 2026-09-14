# nginx

Proxy reverso hacia `backend` (RF-006).

- `nginx.conf` — genérico/local (`listen 80`, sin `server_name` de dominio ni
  TLS real), proxy hacia `backend:8001`. El dominio real
  (`hub.hira.cjhirashi.com`) y TLS/Let's Encrypt/Certbot
  (`docs/hira-hub/spec/deployment.md`) son un sprint operativo posterior —
  fuera de alcance de `HUB-001-walking-skeleton` (`spec.md §2`).
