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
| GET | `/budget/period/{label}` | Budget par période |
| DELETE | `/budget/period/{label}` | Supprimer budget |
| GET | `/budget/list` | Lister tous les budgets |
| GET | `/prices/search?q={query}` | Recherche Open Prices |
| GET | `/prices/manual` | Liste prix manuels |
| POST | `/prices/manual` | Ajouter prix manuel |
| GET | `/recipes/{slug}/cost` | Coût d'une recette |
| POST | `/recipes/{slug}/sync-cost` | Publier le coût dans `extras.cout_*` Mealie |
| POST | `/recipes/refresh-costs` | Rafraîchir le coût de toutes les recettes |
| POST | `/recipes/batch-cost` | Coût batch |
| GET | `/recipes/compare-costs` | Comparer recettes |
| GET | `/planning/suggest-alternatives` | Suggestions alternatives |
| GET | `/planning/cost-report` | Rapport coût vs budget |

## 💾 Persistance du coût dans Mealie (`extras`)

L'addon publie le coût calculé d'une recette dans son champ `extras` (visible
dans l'onglet *Propriétés* de chaque recette Mealie). Toutes les clés sont
préfixées `cout_` et nommées en français.

### Clés écrites par l'addon (recalculées à chaque sync)

| Clé | Description |
|-----|-------------|
| `cout_total` | Coût total (€) |
| `cout_par_portion` | Coût par portion (€) |
| `cout_devise` | Devise (`EUR`) |
| `cout_confiance` | Confiance 0–1 |
| `cout_mois_reference` | Mois du calcul (`YYYY-MM`) |
| `cout_calcule_le` | Timestamp ISO UTC |
| `cout_source` | `auto` (calculé) ou `manuel` (override actif) |

### Clés réservées à l'utilisateur (**jamais écrasées**)

| Clé | Description |
|-----|-------------|
| `cout_manuel_par_portion` | Override manuel du coût par portion |
| `cout_manuel_total` | Override manuel du coût total |
| `cout_manuel_raison` | Raison libre (ex. « promo Leclerc -30% ») |

> Pour forcer un coût : éditer la recette dans Mealie → onglet *Propriétés* →
> ajouter `cout_manuel_par_portion` = `1.50`. Le planner et l'UI utiliseront
> cette valeur et marqueront la recette comme `cout_source=manuel`.

### Rafraîchissement mensuel automatique

Un scheduler APScheduler intégré à l'API recalcule et publie le coût de toutes
les recettes, activé par défaut (1er du mois à 03:00 UTC). Variables d'env :

```bash
ENABLE_MONTHLY_COST_REFRESH=true        # false pour désactiver
MONTHLY_COST_REFRESH_CRON="0 3 1 * *"   # cron 5 champs (UTC)
```

### CLI

```bash
# Publier le coût d'une recette unique
mealie-budget sync-cost poulet-riz --month 2026-04

# Recalculer toutes les recettes
mealie-budget refresh-costs --month 2026-04
```

## 🧪 Tests rapides

```bash
# Vérifier l'API
curl http://localhost:8003/health

# Rechercher un prix
curl "http://localhost:8003/prices/search?q=farine&limit=5"

# Calculer le coût d'une recette
curl "http://localhost:8003/recipes/carbonara-marmiton/cost"

# Définir un budget
curl -X POST http://localhost:8003/budget \
  -H "Content-Type: application/json" \
  -d '{
    "period": {"year": 2026, "month": 4},
    "total_budget": 500,
    "condiments_forfait": 20,
    "meals_per_day": 3,
    "days_per_month": 30
  }'

# Suggestions d'alternatives
curl "http://localhost:8003/planning/suggest-alternatives?current_slug=carbonara-marmiton&limit=5"
```

## 🎨 UI Streamlit

L'interface utilisateur est accessible sur `http://localhost:8503` et comprend 5 onglets :

- **📊 Statut**: État du système (connexion Mealie, nombre de recettes, feature flags)
- **💰 Budget**: Gestion du budget mensuel (CRUD, historique)
- **🎯 Planning**: Suggestions d'alternatives respectant le budget
- **🏷️ Prix**: Gestion des prix manuels et recherche Open Prices
- **📈 Coûts**: Calcul du coût des recettes et comparaison budget

## 🗺️ Roadmap

### Sprint 1 ✅
- [x] Structure de base de l'addon
- [x] Modèles Pydantic (budget, cost, pricing)
- [x] Client API Open Prices
- [x] Gestion prix manuels (JSON)
- [x] API endpoints de base
- [x] UI Streamlit basique

### Sprint 2 ✅
- [x] Parser ingrédients avancé (fractions, décimales françaises)
- [x] Matching fuzzy ingrédients ↔ produits
- [x] Calcul coût recette complet
- [x] UI gestion des prix
- [x] Unit tests pour pricing
- [x] Docker build fixes

### Sprint 3 ✅
- [x] Gestion budget mensuel (CRUD)
- [x] BudgetManager avec persistance JSON
- [x] API endpoints budget
- [x] Intégration coût dans détails recette
- [x] Onglet Budget dans UI Streamlit
- [x] Comparaison budget vs coût

### Sprint 4 ✅
- [x] Planner budget-aware
- [x] Suggestions d'alternatives moins chères
- [x] Rapport coût vs budget
- [x] API endpoints planning
- [x] Onglet Planning dans UI Streamlit

### Sprint 5 🔄 (En cours)
- [x] Documenter l'API (OpenAPI/Swagger)
- [x] Créer le README de l'addon
- [ ] Ajouter tests E2E pour le workflow complet
- [ ] Documenter l'architecture et l'intégration
- [ ] Nettoyer et finaliser pour release

## 📄 Licence

MIT - Voir [LICENSE](../../LICENSE)
