# mealie-budget-advisor

Addon externe Mealie pour :

- **Définir** un budget alimentaire mensuel (avec forfait condiments).
- **Estimer** le coût des recettes via Open Prices + une base de prix manuels.
- **Prioriser** les recettes selon leur coût relatif pour aider au choix.
- **Planifier** un menu qui respecte le budget mensuel.

> Cet addon ne modifie pas l'image Mealie. Il passe exclusivement par l'API publique.

---

## Principes

- **Assistance, pas comptabilité** : on cherche l'ordre de grandeur, pas la précision au centime.
- **Budget mensuel** modifiable par l'utilisateur, scope foyer entier.
- **Forfait condiments** : le budget effectif est `total - forfait` (par défaut 20 €/mois) pour couvrir huile, sel, épices non comptabilisés dans les recettes.
- **Valeurs relatives** : même quand les prix sont estimés, l'ordre relatif entre recettes reste exploitable.

---

## Installation

### Installation locale

```bash
pip install -e "addons/mealie-budget-advisor"
pip install fastapi "uvicorn[standard]" streamlit requests
```

### Variables d'environnement

```bash
cp addons/mealie-budget-advisor/.env.template .env
# Remplir MEALIE_BASE_URL et MEALIE_API_KEY
```

Voir `.env.template` pour la liste complète (Open Prices, ports, feature flags).

---

## Utilisation

### CLI

```bash
# Statut de l'addon
mealie-budget status

# Définir le budget du mois
mealie-budget budget-set --month 2026-04 --total 500 --forfait 20

# Lire le budget d'un mois
mealie-budget budget-get --month 2026-04

# Ajouter un prix manuel
mealie-budget price-add --name poulet --unit kg --price 9.50

# Coût d'une recette
mealie-budget recipe-cost poulet-roti

# Planning budget-aware
mealie-budget plan --month 2026-04 --meals 21

# Publier le coût d'une recette dans Mealie (extras.cout_*)
mealie-budget sync-cost poulet-roti

# Rafraîchir tous les coûts Mealie (tâche mensuelle manuelle)
mealie-budget refresh-costs --month 2026-04
```

### Persistance du coût dans Mealie (extras)

Le coût calculé est publié dans le champ `extras` (libre) de la recette, sous
des clés préfixées `cout_*`. Elles apparaissent dans l'onglet *Propriétés* de
la fiche recette Mealie et peuvent être éditées manuellement pour forcer une
valeur.

| Clé | Écrite par | Rôle |
|-----|-----------|------|
| `cout_total` | addon | Coût total calculé (string, 2 décimales) |
| `cout_par_portion` | addon | Coût par portion |
| `cout_devise` | addon | `EUR` par défaut |
| `cout_confiance` | addon | Ratio d'ingrédients avec prix résolu |
| `cout_mois_reference` | addon | Mois du calcul (`YYYY-MM`) |
| `cout_calcule_le` | addon | Horodatage ISO8601 UTC |
| `cout_source` | addon | `auto` |
| `cout_manuel_par_portion` | **utilisateur** | Override manuel par portion (prioritaire) |
| `cout_manuel_total` | **utilisateur** | Override manuel total (prioritaire) |
| `cout_manuel_raison` | **utilisateur** | Libre : raison de l'override |

Règles :

