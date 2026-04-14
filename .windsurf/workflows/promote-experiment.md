---
description: Transformer une expérimentation utile en implémentation canonique sans dupliquer la logique
---

# Workflow Promote Experiment

Utilise ce workflow lorsqu'une expérimentation dans `labs/` ou un script temporaire devient utile au produit.

## Étapes

1. Identifier le comportement réellement validé par l'expérimentation.
2. Déterminer le module canonique qui doit absorber cette logique.
3. Extraire la logique réutilisable hors du script exploratoire.
4. Intégrer cette logique dans le module canonique.
5. Ajouter ou mettre à jour les validations nécessaires.
6. Supprimer l'expérimentation devenue inutile ou la laisser explicitement dans `labs/` si elle reste exploratoire.

## Rappels

- Ne jamais garder deux implémentations concurrentes en parallèle
- Le script exploratoire n'est pas une source de vérité
- Toute promotion doit réduire la dette structurelle du repo
