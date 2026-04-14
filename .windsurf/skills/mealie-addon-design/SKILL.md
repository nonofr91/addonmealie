---
name: mealie-addon-design
description: Conçoit un addon externe à Mealie sans modifier l'image Mealie, avec frontières claires et intégration publique
---

# Mealie Addon Design Skill

Utilise ce skill pour cadrer ou implémenter une nouvelle capacité autour de Mealie sous forme de module externe.

## Mission

Concevoir des addons externes à Mealie, maintenables et publiables, sans fork ni image Mealie modifiée.

## Principes

- Mealie reste stock
- toute intégration passe par une interface publique
- toute capacité a un périmètre clair
- les effets de bord sur Mealie sont explicités
- la sécurité et la configuration sont externalisées

## Questions à traiter

1. Quel problème l'addon résout-il ?
2. Existe-t-il déjà un module canonique qui couvre cette capacité ?
3. Quel est le mode d'intégration : MCP, worker, pipeline, CLI, service ?
4. Quelles sont les entrées, sorties et validations ?
5. Quels sont les risques de duplication, corruption ou couplage fort ?
6. Quelle documentation minimale faudra-t-il ?

## Résultat attendu

- une spec courte
- un module placé au bon endroit
- un découpage propre entre logique partagée et logique spécifique
- une intégration externe à Mealie, sans dette structurelle inutile
