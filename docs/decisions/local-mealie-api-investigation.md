# Investigation de l'API Mealie Locale

## Statut actuel

Cette note conserve des résultats d'investigation intermédiaires. L'état confirmé le plus récent est le suivant :

- le workflow canonique `mealie-import-orchestrator -> mealie-workflow -> mcp_auth_wrapper.py` a été restauré et fonctionne de nouveau
- le payload envoyé par le workflow est correct avant l'appel API
- sur l'instance locale testée via le chemin canonique, la recette relue après import contient toujours des valeurs par défaut ou de démonstration
- la source de vérité sur la conclusion actuelle est `docs/decisions/local-mealie-314-data-loss-issue.md`

## Contexte
Investigation du problème d'import de recettes via MCP Mealie local. L'objectif était de comprendre pourquoi l'import de recette via le MCP Mealie local ne fonctionnait pas : la recette créée contenait des données par défaut au lieu du payload complet.

## Découvertes

### Instance Mealie Locale Port 9925 (mealie-local-dev)
- **Version** : v3.14.0
- **Problème** : POST /api/recipes avec payload complet ignore les données et renvoie les données par défaut ("1 Cup Flour")
- **Schéma CreateRecipe** : n'accepte que le nom de la recette, pas les ingrédients/instructions
- **Bug PUT** : PUT pour mettre à jour les recettes ne fonctionne pas
- **Bug #7210** : Corrigé dans v3.14.0 (GET/PATCH/DELETE fonctionnent maintenant)

### Instance Mealie Locale Port 39077
- **Version** : v3.14.0
- **API différente** : Structure d'API différente de l'instance port 9925
- **Endpoint fonctionnel** : `/api/recipes/create/html-or-json` fonctionne correctement avec JSON schema.org

## Solution

### Configuration MCP Mealie
- **URL de base** : http://127.0.0.1:39077
- **API Key** : Token JWT local
- **Fichier de config** : mealie-mcp-server/.env

### Endpoint de création de recettes
**POST /api/recipes/create/html-or-json**
- **Schéma** : ScrapeRecipeData
- **Champs** :
  - `data` (required, string) : JSON schema.org de la recette
  - `url` (optional, string) : URL de la recette
  - `includeTags` (optional, boolean, default false)
  - `includeCategories` (optional, boolean, default false)

### Format JSON Schema.org
```json
{
  "@context": "https://schema.org",
  "@type": "Recipe",
  "name": "Nom de la recette",
  "recipeIngredient": ["Ingrédient 1", "Ingrédient 2"],
  "recipeInstructions": ["Étape 1", "Étape 2"]
}
```

## Test Réussi
Le MCP Mealie fonctionne correctement avec l'instance locale (port 39077) :
- Recette créée avec succès
- Ingrédients corrects : "2 Tomates", "1 oignon"
- Instructions correctes : "Préparer", "Cuire"

## Recommandations

1. **Utiliser l'instance locale port 39077** pour le développement local
2. **Configurer le MCP Mealie** pour utiliser cette instance par défaut
3. **Adapter le code d'import** pour utiliser l'endpoint `/api/recipes/create/html-or-json` avec JSON schema.org
4. **Conserver le fichier openapi.json** comme référence de l'API locale

## Transport MCP pour Déploiement en Production

### Problème
Le MCP Mealie actuel utilise le transport `stdio` qui nécessite stdin disponible, ce qui ne fonctionne pas en production (Coolify/Docker).

### Solution pour Coolify
Le MCP doit utiliser un transport compatible avec le déploiement en production :
- **SSE (Server-Sent Events)** : le MCP écoute sur un port HTTP
- **WebSocket** : communication bidirectionnelle sur un port

### Implémentation requise
1. Modifier `mealie-mcp-server/src/server.py` : utiliser `transport="sse"` au lieu de `transport="stdio"`
2. Exposer un port HTTP (ex: 8000)
3. Configuration Coolify : le service Docker expose ce port

## Fichiers de Référence
- `local_openapi.json` : Spécification OpenAPI de l'instance locale port 39077
- `mealie-mcp-server/.env` : Configuration du MCP Mealie
- `mealie-mcp-server/src/server.py` : Configuration du transport MCP
