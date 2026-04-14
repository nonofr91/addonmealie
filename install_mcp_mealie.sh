#!/bin/bash

# Script d'installation du serveur MCP Mealie pour Cascade

echo "🚀 INSTALLATION DU SERVEUR MCP MEALIE"
echo "===================================="

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi

echo "✅ Python3 trouvé"

if [ ! -d "mealie-mcp-server" ]; then
    echo "❌ Sous-projet canonique introuvable: mealie-mcp-server/"
    exit 1
fi

echo "✅ Sous-projet canonique détecté: mealie-mcp-server/"
echo ""
echo "📋 Ce repo utilise désormais mealie-mcp-server/ comme source de vérité MCP."
echo ""
echo "Prochaines étapes recommandées:"
echo "1. Copier ou adapter mealie-mcp-server/.env.template"
echo "2. Suivre la configuration documentée dans mealie-mcp-server/README.md"
echo "3. Pointer votre configuration MCP vers le serveur canonique du sous-projet"
echo ""
echo "Documentation canonique: mealie-mcp-server/README.md"
echo "Exemple d'environnement: mealie-mcp-server/.env.template"
