# Abstraction de scraping

## Problème résolu

Le projet n’est plus dépendant du MCP Jina Cascade. Une abstraction de providers de scraping a été créée pour permettre différents modes de scraping.

## Architecture

### Interface abstraite

`mealie-workflow/src/scraping/base.py` - Interface `ScrapingProvider` avec méthodes :
- `extract_url(url)` - Extrait le contenu d’une URL (retourne str ou dict structuré)
- `search_images(query, num)` - Recherche des images
- `get_provider_name()` - Retourne le nom du provider
- `is_available()` - Vérifie si le provider est disponible

### Providers implémentés

1. **JinaMCPProvider** (`mealie-workflow/src/scraping/providers/jina_mcp_provider.py`)
   - Utilise les MCP Jina via Cascade
   - Meilleure qualité de scraping
   - Nécessite l’environnement Cascade

2. **RequestsProvider** (`mealie-workflow/src/scraping/providers/requests_provider.py`)
   - Utilise requests + BeautifulSoup
   - Fonctionne localement sans dépendance Cascade
   - Parsing spécifique par site (Marmiton, 750g) via JSON-LD
   - Retourne des données structurées (name, ingredients, instructions, image)

### Factory

`mealie-workflow/src/scraping/factory.py` - Factory pour créer le provider approprié

## Configuration

### Variable d’environnement

`SCRAPING_USE_JINA_MCP` - Force l’utilisation de JinaMCPProvider

- `false` (défaut) : Utilise RequestsProvider (local)
- `true` : Utilise JinaMCPProvider (via Cascade)

### Exemples

```bash
# Utiliser RequestsProvider par défaut (local)
mealie-import-orchestrator full --source https://www.marmiton.org/recettes/recette_carbonara-traditionnelle_340808.aspx

# Forcer l’utilisation de JinaMCPProvider (via Cascade)
export SCRAPING_USE_JINA_MCP=true
mealie-import-orchestrator full --source https://www.marmiton.org/recettes/recette_carbonara-traditionnelle_340808.aspx
```

## Intégration dans le scraper

`mealie-workflow/src/scraping/recipe_scraper_mcp.py` utilise la factory pour créer le provider de scraping :

```python
self.scraping_provider = create_scraping_provider()
```

Le scraper gère maintenant deux types de retour du provider :
- Si le provider retourne un dict structuré (RequestsProvider), il utilise directement les données
- Si le provider retourne une chaîne de caractères (JinaMCPProvider), il utilise l’AIRecipeAnalyzer pour parser

## Corrections apportées

1. **Parsing spécifique par site** : RequestsProvider utilise les données JSON-LD de Marmiton pour extraire les ingrédients et instructions
2. **Transmission des données** : Le structurer supporte maintenant les deux noms de champs (`recipeIngredient`/`recipeInstructions` et `ingredients`/`instructions`)
3. **Gestion des None** : Le parser d’ingrédients gère maintenant les cas où unit ou food sont None

## Avantages

1. **Indépendance** : Le projet n’est plus dépendant du MCP Jina Cascade
2. **Flexibilité** : Facile d’ajouter d’autres providers (services externes, API payantes)
3. **Fallback** : Si un provider n’est pas disponible, fallback automatique
4. **Testabilité** : Facile de tester avec différents providers
5. **Qualité** : Le parsing spécifique par site via JSON-LD assure une meilleure qualité d’extraction

## Améliorations futures

1. **Services externes** : Ajouter des providers pour des services de scraping externes (ScrapingBee, Apify, etc.)
2. **Cache** : Ajouter un cache pour éviter de scraper les mêmes URLs
3. **Rate limiting** : Ajouter un rate limiting pour éviter d’être bloqué par les sites
4. **Plus de sites** : Ajouter le parsing spécifique pour d’autres sites (750g, Cuisine Actuelle, etc.)

## Fichiers créés

- `mealie-workflow/src/scraping/base.py` - Interface abstraite
- `mealie-workflow/src/scraping/factory.py` - Factory
- `mealie-workflow/src/scraping/providers/__init__.py` - Package providers
- `mealie-workflow/src/scraping/providers/jina_mcp_provider.py` - Provider Jina MCP
- `mealie-workflow/src/scraping/providers/requests_provider.py` - Provider Requests avec parsing JSON-LD

## Test réussi

Le workflow complet fonctionne avec RequestsProvider :
- Scraping : 7 ingrédients, 9 instructions, images extraites
- Structuration : 7 ingrédients, 9 instructions conservés
- Import : 1 recette importée dans Mealie avec 7 ingrédients et 9 instructions

Le pipeline fonctionne maintenant correctement sans dépendance au MCP Jina Cascade.
