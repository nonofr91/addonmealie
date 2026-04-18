# Guide d'installation - Mealie Addons Platform

Ce guide explique comment installer et configurer les addons Mealie pour votre installation Mealie existante.

## Prérequis

### Requis

- **Docker** : Version 20.10 ou supérieure
- **Docker Compose** : Version 2.0 ou supérieure
- **Instance Mealie** : Version 3.x avec API key
- **Espace disque** : Minimum 5 GB pour les images et logs

### Optionnel (développement)

- **Python** : Version 3.12 ou supérieure
- **uv** : Gestionnaire de packages Python (recommandé)
- **Git** : Pour cloner le dépôt

## Installation Docker (recommandée)

### Import Addon

L'addon d'import permet d'importer des recettes depuis le web et d'auditer leur qualité.

#### 1. Pull de l'image

```bash
docker pull ghcr.io/nonofr91/mealie-import-addon:latest
```

#### 2. Lancement avec Docker

```bash
docker run -d \
  --name mealie-import-addon \
  -e MEALIE_BASE_URL=https://your-mealie-instance.com \
  -e MEALIE_API_KEY=your-mealie-api-key \
  -p 8000:8000 \
  -p 8501:8501 \
  ghcr.io/nonofr91/mealie-import-addon:latest
```

#### 3. Accès

- **API** : http://localhost:8000
- **API docs** : http://localhost:8000/docs
- **Web UI** : http://localhost:8501

#### 4. Configuration avancée (optionnel)

```bash
docker run -d \
  --name mealie-import-addon \
  -e MEALIE_BASE_URL=https://your-mealie-instance.com \
  -e MEALIE_API_KEY=your-mealie-api-key \
  -e OPENAI_API_KEY=sk-... \
  -e OPENAI_MODEL=gpt-4.1-mini \
  -e ADDON_SECRET_KEY=change-me-in-production \
  -e LOG_LEVEL=INFO \
  -p 8000:8000 \
  -p 8501:8501 \
  ghcr.io/nonofr91/mealie-import-addon:latest
```

### Nutrition Addon

L'addon nutrition permet de calculer les valeurs nutritionnelles et de planifier des menus.

#### 1. Pull de l'image

```bash
docker pull ghcr.io/nonofr91/mealie-nutrition-advisor:latest
```

#### 2. Lancement avec Docker

```bash
docker run -d \
  --name mealie-nutrition-addon \
  -e MEALIE_BASE_URL=https://your-mealie-instance.com \
  -e MEALIE_API_KEY=your-mealie-api-key \
  -p 8001:8001 \
  -p 8502:8502 \
  ghcr.io/nonofr91/mealie-nutrition-advisor:latest
```

#### 3. Accès

- **API** : http://localhost:8001
- **API docs** : http://localhost:8001/docs
- **Web UI** : http://localhost:8502

#### 4. Configuration avancée (optionnel)

```bash
docker run -d \
  --name mealie-nutrition-addon \
  -e MEALIE_BASE_URL=https://your-mealie-instance.com \
  -e MEALIE_API_KEY=your-mealie-api-key \
  -e AI_PROVIDER=mistral \
  -e MISTRAL_API_KEY=your-mistral-key \
  -e MISTRAL_MODEL=mistral-small-latest \
  -e USE_AI_ESTIMATION=true \
  -e ADDON_SECRET_KEY=change-me-in-production \
  -e LOG_LEVEL=INFO \
  -p 8001:8001 \
  -p 8502:8502 \
  ghcr.io/nonofr91/mealie-nutrition-advisor:latest
```

### Docker Compose (recommandé pour production)

Créez un fichier `docker-compose.yml` :

