# Ingredient Price Collector

Addon externe à Mealie chargé de collecter, normaliser et exposer des prix d'ingrédients pour les autres addons, notamment `mealie-budget-advisor`.

## Périmètre MVP

- API FastAPI autonome
- Stockage local SQLite
- Import d'observations JSON et CSV
- Normalisation des prix en €/kg, €/l ou €/pièce
- Scoring de confiance minimal
- Endpoint de recommandation `/prices/search`
- Aucun scraping et aucune dépendance directe à Mealie

## Configuration

Copier le template localement :

```bash
cp .env.template .env
```

Variables disponibles :

```env
PRICE_COLLECTOR_API_PORT=8004
PRICE_COLLECTOR_DEFAULT_CURRENCY=EUR
LOG_LEVEL=INFO
```

## Démarrage Docker

```bash
docker compose up -d
```

API : `http://localhost:8004`

## Endpoints

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/status` | Statut et configuration non sensible |
| POST | `/prices/import` | Import JSON typé |
| POST | `/prices/import/json` | Import JSON souple avec alias de colonnes |
| POST | `/prices/import/csv` | Import CSV multipart |
| POST | `/prices/collect/open_prices?ingredient=oignons` | Collecte depuis Open Prices API |
| POST | `/prices/collect/insee_ipc?ingredient=oignons&base_price=2.4&base_unit=kg` | Fallback par catégorie INSEE IPC |
| GET | `/prices/search?ingredient=oignons&unit=kg` | Recherche une recommandation de prix |
| GET | `/prices/anomalies` | Liste les observations avec flags qualité |

## Format CSV MVP

Colonnes recommandées :

```csv
ingredient_name,product_name,price_amount,currency,package_quantity,package_unit,store_name,observed_at
Oignons,Oignons jaunes,2.40,EUR,1,kg,Carrefour,2026-05-07
```

Alias acceptés :

- `ingredient` → `ingredient_name`
- `product` → `product_name`
- `price` → `price_amount`
- `quantity` → `package_quantity`
- `unit` → `package_unit`
- `store` → `store_name`
- `date` → `observed_at`

## Exemple de recherche

```bash
curl "http://localhost:8004/prices/search?ingredient=oignons&unit=kg"
```

## Tests

Des tests unitaires couvrent la normalisation, l'import CSV/JSON et le stockage SQLite :

```bash
pytest tests
```

## Garde-fous

- L'addon ne modifie pas Mealie.
- Les secrets et URLs sensibles doivent rester en variables d'environnement.
- Les prix issus de l'IA doivent être marqués `source=ai_estimate` et sont plafonnés à `confidence <= 0.5`.
- Les collecteurs drive sont optionnels et désactivés par défaut (voir Phase 4).

## Intégration avec Budget Advisor

Le collecteur peut être intégré dans `mealie-budget-advisor` pour remplacer ou compléter Open Prices brut.

### Pattern d’intégration suggéré

Budget Advisor doit interroger le collecteur avant Open Prices brut :

```text
1. Prix manuel de la recette ou ingrédient
2. Recommandation du collecteur (GET /prices/search)
3. Open Prices filtré
4. Estimation par catégorie
5. Inconnu
```

### Exemple de requête

```bash
curl "http://localhost:8004/prices/search?ingredient=oignons&unit=kg"
```

Réponse exploitable dans les notes Mealie :

```json
{
  "ingredient": "oignons",
  "normalized_ingredient": "oignon",
  "price": 2.4,
  "unit": "kg",
  "source": "manual_import",
  "confidence": 0.95,
  "reason": "Prix manual_import observé chez Carrefour le 2026-05-07",
  "warnings": []
}
```

### Configuration Budget Advisor

Ajouter dans le `.env` de Budget Advisor :

```env
PRICE_COLLECTOR_URL=http://localhost:8004
ENABLE_PRICE_COLLECTOR=true
```

Le client Budget Advisor doit interroger `PRICE_COLLECTOR_URL/prices/search` avant Open Prices.

## Phase 4 : Scraping Drive (Optionnel)

Le scraping drive est désactivé par défaut pour des raisons légales et éthiques.

### Risques

- Violation potentielle des conditions d'utilisation des sites drive
- Charge excessive sur les serveurs des drive (DoS involontaire)
- Données pouvant être obsolètes ou incorrectes
- Maintenance lourde (les sites changent souvent)

### Activation

Pour activer le scraping drive, définir la variable d'environnement :

```env
ENABLE_DRIVE_SCRAPING=true
```

### Garde-fous

- **Cache TTL** : Les résultats sont mis en cache pendant 24h par défaut (`DRIVE_CACHE_TTL_HOURS`)
- **Rate limiting** : Délai entre les requêtes (`DRIVE_RATE_LIMIT_DELAY`, défaut 1 seconde)
- **Désactivé par défaut** : `ENABLE_DRIVE_SCRAPING=false` par défaut

### Endpoint

```bash
curl -X POST "http://localhost:8004/prices/collect/drive?ingredient=oignons&store=Carrefour"
```

**Note** : L'implémentation actuelle est un mock (`_mock_drive_scrape`). Le scraping réel nécessite une implémentation spécifique par drive (E.Leclerc, Carrefour, etc.) et doit respecter les conditions d'utilisation de chaque site.
