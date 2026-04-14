---
trigger: model_decision
description: Contraintes métier à appliquer quand une tâche touche Mealie, MCP, import de recettes, nutrition, images ou pipelines externes.
---

# Mealie Domain

- Ne jamais modifier l'image Mealie.
- Construire des addons, workers, pipelines et intégrations externes autour de Mealie.
- Préférer les MCP disponibles avant d'écrire une intégration personnalisée.
- Les intégrations doivent passer par des interfaces publiques et rester publiables sur un repo propre.
- Toute nouvelle capacité métier doit avoir une seule source de vérité.
- Les données temporaires ou générées doivent rester dans `tmp/`, `reports/` ou `data/generated/`.
