---
description: Qualifier une demande avant d'entrer en planification ou en implémentation
---

# Workflow Task Intake

Utilise ce workflow au début d'une demande pour éviter les changements mal cadrés et limiter la pollution du repo.

## Étapes

1. Reformuler l'objectif utilisateur en une phrase exploitable.
2. Identifier la capacité métier concernée et sa source de vérité actuelle.
3. Déterminer si la tâche relève de `Ask mode`, `Plan mode`, `Code mode` ou `Worktree mode`.
4. Lister les fichiers ou dossiers canoniques potentiellement impactés.
5. Déterminer si une spec courte est requise dans `docs/specs/`.
6. Définir les validations attendues : tests, vérifications fonctionnelles, nettoyage, documentation.
7. Si le besoin reste ambigu, poser une question ciblée avant toute implémentation.

## Résultat attendu

Un cadrage court, actionnable et aligné avec la structure canonique du repo.
