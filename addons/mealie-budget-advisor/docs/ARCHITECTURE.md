# Architecture du Mealie Budget Advisor

## Vue d'ensemble

Le Mealie Budget Advisor est un addon externe pour Mealie qui fournit :
- Estimation des coûts des recettes
- Gestion des prix (manuels + Open Prices)
- Planification budget-aware
- Interface utilisateur Streamlit

## Architecture

### Composants

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI (8503)                   │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │
│  │Statut  │ │Budget  │ │Planning│ │ Prix   │ │ Coûts  │ │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI REST API (8003)                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │   Budget    │ │  Planning   │ │  Pricing    │       │
│  │  Manager    │ │   Planner   │ │  Endpoints  │       │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Mealie     │   │ Open Prices  │   │   Local      │
│    API       │   │    API       │   │   Storage    │
└──────────────┘   └──────────────┘   └──────────────┘
```

### Modules

#### 1. API Layer (`api.py`)

Point d'entrée FastAPI avec endpoints pour :
- Health check (`/health`)
- Status (`/status`)
- Budget management (`/budget/*`)
- Pricing (`/prices/*`)
- Recipe costs (`/recipes/*`)
- Planning (`/planning/*`)

#### 2. Budget Module (`planning/`)

- **BudgetManager**: Gestion CRUD du budget mensuel avec persistance JSON
- **BudgetAwarePlanner**: Suggestions d'alternatives respectant le budget

#### 3. Pricing Module (`pricing/`)

- **OpenPricesClient**: Client API pour Open Prices (OFF)
- **ManualPricer**: Gestion des prix manuels (JSON local)
- **IngredientMatcher**: Matching fuzzy ingrédients ↔ produits
- **CostCalculator**: Calcul du coût des recettes

#### 4. Models (`models/`)

- **BudgetSettings**: Configuration du budget (période, total, repas/jour)
- **BudgetPeriod**: Période de budget (année, mois)
- **RecipeCost**: Coût d'une recette avec breakdown
- **IngredientCost**: Coût par ingrédient
- **PriceSource**: Source de prix (manual, open_prices, estimated)

#### 5. UI Layer (`ui.py`)

Interface Streamlit avec 5 onglets :
- Statut : État du système
- Budget : Gestion budget mensuel
- Planning : Suggestions alternatives
- Prix : Gestion prix manuels
- Coûts : Calcul coût recettes

## Flux de données

### Calcul du coût d'une recette

```
1. User → UI → API: GET /recipes/{slug}/cost
2. API → Mealie: Récupérer la recette
3. API → IngredientMatcher: Parser les ingrédients
4. API → ManualPricer: Chercher prix manuels
5. API → OpenPricesClient: Chercher prix fallback
6. API → CostCalculator: Calculer le coût
7. API → UI: Retourner le coût avec breakdown
```

### Planning budget-aware

```
1. User → UI → API: POST /budget (définir budget)
2. API → BudgetManager: Sauvegarder en JSON
3. User → UI → API: GET /planning/suggest-alternatives
4. API → BudgetManager: Récupérer budget actuel
5. API → Mealie: Récupérer toutes les recettes
6. API → CostCalculator: Calculer coûts batch
7. API → BudgetAwarePlanner: Filtrer alternatives respectant budget
8. API → UI: Retourner suggestions
```

## Intégration Mealie

### Endpoints Mealie utilisés

- `GET /api/recipes/{slug}`: Récupérer une recette
- `GET /api/recipes`: Lister toutes les recettes
- `GET /api/foods`: Lister les foods (pour matching)

### Authentification

Token API Mealie requis :
```
MEALIE_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Configuration

Variables d'environnement :
```env
MEALIE_BASE_URL=http://localhost:9925
MEALIE_API_KEY=your-token
OPEN_PRICES_BASE_URL=https://prices.openfoodfacts.org/api/v1
```

## Persistance

### Budgets

Fichier : `config/budgets.json`
```json
{
  "2026-04": {
    "period": {"year": 2026, "month": 4},
    "total_budget": 500,
    "condiments_forfait": 20,
    "meals_per_day": 3,
    "days_per_month": 30
  }
}
```

### Prix manuels

Fichier : `data/manual_prices.json`
```json
{
  "farine": {
    "ingredient_name": "farine",
    "price": 1.50,
    "unit": "kg",
    "source": "manual"
  }
}
```

## Sécurité

- Aucun secret hardcodé dans le code
- Secrets via variables d'environnement
- `.env` et `.env.*` dans `.gitignore`
- CORS activé pour développement

## Performance

- Caching des prix manuels en mémoire
- Batch processing pour calculs de coûts
- Matching fuzzy avec RapidFuzz (rapide)
- Open Prices avec timeout

## Extensibilité

### Ajouter une nouvelle source de prix

1. Créer un client dans `pricing/`
2. Intégrer dans `CostCalculator`
3. Ajouter dans `PriceSource` enum

### Ajouter un nouveau planner

1. Créer une classe dans `planning/`
2. Exposer via `__init__.py`
3. Ajouter endpoints API
4. Ajouter onglet UI

## Déploiement

### Docker

```bash
docker compose up -d
```

### Ports

- API: 8003
- UI: 8503

### Health Check

```bash
curl http://localhost:8003/health
```

## Monitoring

- Logs niveau DEBUG configurables
- Health check endpoint
- Status endpoint avec métriques