```yaml
version: '3.8'

services:
  mealie-import-addon:
    image: ghcr.io/nonofr91/mealie-import-addon:latest
    container_name: mealie-import-addon
    environment:
      - MEALIE_BASE_URL=https://your-mealie-instance.com
      - MEALIE_API_KEY=your-mealie-api-key
      # - OPENAI_API_KEY=sk-...
      # - ADDON_SECRET_KEY=change-me
      - LOG_LEVEL=INFO
    ports:
      - "8000:8000"
      - "8501:8501"
    restart: unless-stopped

  mealie-nutrition-addon:
    image: ghcr.io/nonofr91/mealie-nutrition-advisor:latest
    container_name: mealie-nutrition-addon
    environment:
      - MEALIE_BASE_URL=https://your-mealie-instance.com
      - MEALIE_API_KEY=your-mealie-api-key
      - AI_PROVIDER=mock
      # - MISTRAL_API_KEY=your-mistral-key
      # - ADDON_SECRET_KEY=change-me
      - LOG_LEVEL=INFO
    ports:
      - "8001:8001"
      - "8502:8502"
    restart: unless-stopped
```

Lancement :

```bash
docker-compose up -d
```

## Installation locale (développement)

### Import Addon

#### 1. Cloner le dépôt

```bash
git clone https://github.com/nonofr91/addonmealie.git
cd addonmealie/addons/mealie-import-orchestrator
```

#### 2. Créer l'environnement virtuel

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows
```

#### 3. Installer les dépendances

```bash
pip install -e .
pip install fastapi uvicorn[standard] streamlit requests beautifulsoup4
```

> **Note** : Sur Linux, utiliser systématiquement `python3` au lieu de `python` pour toutes les commandes Python.

#### 4. Configurer

```bash
cp .env.template .env
# Éditer .env avec vos valeurs
```

#### 5. Lancer l'API

```bash
python3 -m uvicorn mealie_import_orchestrator.api:app --port 8000
```

> **Note** : Si le port 8000 est déjà utilisé, vous pouvez changer le port via la variable d'environnement `ADDON_API_PORT` dans `.env` ou spécifier un autre port directement dans la commande (ex: `--port 8002`).

#### 6. Lancer l'UI (dans un autre terminal)

```bash
ADDON_API_URL=http://localhost:8000 \
python3 -m streamlit run src/mealie_import_orchestrator/ui.py --server.port 8501
```

### Nutrition Addon

#### 1. Cloner le dépôt

```bash
git clone https://github.com/nonofr91/addonmealie.git
cd addonmealie/addons/mealie-nutrition-advisor
```

#### 2. Créer l'environnement virtuel

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows
```

#### 3. Installer les dépendances

```bash
pip install -e .
pip install fastapi uvicorn[standard] streamlit requests
```

#### 4. Configurer

```bash
cp .env.template .env
# Éditer .env avec vos valeurs
```

#### 5. Lancer l'API

```bash
PYTHONPATH=src \
python3 -m mealie_nutrition_advisor.api
```

#### 6. Lancer l'UI (dans un autre terminal)

```bash
PYTHONPATH=src \
ADDON_API_URL=http://localhost:8001 \
python3 -m mealie_nutrition_advisor.ui
```

## Configuration

### Variables d'environnement communes

| Variable | Requis | Description |
|----------|--------|-------------|
| `MEALIE_BASE_URL` | ✅ | URL de votre instance Mealie |
| `MEALIE_API_KEY` | ✅ | Token API Mealie |
| `ADDON_SECRET_KEY` | — | Secret pour sécuriser l'API (optionnel) |
| `LOG_LEVEL` | — | Niveau de log (DEBUG, INFO, WARNING, ERROR) |

### Import Addon - Variables spécifiques

