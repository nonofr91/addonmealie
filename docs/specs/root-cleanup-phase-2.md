# Root Cleanup Phase 2

## Objectif

Préparer la réduction sûre des variantes MCP et des configurations concurrentes à la racine du repo.

## Décision préalable

La source de vérité canonique pour le serveur MCP Mealie est `mealie-mcp-server/`.

## Cibles prioritaires

### Variantes serveur MCP à la racine

- `mealie_mcp_server.py`
- `mealie_mcp_complete.py`
- `mealie_mcp_test.py`
- `mealie_mcp_test_improved.py`
- `mealie_mcp_compliant.py`
- `verbose_mcp.py`
- autres variantes `mealie_mcp_*` concurrentes

### Configurations MCP concurrentes

- `debug_mcp_config.json`
- `final_mcp_config.json`
- `fixed_mcp_config.json`
- `full_mcp_config.json`
- `mcp_config_complete.json`
- `mcp_config_fixed.json`
- `mcp_config_mealie_test.json`
- `mcp_config_verbose.json`
- `mcp_config_with_env.json`
- `mealie_mcp_config.json`
- `mealie_mcp_config_fixed.json`
- `simple_mcp_config.json`

## Stratégie

1. identifier les fichiers encore référencés par des scripts ou de la documentation
2. réécrire les points d'entrée pour pointer vers `mealie-mcp-server/` quand c'est pertinent
3. sortir les variantes obsolètes de la trajectoire active du repo
4. supprimer ou archiver seulement après validation qu'elles ne sont plus des points d'entrée utiles

## Critères de réussite

- une seule cible MCP documentée
- plus de configuration concurrente active à la racine
- plus de secrets dans les points d'entrée MCP conservés
