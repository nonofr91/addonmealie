# MCP Canonical Source

## Contexte

Le repo contient plusieurs implémentations concurrentes du serveur MCP Mealie à la racine, ainsi qu'un sous-projet `mealie-mcp-server/` mieux structuré.

## Décision

La source de vérité canonique pour le serveur MCP Mealie doit être `mealie-mcp-server/`.

## Rationale

### Alignement avec la gouvernance

- l'implémentation est isolée dans un sous-projet dédié plutôt qu'à la racine
- elle réduit la prolifération de variantes concurrentes
- elle est compatible avec l'objectif d'un repo publiable et maintenable

### Sécurité

- `mealie-mcp-server/src/server.py` charge la configuration depuis les variables d'environnement
- `mealie-mcp-server/.env.template` existe déjà
- les variantes racine observées contiennent encore des secrets hardcodés

### Maintenabilité

- `mealie-mcp-server/pyproject.toml` formalise les dépendances
- le serveur est documenté dans `mealie-mcp-server/README.md`
- l'enregistrement des outils est modulaire dans `src/tools/`
- la couche client Mealie est séparée et testable

## Conséquences

- les variantes racine `mealie_mcp_*`, `verbose_mcp.py` et les configs MCP concurrentes deviennent des candidats au déclassement, à l'archivage ou à la suppression
- les prochains lots de nettoyage doivent converger vers cette cible canonique
- toute nouvelle documentation de configuration MCP doit pointer vers `mealie-mcp-server/`
