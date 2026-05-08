# Addon collecteur de prix ingrédients

## Objectif

Créer un addon externe à Mealie chargé de collecter, normaliser et exposer des prix d'ingrédients fiables pour les autres addons, en particulier `mealie-budget-advisor`.

L'addon doit améliorer la fiabilité des coûts de recettes sans modifier Mealie et sans intégrer directement du scraping fragile dans le Budget Advisor.

## Problème traité

Le Budget Advisor sait convertir des quantités culinaires en quantités valorisées, mais les prix sources peuvent être peu fiables :

- mauvais matching produit Open Prices
- prix au kg aberrants
- absence de prix pour les ingrédients bruts
- prix dépendants d'un magasin ou d'une période
- difficulté à distinguer prix réel, indice statistique et estimation

Exemple constaté :

```text
oignons : 150 g × 27,67 €/kg = 4,15 €
```

Le collecteur doit fournir une source plus contrôlée, traçable et explicable.

## Nom de travail

`addons/ingredient-price-collector/`

## Responsabilité

L'addon devient la source de vérité pour :

- ingestion de prix ou indices externes
- normalisation des prix en unités comparables
- stockage local historisé
- scoring de fiabilité
- exposition d'une API interne de recherche de prix

Il ne doit pas calculer le coût complet des recettes. Cette responsabilité reste dans `mealie-budget-advisor`.

## Non-objectifs

- modifier l'image Mealie
- écrire directement dans la base Mealie
- scraper massivement des sites e-commerce
- contourner des protections anti-bot
- remplacer Open Prices
- dupliquer le calcul de coût recette du Budget Advisor
- faire de l'IA une source brute de prix non vérifiée

## Sources de données candidates

### 1. Prix manuels et imports personnels

Source prioritaire pour la fiabilité locale.

Entrées possibles :

- CSV manuel
- export de courses
- ticket ou facture drive
- saisie UI/API

Champs attendus :

- ingrédient ou produit
- prix payé
- unité ou conditionnement
- quantité nette
- magasin
- date
- preuve optionnelle

Usage : prix observé réel, haute confiance.

### 2. Open Prices / Open Food Facts

Source ouverte existante.

Références :

- Dataservice data.gouv : `686109bf2ab1acc14382486f`
- API schema : `https://prices.openfoodfacts.org/api/schema`
- Documentation : `https://prices.openfoodfacts.org/api/docs`

Usage : source ouverte à conserver, mais filtrée.

Contraintes :

- couverture variable
- prix parfois aberrants
- matching produit à contrôler
- produits packagés plus fiables que produits bruts

### 3. INSEE - Indice des prix à la consommation

Source statistique utile pour tendances et fallback, pas pour prix de panier exact.

Références :

- Dataset data.gouv : `6983dff81f90da358ccf74d8`
- Ressource CSV : `5961e778-380b-4098-9b7e-33697b44b3c6`
- URL ressource : `https://api.insee.fr/melodi/file/DS_IPC_PRINC/DS_IPC_PRINC_CSV_FR`
- Exemple utilisateur : `https://www.insee.fr/fr/statistiques/series/103157792`

Usage envisagé :

- suivre l'évolution mensuelle des prix par familles COICOP
- actualiser des prix de référence locaux
- détecter des tendances d'inflation
- alimenter des estimations par catégorie

Limite importante : l'INSEE fournit surtout des indices, pas toujours des prix absolus exploitables directement pour `1 kg d'oignons`.

### 4. FranceAgriMer / RNM

Source potentiellement pertinente pour fruits, légumes, produits frais et marchés.

Référence à explorer :

- `https://rnm.franceagrimer.fr/`

Usage possible : prix moyens de produits frais, selon disponibilité et conditions d'accès.

### 5. Sites drive et e-commerce

Exemples :

- Carrefour
- E.Leclerc
- Intermarché
- Auchan
- Courses U

Usage possible : collecte ponctuelle et cache local.

Contraintes fortes :

- prix dépendants du magasin
- rendu JavaScript
- anti-bot fréquent
- APIs internes non stables
- CGU à respecter
- fréquence très limitée

Constat initial : `https://www.carrefour.fr/s?q=oeufs` renvoie une vérification anti-bot via Cloudflare dans un contexte serveur.

## Architecture proposée

```text
ingredient-price-collector
├── collectors
│   ├── manual_import
│   ├── open_prices
│   ├── insee_ipc
│   ├── rnm_franceagrimer
│   └── drive_scraping_optional
├── normalizer
│   ├── units
│   ├── packaging
│   ├── ingredient_aliases
│   └── price_per_unit
├── quality
│   ├── category_guards
│   ├── outlier_detection
│   └── confidence_scoring
├── storage
│   ├── price_observations
│   ├── source_runs
│   └── ingredient_price_index
└── api
    ├── search price by ingredient
    ├── import observations
    ├── list sources
    └── health
```