| Variable | Requis | Description |
|----------|--------|-------------|
| `OPENAI_API_KEY` | — | Clé OpenAI pour structuration IA |
| `OPENAI_BASE_URL` | — | URL base OpenAI (défaut: https://api.openai.com/v1) |
| `OPENAI_MODEL` | — | Modèle OpenAI (défaut: gpt-4.1-mini) |
| `ADDON_API_PORT` | — | Port API (défaut: 8000) |
| `ADDON_UI_PORT` | — | Port UI (défaut: 8501) |

### Nutrition Addon - Variables spécifiques

| Variable | Requis | Description |
|----------|--------|-------------|
| `AI_PROVIDER` | — | Provider IA (openai, anthropic, mistral, mock) |
| `USE_AI_ESTIMATION` | — | Activer estimation IA (true/false) |
| `OPENAI_API_KEY` | — | Clé OpenAI (si AI_PROVIDER=openai) |
| `ANTHROPIC_API_KEY` | — | Clé Anthropic (si AI_PROVIDER=anthropic) |
| `MISTRAL_API_KEY` | — | Clé Mistral (si AI_PROVIDER=mistral) |
| `OFF_BASE_URL` | — | URL Open Food Facts (défaut: mondial) |
| `NUTRITION_CACHE_TTL_DAYS` | — | TTL cache nutrition (défaut: 30) |
| `ADDON_API_PORT` | — | Port API (défaut: 8001) |
| `ADDON_UI_PORT` | — | Port UI (défaut: 8502) |

### Obtenir votre clé API Mealie

1. Connectez-vous à votre instance Mealie
2. Allez dans **Settings** > **API Tokens**
3. Cliquez sur **Create Token**
4. Copiez le token généré

## Vérification de l'installation

### Vérifier l'Import Addon

```bash
curl http://localhost:8000/health
```

Réponse attendue :
```json
{"status": "ok"}
```

```bash
curl http://localhost:8000/status
```

Réponse attendue :
```json
{
  "status": "ok",
  "mealie_connected": true,
  "ai_enabled": false
}
```

### Vérifier le Nutrition Addon

```bash
curl http://localhost:8001/health
```

Réponse attendue :
```json
{"status": "ok"}
```

```bash
curl http://localhost:8001/status
```

Réponse attendue :
```json
{
  "status": "ok",
  "mealie_connected": true,
  "ai_provider": "mock"
}
```

### Vérifier les Web UI

- Import UI : http://localhost:8501
- Nutrition UI : http://localhost:8502

## Dépannage

### Le conteneur ne démarre pas

**Vérifier les logs :**
```bash
docker logs mealie-import-addon
docker logs mealie-nutrition-addon
```

**Causes courantes :**
- Port déjà utilisé : changez les ports mappés
- Variables d'environnement manquantes : vérifiez MEALIE_BASE_URL et MEALIE_API_KEY
- Image non disponible : faites `docker pull` avant de lancer

### Erreur de connexion à Mealie

**Vérifier :**
- L'URL Mealie est correcte et accessible
- La clé API est valide et non expirée
- Mealie est en cours d'exécution

**Test manuel :**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" https://your-mealie.com/api/groups
```

### L'IA ne fonctionne pas

**Vérifier :**
- La clé API du provider est configurée
- Le provider est correctement spécifié (AI_PROVIDER)
- Les quotas API ne sont pas épuisés

**Test avec mock :**
```bash
AI_PROVIDER=mock python3 -m mealie_nutrition_advisor.api
```

### Logs trop verbeux

**Réduire le niveau de log :**
```bash
LOG_LEVEL=WARNING docker-compose up
```

### Performance lente

**Optimisations :**
- Utiliser le cache nutritionnel (NUTRITION_CACHE_TTL_DAYS)
- Désactiver l'estimation IA si non nécessaire (USE_AI_ESTIMATION=false)
- Augmenter les ressources Docker si nécessaire

## Mise à jour

### Mettre à jour les images Docker

```bash
docker pull ghcr.io/nonofr91/mealie-import-addon:latest
docker pull ghcr.io/nonofr91/mealie-nutrition-advisor:latest
docker-compose pull
docker-compose up -d
```

### Mettre à jour depuis le source

```bash
git pull origin main
pip install -e .
```

## Désinstallation

### Docker

```bash
docker-compose down
docker rmi ghcr.io/nonofr91/mealie-import-addon:latest
docker rmi ghcr.io/nonofr91/mealie-nutrition-advisor:latest
```

### Local

```bash
deactivate
rm -rf .venv
```

## Support

Pour plus d'aide :
- Vérifier la documentation de chaque addon dans `addons/*/README.md`
- Consulter l'architecture dans `docs/ARCHITECTURE.md`
- Ouvrir une issue sur GitHub pour les bugs
- Utiliser GitHub Discussions pour les questions
