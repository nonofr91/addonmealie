# mealie-nutrition-advisor

Addon externe Mealie pour :
- **Calculer** les valeurs nutritionnelles des recettes (kcal, protéines, lipides, glucides, fibres)
- **Enrichir** les recettes existantes sans données nutritionnelles
- **Intégrer** automatiquement le calcul nutritionnel lors des imports
- **Gérer** les profils avancés des membres du foyer (pathologies, présence hebdomadaire)
- **Planifier** des menus hebdomadaires compatibles avec chaque profil et absences
- **Intégrer** avec le planning natif de Mealie (recipe_id UUID)

> Cet addon ne modifie pas l'image Mealie. Il passe exclusivement par l'API publique.

---

## Installation

### Installation locale

```bash
pip install -e "addons/mealie-nutrition-advisor"
```

### Installation des dépendances UI/API

```bash
pip install fastapi uvicorn[standard] streamlit requests
```

## Configuration

```bash
cp addons/mealie-nutrition-advisor/.env.template .env
# Remplir MEALIE_BASE_URL et MEALIE_API_KEY
```

## Utilisation

### CLI (Interface en ligne de commande)

```bash
# Enrichir les recettes Mealie sans valeur nutritionnelle
mealie-nutrition enrich

# Forcer le recalcul de toutes les recettes
mealie-nutrition enrich --force

# Gérer les profils du foyer
mealie-nutrition profile list
mealie-nutrition profile add

# Générer un menu pour la semaine
mealie-nutrition plan --week 2026-W16

# Générer et pousser dans Mealie
mealie-nutrition plan --week 2026-W16 --push
```

### API FastAPI

Lancer l'API :

```bash
PYTHONPATH=addons/mealie-nutrition-advisor/src \
MEALIE_BASE_URL=http://127.0.0.1:9925 \
MEALIE_API_KEY=votre_clé_api \
ADDON_SECRET_KEY=votre_secret \
python3 -m mealie_nutrition_advisor.api
```

Endpoints disponibles :
- `GET /health` - Vérifier le statut de l'API
- `GET /status` - Statut de l'addon et des recettes
- `GET /nutrition/scan` - Scanner les recettes sans nutrition
- `POST /nutrition/enrich` - Enrichir toutes les recettes (optionnel `force=true`)
- `POST /nutrition/recipe/{slug}` - Enrichir une recette spécifique
- `GET /profiles` - Lister tous les profils du foyer
- `GET /profiles/{name}` - Détails d'un profil spécifique
- `POST /profiles` - Créer un nouveau profil
- `PUT /profiles/{name}` - Mettre à jour un profil
- `DELETE /profiles/{name}` - Supprimer un profil
- `POST /profiles/{name}/presence` - Mettre à jour le pattern de présence hebdomadaire

### UI Streamlit

Lancer l'UI :

```bash
PYTHONPATH=addons/mealie-nutrition-advisor/src \
ADDON_API_URL=http://localhost:8001 \
ADDON_SECRET_KEY=votre_secret \
MEALIE_BASE_URL=http://127.0.0.1:9925 \
python3 -m mealie_nutrition_advisor.ui
```

L'UI est accessible sur http://localhost:8502 avec 3 tabs :
- **Enrichissement** - Scanner et enrichir les recettes
- **Profils** - Gestion complète des profils du foyer (ajout, modification, suppression, pathologies, présence)
- **Statut** - Statut de l'addon

### Docker

Lancer avec Docker Compose :

```bash
cd addons/mealie-nutrition-advisor
docker-compose up -d
```

Services :
- API nutrition : http://localhost:8001
- UI nutrition : http://localhost:8502

### Intégration avec mealie-import-orchestrator

L'addon nutrition s'intègre automatiquement dans le workflow d'import de mealie-import-orchestrator. Pour activer le calcul nutritionnel automatique :

```bash
# Dans le .env de mealie-import-orchestrator
ENABLE_NUTRITION=true
NUTRITION_API_URL=http://nutrition-api:8001
```

Lors de l'import d'une recette, l'addon nutrition sera appelé automatiquement pour calculer les valeurs nutritionnelles.

### Intégration UI dans Mealie (Recipe Actions)

Pour intégrer l'UI de l'addon dans Mealie de manière plus élégante, utilisez le script d'automatisation :

```bash
# Configurer les variables d'environnement
export MEALIE_BASE_URL=http://votre-mealie:9000
export MEALIE_API_KEY=votre_token_api
export ADDON_UI_URL=http://localhost:8502

# Exécuter le script
python3 addons/mealie-nutrition-advisor/scripts/setup_mealie_integration.py
```

Ce script crée automatiquement :
- Une recette spéciale "🔬 Nutrition Advisor" dans Mealie
- Un tag `nutrition-addon` pour la retrouver facilement
- Une recipe action qui ouvre l'UI de l'addon