## Modèle de données minimal

### PriceObservation

```text
id
ingredient_name
normalized_ingredient
product_name
barcode
source
source_url
store_name
store_location
observed_at
price_amount
currency
package_quantity
package_unit
price_per_kg
price_per_l
price_per_piece
confidence
quality_flags
raw_payload_ref
created_at
```

### PriceRecommendation

```text
ingredient_name
normalized_ingredient
recommended_price
recommended_unit
source
confidence
reason
observed_at
valid_until
alternatives
warnings
```

## API interne cible

### Rechercher un prix

```http
GET /prices/search?ingredient=oignons&unit=kg&store=carrefour
```

Réponse :

```json
{
  "ingredient": "oignons",
  "normalized_ingredient": "oignon",
  "price": 2.4,
  "unit": "kg",
  "source": "manual_import",
  "confidence": 0.95,
  "reason": "Prix personnel récent observé en magasin",
  "observed_at": "2026-05-07",
  "warnings": []
}
```

### Importer des observations

```http
POST /prices/import
```

Formats envisagés :

- JSON
- CSV
- ticket/facture transformé en JSON

### Lister les anomalies

```http
GET /prices/anomalies
```

Objectif : revoir les prix rejetés ou suspects.

## Intégration avec Budget Advisor

Le Budget Advisor doit interroger le collecteur avant Open Prices brut :

```text
1. prix manuel recette ou ingrédient
2. ingredient-price-collector recommendation
3. Open Prices filtré
4. estimation par catégorie
5. inconnu
```

Le collecteur doit retourner une explication exploitable dans les notes Mealie :

```text
Source : collecteur local
Raison : prix observé Carrefour du 2026-05-07
Prix retenu : 2,40 €/kg
```

## Rôle de l'IA

L'IA peut aider pour :

- classification d'ingrédients inconnus
- extraction structurée depuis ticket ou facture
- mapping produit → ingrédient
- détection de prix absurdes
- génération d'explication utilisateur

L'IA ne doit pas être la source brute du prix. Toute estimation IA doit être marquée comme :

```text
source = ai_estimate
confidence <= 0.5
```

## Garde-fous scraping

Si un collecteur drive est ajouté :

- désactivé par défaut
- configuration explicite par source
- cache obligatoire
- rate limit strict
- timeout court
- respect de `robots.txt` et des CGU
- pas de contournement de CAPTCHA/anti-bot
- journalisation des échecs sans secret
- mode dry-run possible

## Priorités de première implémentation

### Phase 1 - MVP sans scraping

- créer addon `addons/ingredient-price-collector/`
- API FastAPI minimale
- stockage local SQLite ou JSONL version non sensible
- import CSV manuel
- connecteur Open Prices existant ou réutilisable
- normalisation unité/prix au kg/l/pièce
- endpoint `/prices/search`

### Phase 2 - Données publiques

- connecteur INSEE IPC pour indices par catégorie
- table de mapping ingrédient → catégorie IPC/COICOP
- fallback par catégorie avec actualisation par indice
- exploration FranceAgriMer/RNM

### Phase 3 - Qualité et intégration

- bornes réalistes par catégorie
- scoring de confiance
- API anomalies
- intégration Budget Advisor
- affichage source/raison dans les notes Mealie

### Phase 4 - Collecte drive optionnelle

- étude Playwright ou API interne par enseigne
- stockage uniquement en cache local
- pas de scraping massif
- activation manuelle par configuration

## Questions ouvertes pour la prochaine session

1. Le MVP doit-il utiliser SQLite, JSONL ou les deux ?
2. Quel format CSV d'import manuel choisir ?
3. Faut-il exposer une UI Streamlit dès le MVP ou seulement une API ?
4. Quelle granularité pour les catégories de prix ?
5. Quels magasins/sources prioriser ?
6. Souhaite-t-on importer les prix depuis des tickets/factures avant le scraping drive ?

## Critères d'acceptation MVP

- aucun fichier métier à la racine
- addon autonome dans `addons/ingredient-price-collector/`
- configuration par variables d'environnement
- aucune clé ou URL sensible hardcodée
- au moins un import CSV fonctionnel
- endpoint de recherche de prix stable
- réponse avec prix, unité, source, confiance et raison
- documentation minimale de démarrage
- pas de dépendance directe à Mealie pour la collecte
- intégration Budget Advisor laissée explicite mais non obligatoire au premier commit
