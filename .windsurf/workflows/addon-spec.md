---
description: Cadrer un nouvel addon externe pour Mealie avant implémentation
---

# Workflow Addon Spec

Utilise ce workflow pour définir proprement un addon externe à Mealie avant toute implémentation.

## Objectif

Produire une spécification courte et exploitable sans modifier l'image Mealie et sans créer de fichier parasite.

## Étapes

1. Vérifier si la capacité demandée existe déjà dans un module canonique.
2. Si elle existe, enrichir le module existant au lieu de créer un nouvel addon.
3. Si elle n'existe pas, définir :
   - le problème traité
   - le périmètre et les non-objectifs
   - le mode d'intégration externe à Mealie
   - les entrées, sorties et effets de bord
   - les risques de qualité et de duplication
   - les validations attendues
4. Enregistrer la spec dans `docs/specs/` avec un nom clair et stable.
5. Proposer ensuite un plan d'implémentation limité aux modules canoniques concernés.

## Rappels

- Ne jamais créer un fichier métier à la racine
- Ne jamais utiliser `final`, `debug`, `copy`, `v2`
- Préférer `Plan mode` pour tout addon nouveau ou tout changement non trivial
