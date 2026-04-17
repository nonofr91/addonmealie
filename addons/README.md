# Addons

Ce dossier contient les modules externes à Mealie qui constituent les capacités publiables du projet.

Règles :

- un addon = une responsabilité claire
- pas de duplication de logique métier entre addons
- toute intégration reste externe à Mealie

## Addons disponibles

| Addon | Responsabilité |
|---|---|
| `mealie-import-orchestrator/` | Pipeline d'import de recettes (scraping → structuration → Mealie) |
| `mealie-nutrition-advisor/` | Calcul nutritionnel des recettes + profils du foyer + planificateur de menus |
