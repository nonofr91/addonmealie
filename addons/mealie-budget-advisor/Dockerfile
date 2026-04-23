FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances Python
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e "."

# Copie du code source
COPY src/ ./src/

# Réinstallation avec le code
RUN pip install --no-cache-dir -e "."

# Port exposés
EXPOSE 8003 8503

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8003/health')" || exit 1

# Commande par défaut (API)
CMD ["uvicorn", "mealie_budget_advisor.api:app", "--host", "0.0.0.0", "--port", "8003"]
