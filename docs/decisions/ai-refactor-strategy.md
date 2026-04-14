# Stratégie de Refactor pour l'Architecture IA

## Analyse de l'Utilisation Actuelle de l'IA

### Fichiers Identifiés
- `mealie-workflow/src/scraping/recipe_scraper_mcp.py` : Utilise MCP Cascade pour scraping
- `mealie-workflow/src/ai/providers/cascade_provider.py` : Provider Cascade (implémentation placeholder)

### Utilisation Actuelle dans recipe_scraper_mcp.py

**MCP utilisés directement :**
1. `mcp2_read_url()` : Scraping de contenu web (Jina)
2. `mcp2_search_images()` : Recherche d'images (Jina)
3. `IntelligentRecipeAnalyzer` : Analyse locale de recettes

**Types d'opérations :**
- **Scraping web** : Extraction de contenu depuis URLs
- **Recherche d'images** : Trouver des images pour les recettes
- **Analyse locale** : Parsing et structuration de recettes

## Architecture IA Implémentée

**Interface AIProvider :**
- `complete(prompt)` : Complétion de texte
- `analyze_ingredient(text)` : Analyse d'ingrédients
- `structure_recipe(data)` : Structuration de recettes

**Providers implémentés :**
- `CascadeProvider` : Utilise MCP Cascade (placeholder)
- `OpenAIProvider` : Utilise API OpenAI
- `AnthropicProvider` : Utilise API Anthropic
- `MockProvider` : Pour tests

## Stratégie de Refactor

### Phase 1 : Séparation des Responsabilités

**Principe :** Les MCP de scraping (Jina) restent comme ils sont, l'architecture IA est utilisée pour l'analyse/structuration.

**Justification :**
- Les MCP Jina sont spécifiques au scraping et ne sont pas de l'IA générative
- Les providers IA (OpenAI, Anthropic) sont optimisés pour l'analyse et la structuration
- Le scraping peut continuer à utiliser les MCP Cascade spécifiques

### Phase 2 : Points d'Intégration

**1. Analyse d'ingrédients :**
- Remplacer l'analyse locale par `AIProvider.analyze_ingredient()`
- Permet d'utiliser OpenAI/Anthropic pour un parsing plus précis

**2. Structuration de recettes :**
- Remplacer l'analyse locale par `AIProvider.structure_recipe()`
- Permet d'utiliser OpenAI/Anthropic pour une structuration plus intelligente

**3. Scraping web :**
- Garder les MCP Jina (`mcp2_read_url`)
- Ce sont des outils spécifiques qui ne sont pas dans l'interface AIProvider

**4. Recherche d'images :**
- Garder les MCP Jina (`mcp2_search_images`)
- Ce sont des outils spécifiques qui ne sont pas dans l'interface AIProvider

### Phase 3 : Implémentation

**Étapes :**
1. Identifier les fonctions d'analyse dans `IntelligentRecipeAnalyzer`
2. Créer une nouvelle classe `AIRecipeAnalyzer` utilisant `AIProvider`
3. Remplacer progressivement les appels à `IntelligentRecipeAnalyzer`
4. Garder les MCP de scraping comme ils sont
5. Tester avec MockProvider d'abord, puis OpenAI/Anthropic

### Phase 4 : CascadeProvider Amélioré

**Implémentation complète :**
- Utiliser les MCP Cascade pour `complete()`
- Utiliser le skill ingredient-manager pour `analyze_ingredient()`
- Utiliser le skill recipe-analyzer pour `structure_recipe()`

## Avantages de cette Approche

1. **Séparation claire** : Scraping vs IA générative
2. **Flexibilité** : Peut utiliser différents providers selon l'environnement
3. **Testabilité** : MockProvider pour les tests
4. **Production** : OpenAI/Anthropic pour la production
5. **Développement** : Cascade pour le développement local

## Risques et Mitigations

**Risque :** Le refactor peut casser le scraping existant
**Mitigation :** Tester avec MockProvider d'abord, puis Cascade

**Risque :** Les MCP Jina ne sont pas remplaçables par OpenAI/Anthropic
**Mitigation :** Garder les MCP Jina pour le scraping, utiliser l'IA pour l'analyse seulement

## Échéance Suggérée

- Phase 1 : Immédiat (documenté)
- Phase 2 : Court terme (analyse approfondie)
- Phase 3 : Moyen terme (implémentation progressive)
- Phase 4 : Long terme (CascadeProvider complet)
