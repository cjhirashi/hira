# Imagen del `backend` (FastAPI) — Walking Skeleton (`HUB-001-walking-skeleton`, T-016).
# Perfil único (cloud single-tenant, `E-ADR-002`): sin build condicional.
# Puerto :8001 — puerto interno de Hub (`docs/hira-hub/spec/deployment.md`),
# distinto del :8000 de `hira-server`, para poder correr ambos stacks locales
# al mismo tiempo sin colisión de puertos.
FROM python:3.12-slim

WORKDIR /app

# curl: usado por el HEALTHCHECK (`GET /health`, ver docker-compose.yml).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
