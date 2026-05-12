FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MEALIE_IMPORT_ORCHESTRATOR_REPO_ROOT=/app \
    MEALIE_IMPORT_ORCHESTRATOR_ENABLE_SCRAPING=true \
    ADDON_API_HOST=0.0.0.0 \
    ADDON_API_PORT=8000 \
    ADDON_UI_PORT=8501

WORKDIR /app

# System deps for scraping (lxml, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libxml2 \
        libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# Copy the canonical workflow (source de vérité)
COPY mealie-workflow /app/mealie-workflow

# Copy and install the addon (includes FastAPI + Streamlit)
COPY addons/mealie-import-orchestrator /app/addons/mealie-import-orchestrator
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "/app/addons/mealie-import-orchestrator" rapidfuzz

# Entrypoint script
RUN chmod +x /app/addons/mealie-import-orchestrator/entrypoint.sh

EXPOSE 8000 8501

ENTRYPOINT ["/app/addons/mealie-import-orchestrator/entrypoint.sh"]
