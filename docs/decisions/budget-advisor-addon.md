# Budget Advisor Addon

## Contexte

Les utilisateurs souhaitent définir un budget alimentaire mensuel et obtenir
une aide au choix des recettes selon leur coût estimé. Cette capacité
n'existe dans aucun addon canonique et ne doit pas vivre dans Mealie.

## Décision

Implémenter un nouvel addon externe `mealie-budget-advisor`, séparé de
`mealie-nutrition-advisor`, selon le pattern "un addon = une responsabilité".
L'addon expose :

- une API FastAPI (port 8003) avec endpoints budget, prix, coût recettes,
  planning budget-aware
- une UI Streamlit (port 8503) avec 4 onglets (Budget / Prix / Coût / Plan)
- une CLI `mealie-budget`

L'addon suit la convention de gouvernance du repo : emplacement canonique
(`addons/mealie-budget-advisor/`), stockage local JSON pour le budget
(`config/budget_settings.json`) et les prix manuels (`data/ingredient_prices.json`),
intégration Mealie en lecture seule via l'API publique.

## Rationale

### Pourquoi un addon séparé

- Respecte la règle "une capacité métier, un module canonique".
- Les concerns (nutrition vs budget) sont orthogonaux ; les fusionner rendrait
  l'API et l'UI plus difficiles à raisonner.
- L'intégration entre les deux addons se fait via HTTP (endpoint
  `POST /plan/budget-aware` côté budget, appelable par nutrition).

### Sources de prix

| Source | Usage |
|--------|-------|
| Base manuelle (`data/ingredient_prices.json`) | Source prioritaire — prix renseignés par l'utilisateur |
| Open Prices API (Open Food Facts) | Fallback — prix réels constatés en magasin |
| Estimation statique (`_FALLBACK_ESTIMATES`) | Dernier recours — garantit un ordre de grandeur |

Le parti-pris explicite : l'addon est une **aide au choix**, pas une
comptabilité exacte. Les valeurs relatives suffisent pour prioriser
les recettes.

### Forfait condiments

Le budget effectif est calculé comme `total_budget - condiments_forfait`
(par défaut 20 €/mois) pour absorber les petites quantités (huile, sel,
épices) non comptabilisées dans les recettes.

## Conséquences

- Nouveau service Docker ajouté dans `docker-compose.yml`.
- Tags Docker dédiés `budget-v*` gérés par `.github/workflows/docker-publish.yml`.
- Les prix manuels et les budgets ne sont pas commités (gitignorés dans
  `addons/mealie-budget-advisor/data/` et `config/`).
- Peut être fusionné plus tard avec `nutrition-advisor` si l'expérience
  utilisateur le demande, sans perte de données (le format JSON est stable).