- L'addon ne touche **jamais** aux clés `cout_manuel_*` lors d'un recalcul.
- Les autres extras (ex. `nutrition_calories` d'un autre addon) sont préservés.
- Si `cout_manuel_par_portion` ou `cout_manuel_total` est présent, il prend la
  priorité sur la valeur calculée dans `/recipes/{slug}/cost` et dans le
  planning.

### Rafraîchissement mensuel automatique

Un `APScheduler` interne (activé par défaut) relance `refresh-costs` le **1er
du mois à 03:00 UTC**. Pilotage via env :

- `ENABLE_MONTHLY_COST_REFRESH=true|false` (défaut `true`)
- `MONTHLY_COST_REFRESH_CRON="0 3 1 * *"` (expression cron 5-champs UTC)

### API FastAPI (port 8003)

```bash
PYTHONPATH=addons/mealie-budget-advisor/src \
MEALIE_BASE_URL=http://127.0.0.1:9925 \
MEALIE_API_KEY=votre_clé \
ADDON_SECRET_KEY=votre_secret \
uvicorn mealie_budget_advisor.api:app --host 0.0.0.0 --port 8003
```

Endpoints principaux :

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/status` | Statut (connexions + couverture prix) |
| GET | `/budget?month=YYYY-MM` | Lire le budget |
| POST | `/budget` | Définir / modifier le budget |
| GET | `/prices/manual` | Lister les prix manuels |
| POST | `/prices/manual` | Ajouter / modifier un prix manuel |
| DELETE | `/prices/manual/{name}` | Supprimer un prix manuel |
| GET | `/prices/search?q={query}` | Recherche Open Prices |
| GET | `/recipes/{slug}/cost` | Coût d'une recette (applique l'override si présent) |
| POST | `/recipes/batch-cost` | Coût de plusieurs recettes |
| POST | `/recipes/{slug}/sync-cost` | Publie `cout_*` dans `extras` Mealie pour une recette |
| POST | `/recipes/refresh-costs` | Recalcule et publie le coût de toutes les recettes |
| POST | `/plan/budget-aware` | Planning respectant le budget |

Authentification optionnelle via `X-Addon-Key` si `ADDON_SECRET_KEY` est défini.

### UI Streamlit (port 8503)

```bash
PYTHONPATH=addons/mealie-budget-advisor/src \
ADDON_API_URL=http://localhost:8003 \
ADDON_SECRET_KEY=votre_secret \
MEALIE_BASE_URL=http://127.0.0.1:9925 \
streamlit run src/mealie_budget_advisor/ui.py \
  --server.port=8503 --server.headless=true \
  --browser.gatherUsageStats=false --server.fileWatcherType=none
```

Onglets :

- **Budget** : définir/consulter le budget mensuel
- **Prix** : CRUD prix manuels + recherche Open Prices
- **Coût recette** : estimer le coût d'une recette
- **Planning** : générer un menu respectant le budget

### Docker

```bash
cd addons/mealie-budget-advisor
docker-compose up -d
```

Services :

- API budget : http://localhost:8003
- UI budget  : http://localhost:8503

---

## Architecture

```
addons/mealie-budget-advisor/
├── src/mealie_budget_advisor/
│   ├── api.py / ui.py / cli.py / config.py / orchestrator.py
│   ├── mealie_sync.py
│   ├── budget_manager.py
│   ├── models/        # BudgetSettings, RecipeCost, pricing
│   ├── pricing/       # Open Prices, manual pricer, matcher, cost calculator
│   └── planning/      # Budget scorer + planner
├── data/              # ingredient_prices.json (gitignored)
├── config/            # budget_settings.json (gitignored)
├── tests/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

### Intégration avec `mealie-nutrition-advisor`

L'intégration se fait via API externe. L'addon nutrition peut interroger
`POST /plan/budget-aware` pour vérifier qu'un menu équilibré reste dans le
budget, ou `POST /recipes/batch-cost` pour obtenir les coûts des candidats.

---

## Limitations connues

- **Open Prices** a une couverture variable selon les régions et catégories. La
  base de prix manuels est la source de vérité recommandée pour les produits
  frais / ingrédients courants.
- **Matching ingrédients** : normalisation textuelle simple. Les ingrédients
  non matchés tombent sur une estimation statique (fallback) qui préserve
  l'ordre relatif des coûts.
- **Unités complexes** (pots, tranches, etc.) sont rabattues sur g/ml via un
  tableau statique — les ordres de grandeur sont fiables, la précision
  absolue ne l'est pas.
