---
trigger: model_decision
description: Contraintes métier génériques à appliquer quand une tâche touche le projet.
---

# Generic Domain

- Construire des solutions propres et maintenables.
- Préférer les modules canoniques aux duplications.
- Les intégrations doivent passer par des interfaces publiques et rester publiables sur un repo propre.
- Toute nouvelle capacité métier doit avoir une seule source de vérité.
- Les données temporaires ou générées doivent rester dans `tmp/`, `reports/` ou `data/generated/`.

*Cette règle sera adaptée lors de l'initialisation du projet spécifique.*
