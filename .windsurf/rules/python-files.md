---
trigger: glob
globs: "**/*.py"
---

# Python Files

- Ce dépôt doit évoluer vers des modules canoniques plutôt que vers une accumulation de scripts concurrents.
- Avant de créer un nouveau fichier Python, vérifier si la capacité existe déjà dans un module ou un dossier canonique.
- Si un script Python devient une source de vérité métier, le promouvoir vers `addons/`, `packages/` ou un module canonique documenté.
- Éviter les noms de fichiers contenant `final`, `debug`, `copy`, `backup`, `new`, `fixed`, `v2`, `v3`.
- Garder les secrets, tokens et URLs sensibles hors du code versionné.
- Pour toute opération sur Mealie, préférer les MCP disponibles et les interfaces publiques avant d'ajouter une logique ad hoc.
- Si un changement est multi-fichiers, architectural ou à effets de bord importants, produire d'abord une spec courte dans `docs/specs/`.
