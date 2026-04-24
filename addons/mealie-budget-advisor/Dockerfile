FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie du code source, README et pyproject.toml
COPY pyproject.toml README.md src/ ./

# Installation des dépendances Python (non-editable pour éviter le problème egg_base)
RUN pip install --no-cache-dir "."

# Port exposés
EXPOSE 8003 8503

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Commande par défaut (API)
CMD ["uvicorn", "mealie_budget_advisor.api:app", "--host", "0.0.0.0", "--port", "8003"]
