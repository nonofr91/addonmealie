---
name: contract-review
description: Vérifie les contrats d'entrée, de sortie et les effets de bord d'un module ou addon Mealie
---

# Contract Review Skill

Utilise ce skill lorsqu'un module lit, transforme ou écrit des données Mealie et qu'il faut clarifier son contrat.

## Mission

S'assurer qu'une capacité importante a des entrées, sorties et effets de bord explicites avant ou pendant son implémentation.

## Points de revue

- quelles données entrent dans le module
- quelles transformations sont appliquées
- quelles données sont écrites dans Mealie
- quelles hypothèses sont faites sur les recettes, ingrédients, tags ou unités
- quels cas d'erreur doivent être gérés
- si le traitement est rejouable sans casser l'état

## Cas d'usage

- addon d'import de recettes
- pipeline de normalisation
- correction d'ingrédients
- audit qualité
- enrichissement nutritionnel ou image

## Résultat attendu

Une vue claire du contrat fonctionnel pour réduire les effets de bord implicites, les régressions et les doublons de logique.
