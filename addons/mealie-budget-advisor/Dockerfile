FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LOG_LEVEL=INFO \
    ADDON_API_HOST=0.0.0.0 \
    ADDON_API_PORT=8003 \
    ADDON_UI_PORT=8503 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY addons/mealie-budget-advisor /app
RUN pip install --no-cache-dir .
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" streamlit requests

RUN mkdir -p /app/data /app/config

EXPOSE 8003 8503

CMD ["uvicorn", "mealie_budget_advisor.api:app", "--host", "0.0.0.0", "--port", "8003"]
