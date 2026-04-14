# Decisions

Ce dossier contient les décisions d'architecture et de gouvernance qui doivent rester traçables dans le temps.

Décisions actuellement importantes :
- `windsurf-project-operating-model.md` : modèle opératoire du repo, hiérarchie entre `AGENTS.md`, `Rules`, `Workflows`, `Skills` et procédure de réutilisation comme starter pack.
- `mcp-canonical-source.md` : désigne `mealie-mcp-server/` comme source de vérité MCP canonique et cadre le déclassement des variantes racine.
- `mealie-platform-constraints.md` : fixe les contraintes de l'image Mealie et le contrat de base que doivent respecter les addons externes.
- `addon-deployment-model.md` : fixe le modèle de déploiement des addons autour d'un Mealie hébergé dans Coolify via Docker.
- `development-environment-strategy.md` : fixe la stratégie d'environnements avec développement local Docker et validation d'intégration dans Coolify.
