# 🍽️ Mealie Import Addon

An external addon for [Mealie](https://mealie.io) that adds a **Web UI + REST API** to import recipes from any cooking website (Marmiton, 750g, …) and audit recipe quality — without modifying your Mealie instance.

## Features

- **📥 Import by URL** — paste any recipe URL, the addon scrapes, structures and imports it into Mealie automatically
- **🔍 Quality audit** — detects missing images, placeholder CDN images, test tags, and probable duplicates
- **🔧 Auto-fix** — uploads a relevant fallback image (via TheMealDB), removes unwanted tags
- **🌐 Web UI** (Streamlit) — simple 3-tab interface: Import / Audit / Status
- **⚡ REST API** (FastAPI) — `POST /import`, `GET /audit`, `POST /audit/fix`, `GET /status`
- **🤖 AI optional** — works without OpenAI key (JSON-LD fallback); enable AI for better recipe structuring
- **🐳 Standalone Docker image** — no dependency on the host filesystem

## Quick start (Docker Compose)

```bash
# 1. Clone and configure
git clone https://github.com/nonofr91/addonmealie.git
cd addonmealie/addons/mealie-import-orchestrator
cp .env.template .env
# Edit .env with your Mealie URL and API key

# 2. Start
docker compose up -d

# 3. Open
#   Web UI  → http://localhost:8501
#   API     → http://localhost:8000
#   API docs → http://localhost:8000/docs
```

## Environment variables

```env
# Required
MEALIE_BASE_URL=https://your-mealie-instance.example.com
MEALIE_API_KEY=your-mealie-api-key

# Optional — AI structuring (JSON-LD fallback if absent)
# OPENAI_API_KEY=sk-...
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-4.1-mini

# Optional — secure the addon API
# ADDON_SECRET_KEY=change-me-in-production

ADDON_API_PORT=8000
ADDON_UI_PORT=8501
LOG_LEVEL=INFO
```

## Deploy on Coolify / self-hosted

Use the pre-built Docker image:

```bash
docker pull ghcr.io/nonofr91/mealie-import-addon:latest
docker run -d \
  -e MEALIE_BASE_URL=https://your-mealie.example.com \
  -e MEALIE_API_KEY=your-key \
  -p 8000:8000 -p 8501:8501 \
  ghcr.io/nonofr91/mealie-import-addon:latest
```

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/status` | Mealie connectivity + AI status |
| `POST` | `/import` | `{"url": "..."}` → import recipe |
| `GET` | `/audit` | Scan all recipes, return issues |
| `POST` | `/audit/fix` | Scan + auto-fix issues |

Optional auth: pass `X-Addon-Key: <ADDON_SECRET_KEY>` header.

## Run locally (dev)

```bash
# Install
pip install -e .

# Start API (port 8002)
MEALIE_BASE_URL=http://localhost:9925 MEALIE_API_KEY=<key> \
  python -m uvicorn mealie_import_orchestrator.api:app --port 8002

# Start UI (port 8502)
ADDON_API_URL=http://localhost:8002 \
  python -m streamlit run src/mealie_import_orchestrator/ui.py --server.port 8502
```

## Architecture

```
addons/mealie-import-orchestrator/
├── src/mealie_import_orchestrator/
│   ├── api.py          ← FastAPI (REST API)
│   ├── ui.py           ← Streamlit (Web UI)
│   ├── cli.py          ← CLI
│   ├── orchestrator.py ← Core logic
│   └── config.py       ← Env-based config
├── Dockerfile          ← Standalone image (mealie-workflow embedded)
├── docker-compose.yml  ← Mealie + addon
├── entrypoint.sh       ← Starts API + UI
└── .env.template       ← Config template
```

The addon communicates with Mealie **exclusively via its public API** — no modifications to the Mealie image or database.

## Supported recipe sources

Tested: Marmiton, 750g  
Should work: any site with JSON-LD `Recipe` schema

## License

MIT
