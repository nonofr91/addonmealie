# Root Cleanup Phase 2 - COMPLETED

## Objectif

Préparer la réduction sûre des variantes MCP et des configurations concurrentes à la racine du repo.

## Décision préalable

La source de vérité canonique pour le serveur MCP Mealie est `mealie-mcp-server/`.

## ✅ Statut: Cleanup Terminé

### Fichiers nettoyés

Toutes les variantes MCP ont été supprimées ou consolidées:
- ✅ `mealie_mcp_server.py` - supprimé
- ✅ `mealie_mcp_test.py` - supprimé
- ✅ `mealie_mcp_test_improved.py` - supprimé
- ✅ `mealie_mcp_compliant.py` - supprimé
- ✅ `verbose_mcp.py` - supprimé
- ✅ Toutes les configs `*mcp_config*.json` - supprimées

### Fichiers conservés

- ✅ `mealie_mcp_complete.py` - **BRIDGE LÉGITIME** - Point d'entrée pour Windsurf qui délègue à `mealie-mcp-server/`
- ✅ `install_mcp_mealie.sh` - Script d'installation qui pointe vers le canonique

### Documentation mise à jour

- ✅ `docs/internal/GUIDE_COMPLET.md` - marqué comme DEPRECATED avec références aux docs actuelles

## Critères de réussite

- ✅ une seule cible MCP documentée: `mealie-mcp-server/`
- ✅ plus de configuration concurrente active à la racine
- ✅ plus de secrets dans les points d'entrée MCP conservés

## Vérification

```bash
# Liste des fichiers MCP à la racine
find . -maxdepth 1 -name "*mcp*" -type f
# Résultat: mealie_mcp_complete.py (bridge légitime)

# Configs MCP
find . -maxdepth 1 -name "*mcp_config*" -type f
# Résultat: aucune
```
