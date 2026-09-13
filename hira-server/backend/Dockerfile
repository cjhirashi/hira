# Imagen del `backend` (FastAPI) — Walking Skeleton (`SRV-001-walking-skeleton`, T-016).
# Perfil único de producción (`E-ADR-001`): sin HIRA_DEPLOY_MODE, sin build condicional.
FROM python:3.12-slim

WORKDIR /app

# curl: usado por el HEALTHCHECK (`GET /health`, ver docker-compose.yml).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
