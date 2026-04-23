# 🍽️ Mealie Budget Advisor

Addon externe pour Mealie permettant l'estimation des coûts des recettes et l'assistance au choix selon le budget.

## 🎯 Objectif

Aider à planifier des menus en tenant compte du budget mensuel, sans rigidité comptable :
- **Estimation des coûts** des recettes (pas précision au centime)
- **Assistance au choix** : prioriser les recettes selon leurs coûts relatifs
- **Logique de comparaison** : "poulet rôti > bœuf bourguignon" en termes de coût

## 🏗️ Architecture

```
addons/mealie-budget-advisor/
├── src/mealie_budget_advisor/
│   ├── api.py              # FastAPI REST
│   ├── ui.py               # Streamlit UI
│   ├── config.py           # Configuration
│   ├── mealie_sync.py      # Client Mealie API
│   ├── models/             # Pydantic models
│   │   ├── budget.py       # BudgetSettings, BudgetPeriod
│   │   ├── cost.py         # RecipeCost, IngredientCost
│   │   └── pricing.py      # PriceSource, ManualPrice
│   ├── pricing/            # Gestion des prix
│   │   ├── open_prices_client.py  # API Open Prices
│   │   ├── manual_pricer.py       # Prix manuels (JSON)
│   │   ├── ingredient_matcher.py  # Matching ingrédients
│   │   └── cost_calculator.py     # Calcul coût recettes
│   └── planning/           # Planning budget-aware (Phase 2)
├── data/                   # Données persistantes
├── config/                 # Configuration
├── pyproject.toml
├── Dockerfile
└── docker-compose.yml
```

## 📊 Sources de prix

| Source | Fiabilité | Couverture | Usage |
|--------|-----------|------------|-------|
| **Open Prices** (OFF) | Élevée | Variable | Recherche par nom/code-barres |
| **Prix manuels** | Très élevée | Limitée | Fallback personnalisé |
| **Estimation** | Moyenne | Tous | Dernier recours |

## 🚀 Démarrage rapide

### Prérequis

- Docker et Docker Compose
- Instance Mealie accessible avec API token

### Configuration

1. Copier et modifier le fichier d'environnement :
```bash
cp .env.template .env
# Éditer .env avec vos valeurs
```

2. Variables obligatoires :
```env
MEALIE_BASE_URL=http://localhost:9925
MEALIE_API_KEY=votre-token-api-mealie
```

### Démarrage

```bash
# Production
docker compose up -d

# Développement (hot reload)
cp .env.template .env.dev
# Éditer .env.dev avec vos valeurs
docker compose -f docker-compose.dev.yml up
```

### Accès

- **API**: http://localhost:8003
- **UI**: http://localhost:8503
- **Health**: `curl http://localhost:8003/health`

## 📚 API Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/status` | Statut et configuration |
| GET | `/budget` | Budget mensuel actuel |
| POST | `/budget` | Définir le budget |
| GET | `/prices/search?q={query}` | Recherche Open Prices |
| GET | `/prices/manual` | Liste prix manuels |
| POST | `/prices/manual` | Ajouter prix manuel |
| GET | `/recipes/{slug}/cost` | Coût d'une recette |
| POST | `/recipes/batch-cost` | Coût batch |
| GET | `/recipes/compare-costs` | Comparer recettes |

## 🧪 Tests rapides

```bash
# Vérifier l'API
curl http://localhost:8003/health

# Rechercher un prix
curl "http://localhost:8003/prices/search?q=farine&limit=5"

# Calculer le coût d'une recette
curl "http://localhost:8003/recipes/carbonara-marmiton/cost"
```

## 🗺️ Roadmap

### Sprint 1 ✅ (Actuel)
- [x] Structure de base de l'addon
- [x] Modèles Pydantic
- [x] Client API Open Prices
- [x] Gestion prix manuels
- [x] API endpoints de base
- [x] UI Streamlit basique

### Sprint 2 (À venir)
- [ ] Parser ingrédients avancé
- [ ] Calcul coût recette complet
- [ ] UI gestion des prix

### Sprint 3 (À venir)
- [ ] Gestion budget mensuel
- [ ] Affichage coût dans recettes

### Sprint 4 (À venir)
- [ ] Planning respectant le budget
- [ ] Suggestions d'alternatives

## 📄 Licence

MIT - Voir [LICENSE](../../LICENSE)
