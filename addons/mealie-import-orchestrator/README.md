# 🍽️ Mealie Import Addon

Addon externe pour [Mealie](https://mealie.io) qui ajoute une **Web UI + REST API** pour importer des recettes depuis n'importe quel site de cuisine (Marmiton, 750g, …) et auditer la qualité des recettes — sans modifier votre instance Mealie.

## Fonctionnalités

- **📥 Import par URL** — collez n'importe quelle URL de recette, l'addon scrape, structure et importe automatiquement dans Mealie
- **🔍 Audit de qualité** — détecte les images manquantes, les images CDN placeholder, les tags de test, et les doublons probables
- **🔧 Auto-correction** — télécharge une image de remplacement pertinente (via TheMealDB), supprime les tags indésirables
- **🌐 Web UI** (Streamlit) — interface simple à 3 onglets : Import / Audit / Statut
- **⚡ REST API** (FastAPI) — `POST /import`, `GET /audit`, `POST /audit/fix`, `GET /status`
- **🤖 IA optionnelle** — fonctionne sans clé OpenAI (fallback JSON-LD) ; activez l'IA pour un meilleur structuration des recettes
- **🐳 Image Docker autonome** — aucune dépendance au système de fichiers hôte

## Démarrage rapide (Docker Compose)

```bash
# 1. Cloner et configurer
git clone https://github.com/nonofr91/addonmealie.git
cd addonmealie/addons/mealie-import-orchestrator
cp .env.template .env
# Éditez .env avec votre URL Mealie et clé API

# 2. Démarrer
docker compose up -d

# 3. Ouvrir
#   Web UI  → http://localhost:8501
#   API     → http://localhost:8000
#   API docs → http://localhost:8000/docs
```

## Variables d'environnement

```env
# Obligatoire
MEALIE_BASE_URL=https://your-mealie-instance.example.com
MEALIE_API_KEY=your-mealie-api-key

# Optionnel — structuration IA (fallback JSON-LD si absent)
# OPENAI_API_KEY=sk-...
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-4.1-mini

# Optionnel — sécuriser l'API de l'addon
# ADDON_SECRET_KEY=change-me-in-production

ADDON_API_PORT=8000
ADDON_UI_PORT=8501
LOG_LEVEL=INFO
```

## Déploiement sur Coolify / self-hosted

Utilisez l'image Docker pré-construite :

```bash
docker pull ghcr.io/nonofr91/mealie-import-addon:latest
docker run -d \
  -e MEALIE_BASE_URL=https://your-mealie.example.com \
  -e MEALIE_API_KEY=your-key \
  -p 8000:8000 -p 8501:8501 \
  ghcr.io/nonofr91/mealie-import-addon:latest
```

## API REST

| Méthode | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Vérification de l'état |
| `GET` | `/status` | Connectivité Mealie + statut IA |
| `POST` | `/import` | `{"url": "..."}` → importer une recette |
| `GET` | `/audit` | Scanner toutes les recettes, retourner les problèmes |
| `POST` | `/audit/fix` | Scanner + auto-correction des problèmes |

Auth optionnelle : passez l'en-tête `X-Addon-Key: <ADDON_SECRET_KEY>`.

## Exécution locale (dev)

```bash
# Installer
pip install -e .

# Démarrer l'API (port 8002)
MEALIE_BASE_URL=http://localhost:9925 MEALIE_API_KEY=<key> \
  python -m uvicorn mealie_import_orchestrator.api:app --port 8002

# Démarrer l'UI (port 8502)
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

L'addon communique avec Mealie **exclusivement via son API publique** — aucune modification de l'image Mealie ou de la base de données.

## Sources de recettes supportées

Testés : Marmiton, 750g  
Devrait fonctionner : tout site avec schema JSON-LD `Recipe`

## License

MIT
