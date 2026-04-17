FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AI_PROVIDER=mock \
    LOG_LEVEL=INFO \
    ADDON_API_HOST=0.0.0.0 \
    ADDON_API_PORT=8001 \
    ADDON_UI_PORT=8502 \
    PYTHONPATH=/app/addons/mealie-nutrition-advisor/src

WORKDIR /app

COPY addons/mealie-nutrition-advisor /app/addons/mealie-nutrition-advisor
RUN pip install --no-cache-dir "/app/addons/mealie-nutrition-advisor"
RUN pip install --no-cache-dir fastapi uvicorn[standard] streamlit requests

RUN mkdir -p /app/addons/mealie-nutrition-advisor/data/menu_plans

# Default to API server
ENTRYPOINT ["uvicorn", "mealie_nutrition_advisor.api:app", "--host", "0.0.0.0", "--port", "8001"]
