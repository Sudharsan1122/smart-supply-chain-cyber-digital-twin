# ============================================================================
# Smart Supply Chain Cyber Digital Twin — Dashboard Dockerfile
# ============================================================================

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash app
WORKDIR /app

RUN pip install --no-cache-dir flask==3.0.3 requests==2.32.3 gunicorn==22.0.0

COPY --chown=app:app dashboard/ /app/dashboard/

USER app

EXPOSE 5000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
    CMD curl -fsS http://localhost:5000/healthz || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", \
     "--threads", "4", "dashboard.app:app"]
