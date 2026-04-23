# ADR — Persistance du coût recette dans Mealie (`extras`)

## Contexte

L'addon `mealie-budget-advisor` calcule le coût d'une recette à la volée
(API + UI + CLI). Pour faciliter les choix manuels côté utilisateur, il faut
rendre ce coût visible **directement dans Mealie** et permettre un override
manuel persistant, avec un rafraîchissement mensuel automatique.

## Décision

1. **Cible d'écriture** : champ `extras` (dict libre string→string) d'une
   recette Mealie, patché via `PATCH /api/recipes/{slug}`.
2. **Namespace de clés** : toutes les clés de l'addon sont préfixées
   `cout_*` et nommées en français (cohérent avec la langue fonctionnelle
   du dépôt). Liste exhaustive dans le README de l'addon.
3. **Override manuel** : trois clés réservées à l'utilisateur
   (`cout_manuel_par_portion`, `cout_manuel_total`, `cout_manuel_raison`).
   L'addon ne les écrit jamais. Lorsqu'un override est présent, il
   prend le pas sur la valeur calculée dans l'API et dans le planning.
4. **Préservation** : avant chaque PATCH, l'addon relit les `extras`
   existants et fusionne uniquement ses propres clés — aucune autre
   donnée (nutrition, tags free-form) n'est touchée.
5. **Rafraîchissement mensuel** : `APScheduler` (`BackgroundScheduler`)
   démarré dans le cycle de vie FastAPI, tâche cron `0 3 1 * *` (UTC)
   par défaut, pilotable par `ENABLE_MONTHLY_COST_REFRESH` /
   `MONTHLY_COST_REFRESH_CRON`.
6. **Déclencheurs manuels** : endpoints `POST /recipes/{slug}/sync-cost` et
   `POST /recipes/refresh-costs`, CLI `mealie-budget sync-cost` /
   `refresh-costs`, bouton dans l'UI Streamlit.

## Alternatives écartées

- **Sidecar container cron** : ajoute un conteneur et un couplage externe
  là où APScheduler suffit dans le process API existant.
- **Champ `nutrition`** : déjà utilisé par `mealie-nutrition-advisor`.
  Mélanger deux sémantiques dans un même champ serait ambigu.
- **Store externe** : inutile, `extras` Mealie est fait pour ça et
  restitue les valeurs dans l'UI native.

## Conséquences

- Aucune modification de l'image Mealie.
- Contraintes de sérialisation : `extras` n'accepte que des strings,
  on formate explicitement les nombres (`f"{x:.2f}"`).
- Dépendance ajoutée : `apscheduler>=3.10`.
- Version de l'addon bumpée à `0.2.0`.
