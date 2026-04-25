# ADR — Persistance du coût recette dans Mealie via ``extras``

**Statut**: Accepté
**Date**: 2026-04-23
**Contexte**: Addon `mealie-budget-advisor`

## Problème

Le coût calculé d'une recette n'est visible que dans l'UI Streamlit de l'addon
et le plan budget-aware le recalcule à chaque exécution. L'utilisateur veut :

1. Voir le coût **dans Mealie** (source de vérité visuelle).
2. Pouvoir **forcer manuellement** un coût spécifique (promo, connaissance
   terrain) sans que l'addon l'écrase.
3. Recalculer une fois par mois, pas à chaque appel, pour amortir les requêtes
   Open Prices.

## Options examinées

### A) Champ natif Mealie

Mealie ne dispose pas d'un champ natif « coût ». Le champ `nutrition` sert
uniquement aux valeurs nutritionnelles. Exclu.

### B) Base de données externe (SQLite dédié à l'addon)

Avantages : structuré, typé. Inconvénients : invisible dans l'UI Mealie,
l'utilisateur ne peut pas forcer manuellement sans passer par une API, perte
lors d'export/import Mealie. **Exclu** — casse l'exigence "choix manuel visible".

### C) Champ ``extras`` (dictionnaire libre Mealie)  ✅

Mealie expose un champ ``extras: dict[str, str]`` sur chaque recette :
- Affiché dans l'UI Mealie (onglet *Propriétés*).
- Éditable manuellement (l'utilisateur peut forcer une valeur).
- Persisté aux exports / restaurations.
- Patché via PATCH ``/api/recipes/{slug}``.

C'est le pattern déjà utilisé par `mealie-nutrition-advisor` pour
`patch_nutrition`. On applique la même mécanique, adaptée au coût.

## Décision

**Utiliser ``extras`` avec des clés préfixées ``cout_`` (toutes en français).**

### Convention de nommage

Toutes les clés sont en français, snake_case, préfixe `cout_`. Les valeurs
sont des chaînes (Mealie n'accepte que `dict[str, str]` dans `extras`).

**Clés écrites par l'addon** (recalculées à chaque sync) :

| Clé | Description |
|-----|-------------|
| `cout_total` | Coût total de la recette (€) |
| `cout_par_portion` | Coût par portion (€) |
| `cout_devise` | Devise (ex. `EUR`) |
| `cout_confiance` | Confiance 0-1 (coverage des prix connus) |
| `cout_mois_reference` | Mois du calcul (`YYYY-MM`) |
| `cout_calcule_le` | Timestamp ISO UTC du calcul |
| `cout_source` | `auto` (calculé) ou `manuel` (override actif) |

**Clés réservées à l'utilisateur** (jamais écrasées par l'addon) :

| Clé | Description |
|-----|-------------|
| `cout_manuel_par_portion` | Override manuel du coût par portion |
| `cout_manuel_total` | Override manuel du coût total |
| `cout_manuel_raison` | Libre (ex. « promo Leclerc -30% ») |

### Priorité de lecture (planner + UI)

Lorsque l'addon charge le coût d'une recette :

1. Si `cout_manuel_par_portion` est présent et numérique → c'est la valeur utilisée.
2. Sinon si `cout_manuel_total` est présent → converti en per-serving.
3. Sinon → valeur calculée (`cout_par_portion`).

La confiance est forcée à `1.0` quand un override manuel est actif.

### Garanties de préservation

L'addon ne touche **jamais** :
- Les clés `cout_manuel_*`.
- Les clés sans préfixe `cout_` (d'autres addons, tags utilisateur, etc.).

Seules les clés listées dans `ADDON_KEYS` sont remplacées à chaque sync.

## Déclenchement

1. **Manuel** : endpoint `POST /recipes/{slug}/sync-cost` ou CLI
   `mealie-budget sync-cost <slug>`.
2. **Batch manuel** : `POST /recipes/refresh-costs` ou CLI
   `mealie-budget refresh-costs`.
3. **Automatique** : cron APScheduler intégré à l'API, activé par défaut,
   expression cron `0 3 1 * *` (UTC, 1er du mois à 03:00).
   Désactivable via `ENABLE_MONTHLY_COST_REFRESH=false`.

## Conséquences

### Positives

- Coût visible dans Mealie sans écran supplémentaire.
- Override manuel simple (édition dans l'UI Mealie).
- Compatible export/import Mealie.
- Pattern identique à `mealie-nutrition-advisor` → cohérence.

### Négatives

- Les valeurs sont des chaînes (contrainte Mealie), pas des nombres.
- Ajoute une dépendance APScheduler (pure Python, légère).
- Un refresh batch sur une grande base parcourt toutes les recettes
  séquentiellement (pas de parallélisme — à évaluer si > 1000 recettes).

## Références

- Pattern `patch_nutrition` : `addons/mealie-nutrition-advisor/src/mealie_nutrition_advisor/mealie_sync.py`
- Contrainte Mealie `extras: dict[str, str]` : schéma `/api/recipes/{slug}`.
