#!/bin/bash
set -e

echo "🍽️  Mealie Import Addon starting…"
echo "   Mealie : ${MEALIE_BASE_URL:-<not set>}"
echo "   AI     : ${OPENAI_API_KEY:+enabled}${OPENAI_API_KEY:-disabled}"

# Start FastAPI in background
uvicorn mealie_import_orchestrator.api:app \
    --host "${ADDON_API_HOST:-0.0.0.0}" \
    --port "${ADDON_API_PORT:-8000}" \
    --log-level "${LOG_LEVEL:-info}" &

API_PID=$!
echo "   API    : PID $API_PID  → http://0.0.0.0:${ADDON_API_PORT:-8000}"

# Wait a moment for the API to be ready
sleep 2

# Start Streamlit in foreground (keeps container alive)
UI_FILE=$(python -c "import mealie_import_orchestrator.ui as m; import os; print(os.path.abspath(m.__file__))")
exec streamlit run "$UI_FILE" \
    --server.port "${ADDON_UI_PORT:-8501}" \
    --server.address "0.0.0.0" \
    --server.headless "true" \
    --browser.gatherUsageStats "false"
