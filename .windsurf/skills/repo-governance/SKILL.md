---
name: repo-governance
description: Applique les règles de structure du repo, évite la pollution des fichiers et protège la source de vérité
---

# Repo Governance Skill

Utilise ce skill quand une tâche risque d'introduire des fichiers parasites, de dupliquer une capacité métier ou de modifier la structure du repo.

## Mission

Aider Cascade à prendre les bonnes décisions de placement, de promotion ou de suppression de fichiers pour garder le repo propre et maintenable.

## Décisions à prendre systématiquement

1. Identifier la source de vérité de la capacité concernée.
2. Déterminer si le changement doit aller dans :
   - `addons/`
   - `packages/`
   - `tests/`
   - `docs/`
   - `scripts/`
   - `labs/`
   - `tmp/`
   - `reports/` ou `data/generated/`
3. Refuser tout nouveau fichier métier à la racine.
4. Refuser les noms `final`, `debug`, `copy`, `backup`, `new`, `fixed`, `v2`, `v3`.
5. Si une expérimentation devient utile, la promouvoir dans le module canonique au lieu de la laisser dériver.

## Règles d'arbitrage

- Modifier un module existant plutôt que créer une variante
- Déplacer une exploration vers `labs/` plutôt que la laisser à la racine
- Supprimer un fichier temporaire plutôt que le conserver "au cas où"
- Préférer une règle versionnée à une consigne implicite en mémoire

## Check final

- une seule source de vérité
- pas de fichier parasite
- pas de secret dans le code
- pas de duplication métier
