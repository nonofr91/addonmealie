---
description: Vérifier qu'un changement respecte la structure du repo et n'introduit pas de pollution
---

# Workflow Repo Hygiene

Utilise ce workflow avant ou après une tâche pour contrôler la qualité structurelle du repo.

## Étapes

1. Identifier la source de vérité du sujet traité.
2. Lister les fichiers à modifier ou créer.
3. Vérifier que chaque fichier a une catégorie valide :
   - `addons/`, `packages/`, `tests/`, `docs/`, `scripts/`
   - `labs/`
   - `tmp/`
   - `reports/` ou `data/generated/`
4. Refuser toute création de fichier métier à la racine.
5. Signaler comme pollution potentielle tout nom du type `final_*`, `debug_*`, `copy`, `fixed`, `v2`, `v3`.
6. Vérifier qu'aucune logique métier n'est dupliquée dans plusieurs fichiers concurrents.
7. Proposer soit :
   - la promotion dans le module canonique
   - le déplacement vers `labs/`
   - la suppression

## Résultat attendu

Un repo plus lisible, avec une seule source de vérité par capacité métier.
