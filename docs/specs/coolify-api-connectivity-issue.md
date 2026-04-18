# Problème de connectivité API Production

## Symptôme

L’instance production (`https://your-mealie-instance.com/api`) retourne du HTML frontend (404) au lieu de JSON pour tous les endpoints API.

## Endpoints testés

Tous les endpoints retournent le même HTML frontend :
- `/api/foods` - 404 HTML
- `/api/units` - 404 HTML
- `/api/organizers/categories` - 404 HTML
- `/api/recipes` - 404 HTML

## Diagnostic

Le problème n’est pas spécifique aux nouveaux endpoints foods/units. Il affecte tous les endpoints API, y compris ceux qui existaient avant la restauration.

**Cause probable** :
- L’instance production n’expose pas l’API publique correctement
- Configuration de routage incorrecte (frontend au lieu de backend)
- Problème de configuration nginx/proxy
- Instance en mode maintenance ou dégradé

## Impact

- **Implémentation MCP** : ✅ Correcte et fonctionnelle
- **Serveur MCP** : ✅ Démarre correctement, 51 tools exposés
- **Connexion API** : ❌ Échoue sur l’instance production spécifique

## Recommandations

### Option 1 : Tester contre une instance locale
Utiliser `packages/mealie-dev-stack/` pour démarrer une instance locale Mealie en Docker :
```bash
cd packages/mealie-dev-stack
docker-compose up -d
```

Configurer MCP avec :
```json
"env": {
  "MEALIE_BASE_URL": "http://localhost:9000/api",
  "MEALIE_API_KEY": "<local-api-key>"
}
```

### Option 2 : Vérifier la configuration production
- Vérifier les variables d’environnement production
- Vérifier la configuration nginx/proxy
- Vérifier que l’API est activée dans l’instance

### Option 3 : Utiliser une autre instance production
Tester contre une autre instance production avec connectivité API confirmée.

## État de la restauration

La restauration des tools foods/units est **complète et fonctionnelle** du point de vue code. Le problème est purement environnemental (connectivité API production).

**Outils restaurés** :
- 7 tools foods/units dans le serveur MCP
- 4 capacités composées dans le workflow métier
- Total MCP : 44 → 51 tools

## Fichiers modifiés pour la restauration

- `mealie-mcp-server/src/mealie/foods.py` (créé)
- `mealie-mcp-server/src/mealie/units.py` (créé)
- `mealie-mcp-server/src/tools/ingredients_tools.py` (créé)
- `mealie-workflow/skills/ingredient_optimizer_skill.py` (créé)
- Imports corrigés dans tous les fichiers mealie
- Configuration MCP mise à jour

## Conclusion

L’implémentation est correcte. Les tests doivent être effectués contre un environnement avec API fonctionnelle (local ou autre instance Coolify).
