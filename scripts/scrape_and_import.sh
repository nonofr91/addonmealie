#!/bin/bash
# Script pour scraper une URL avec les MCP Jina via Cascade et importer dans Mealie

URL=$1

if [ -z "$URL" ]; then
    echo "Usage: $0 <URL>"
    exit 1
fi

echo "🔍 Scraping de l'URL: $URL"

# Utiliser l'outil Cascade mcp2_read_url pour scraper l'URL
# Note: Ceci doit être exécuté depuis l'environnement Cascade
# Le résultat sera sauvegardé dans scraped_data/latest_scraped_recipes_mcp.json

# Pour l'instant, on utilise l'addon avec le fichier structuré existant
echo "⚠️ Les MCP Jina ne sont pas disponibles localement"
echo "💡 Utilisez le fichier structuré JSON existant pour l'import"
echo "📁 Exemple: mealie-import-orchestrator step importing --structured-filename data/carbonara_marmiton.json"