Vous pouvez ensuite trouver cette recette dans Mealie en recherchant le tag `nutrition-addon` ou le nom "🔬 Nutrition Advisor".

## Sources nutritionnelles

1. **Open Food Facts** — base mondiale gratuite, sans clé API
2. **LLM fallback** — estimation via OpenAI/Anthropic/Mistral si OFF ne trouve rien
3. **Cache local** — `data/nutrition_cache.json` (TTL configurable)

## Profils du foyer

Éditer `config/household_profiles.json`, utiliser `mealie-nutrition profile add`, ou l'UI Streamlit.

Champs supportés :
- **Basiques** : nom, âge, sexe, poids, taille, niveau d'activité
- **Objectifs** : perte/maintien/prise de poids, cibles numériques personnalisées
- **Santé** : pathologies médicales (diabète, hypertension, cholestérol, goutte, reflux, insuffisance rénale)
- **Restrictions** : restrictions alimentaires, allergies
- **Présence** : planning hebdomadaire fixe des repas pris par jour (absences gérées)

Les pathologies médicales ajustent automatiquement les cibles nutritionnelles :
- Hypertension : sodium réduit à 1500mg/jour
- Diabète : glucides limités à 45% des calories
- Insuffisance rénale : sodium réduit à 2000mg/jour

## Structure

```
src/mealie_nutrition_advisor/
  models/        # Pydantic models
  nutrition/     # Moteur calcul (OFF + IA + cache)
  profiles/      # Gestion profils + BMR/TDEE
  planner/       # Score, filtre, planificateur hebdo
  mealie_sync.py # Sync vers Mealie
  orchestrator.py# CLI
  config.py      # Configuration centralisée
  api.py         # API FastAPI
  ui.py          # UI Streamlit
```

## Variables d'environnement

| Variable | Requis | Description |
|---|---|---|
| `MEALIE_BASE_URL` | ✅ | URL de l'instance Mealie |
| `MEALIE_API_KEY` | ✅ | Token API Mealie |
| `AI_PROVIDER` | — | `openai` / `anthropic` / `mistral` / `mock` (défaut: `mock`) |
| `USE_AI_ESTIMATION` | — | `true` / `false` pour l'estimation IA des quantités (défaut: `false`) |
| `OPENAI_API_KEY` | Si `AI_PROVIDER=openai` | Clé OpenAI |
| `OPENAI_MODEL` | Si `AI_PROVIDER=openai` | Modèle OpenAI (défaut: `gpt-4.1-mini`) |
| `ANTHROPIC_API_KEY` | Si `AI_PROVIDER=anthropic` | Clé Anthropic |
| `ANTHROPIC_MODEL` | Si `AI_PROVIDER=anthropic` | Modèle Anthropic (défaut: `claude-3-haiku-20240307`) |
| `MISTRAL_API_KEY` | Si `AI_PROVIDER=mistral` | Clé Mistral |
| `MISTRAL_MODEL` | Si `AI_PROVIDER=mistral` | Modèle Mistral (défaut: `mistral-small-latest`) |
| `OFF_BASE_URL` | — | URL Open Food Facts (défaut: off mondial) |
| `NUTRITION_CACHE_TTL_DAYS` | — | TTL cache (défaut: 30) |
| `ADDON_API_HOST` | — | Host API (défaut: `0.0.0.0`) |
| `ADDON_API_PORT` | — | Port API (défaut: `8001`) |
| `ADDON_SECRET_KEY` | — | Secret pour auth API (optionnel) |
| `ADDON_UI_PORT` | — | Port UI (défaut: `8502`) |
| `ADDON_API_URL` | — | URL API pour UI (défaut: `http://localhost:8001`) |
| `LOG_LEVEL` | — | Niveau de log (défaut: `INFO`) |

## Déploiement

### Docker Compose local

```bash
cd addons/mealie-nutrition-advisor
cp .env.template .env
# Configurer .env
docker-compose up -d
```

### Coolify

Le service nutrition-api est déjà intégré dans `docker-compose.coolify.yml`. Variables d'environnement à configurer dans Coolify :

- `MEALIE_API_KEY` : Token API Mealie
- `ENABLE_NUTRITION` : Activer l'intégration avec mealie-import-orchestrator (défaut: `true`)
- `AI_PROVIDER` : Provider IA (défaut: `mock`)
- `USE_AI_ESTIMATION` : Activer l'estimation IA des quantités (défaut: `false`)
- `ADDON_SECRET_KEY` : Secret pour auth API entre services

## Sécurité

- **Ne jamais commit de clés API** dans le repo
- Utiliser des variables d'environnement pour les secrets
- Configurer `ADDON_SECRET_KEY` pour sécuriser l'API entre services
- Utiliser le réseau Docker interne pour la communication entre services
