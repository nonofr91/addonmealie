# Specs

Ce dossier contient les spécifications courtes des addons, pipelines, refactors et règles de gouvernance importantes.

Specs actuellement importantes :
- `starter-pack-bootstrap.md` : procédure de réutilisation de ce repo comme template Windsurf pour un nouveau projet.
- `root-cleanup-phase-1.md` : premier lot de nettoyage sécurisé pour résorber la dette historique à la racine du repo.
- `root-cleanup-phase-2.md` : consolidation de la source de vérité MCP et réduction progressive des variantes concurrentes à la racine.
- `mealie-external-addon.md` : cadrage du futur addon externe Mealie qui orchestre le MCP canonique et le pipeline existant.
- `mealie-addon-contract.md` : contrat minimal que doit respecter tout addon externe développé autour de Mealie.
- `mealie-import-orchestrator.md` : spec du premier addon concret pour piloter le workflow d'import de recettes vers Mealie.
- `local-mealie-dev-stack.md` : définit la stack locale Docker canonique pour développer et tester les addons contre Mealie.
- `local-addon-dev-flow.md` : décrit le parcours développeur local pour tester un addon contre Mealie avant validation dans Coolify.
- `mealie-nutrition-advisor.md` : périmètre, architecture et contrats de l'addon de calcul nutritionnel et planification de menus.
