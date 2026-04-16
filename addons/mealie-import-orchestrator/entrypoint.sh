#!/bin/bash

echo "🍽️  Mealie Import Addon starting…"
echo "   Mealie : ${MEALIE_BASE_URL:-<not set>}"
echo "   AI     : ${OPENAI_API_KEY:+enabled}${OPENAI_API_KEY:-disabled}"

API_PORT="${ADDON_API_PORT:-8000}"

# Start FastAPI in background — stdout+stderr visible in container logs
uvicorn mealie_import_orchestrator.api:app \
    --host "${ADDON_API_HOST:-0.0.0.0}" \
    --port "$API_PORT" \
    --log-level "$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')" &

API_PID=$!
echo "   API    : PID $API_PID → http://0.0.0.0:$API_PORT"

# Wait up to 30s for the API to be ready
echo "   Waiting for API…"
for i in $(seq 1 30); do
    if python -c "import urllib.request; urllib.request.urlopen('http://localhost:$API_PORT/health')" 2>/dev/null; then
        echo "   API    : ✅ ready (${i}s)"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "   API    : ❌ not ready after 30s — Streamlit will start anyway"
    fi
    sleep 1
done

# Start Streamlit in foreground (keeps container alive)
UI_FILE=$(python -c "import mealie_import_orchestrator.ui as m; import os; print(os.path.abspath(m.__file__))")
exec streamlit run "$UI_FILE" \
    --server.port "${ADDON_UI_PORT:-8501}" \
    --server.address "0.0.0.0" \
    --server.headless "true" \
    --browser.gatherUsageStats "false"
