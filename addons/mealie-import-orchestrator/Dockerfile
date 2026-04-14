FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MEALIE_IMPORT_ORCHESTRATOR_REPO_ROOT=/app

WORKDIR /app

COPY addons/mealie-import-orchestrator /app/addons/mealie-import-orchestrator
COPY mealie-workflow /app/mealie-workflow

RUN pip install --no-cache-dir /app/addons/mealie-import-orchestrator

ENTRYPOINT ["mealie-import-orchestrator"]
CMD ["status"]
