---
description: Diagnostiquer un bug avant d'appliquer une correction
---

# Workflow Bug Investigation

Utilise ce workflow pour traiter un bug sans corriger seulement les symptômes.

## Étapes

1. Décrire le symptôme observé, le contexte et l'impact utilisateur.
2. Identifier le module canonique responsable et les éventuels consommateurs affectés.
3. Rechercher le chemin de données, les hypothèses et les invariants impliqués.
4. Reproduire le problème ou collecter suffisamment d'indices fiables pour le localiser.
5. Isoler la cause racine avant toute modification de code.
6. Définir la validation attendue : test ciblé, reproduction manuelle, logs, non-régression.
7. N'implémenter la correction qu'une fois la cause racine suffisamment comprise.

## Résultat attendu

Un diagnostic clair, centré sur la cause racine et prêt à être implémenté proprement.
