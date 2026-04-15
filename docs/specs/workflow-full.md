# Workflow complet Mealie - Toutes les fonctionnalités

## Vue d'ensemble

Le workflow complet Mealie intègre toutes les fonctionnalités développées pour le pipeline d'import de recettes. Il comprend 5 étapes principales :

1. **Scraping** - Extraction des recettes depuis des sources externes
2. **Structuration** - Transformation des données scrapées au format Mealie
3. **Optimisation des ingrédients** - Validation et structuration intelligente des ingrédients
4. **Import** - Import des recettes dans Mealie
5. **Vérification qualité** - Analyse complète de la qualité des données

## Architecture

### Étape 1: Scraping

**Skill**: `RecipeScraperSkill`

**Provider**: `RequestsProvider` (par défaut) ou `JinaMCPProvider` (via variable d'environnement)

**Fonctionnalités**:
- Extraction de contenu via requests + BeautifulSoup (local)
- Parsing spécifique par site (Marmiton, 750g) via JSON-LD
- Extraction de données structurées (nom, ingrédients, instructions, images)
- Sauvegarde des données scrapées dans un fichier JSON

**Fichier de sortie**: `mealie-workflow/scraped_data/latest_scraped_recipes_mcp.json`

**Configuration**: Variable d'environnement `SCRAPING_USE_JINA_MCP`

### Étape 2: Structuration

**Skill**: `DataStructurerSkill`

**Structurer**: `MealieDataStructurer`

**Fonctionnalités**:
- Transformation des données scrapées au format Mealie
- Génération de slugs uniques
- Formatage des ingrédients avec quantités, unités et aliments
- Formatage des instructions avec UUIDs
- Ajout de métadonnées (temps, portions, catégories, tags, nutrition)
- Support des deux noms de champs (`recipeIngredient`/`recipeInstructions` et `ingredients`/`instructions`)

**Fichier de sortie**: `mealie-workflow/structured_data/latest_mealie_structured_recipes.json`

### Étape 2.5: Optimisation des ingrédients

**Skill**: `IngredientOptimizerSkill`

**Fonctionnalités**:
- Validation de la structure des ingrédients
- Structuration intelligente des ingrédients texte
- Amélioration des ingrédients déjà structurés
- Migration complète des ingrédients avec création d'éléments
- Correction des noms d'aliments existants

**Fichier de sortie**: `mealie-workflow/structured_data/optimized_structured_recipes_{timestamp}.json`

**Méthodes**:
- `validate_ingredients_structure(recipe_data)` - Valide la structure des ingrédients
- `intelligent_ingredient_structurer(recipe_data)` - Structure les ingrédients avec IA
- `optimize_ingredients_in_file(structured_filename)` - Optimise les ingrédients dans un fichier

### Étape 3: Import

**Skill**: `RecipeImporterSkill`

**Importer**: `MealieRecipeImporterMCP`

**Fonctionnalités**:
- Import des recettes structurées dans Mealie via API
- Import par lot avec délai configurable
- Vérification des imports après import
- Gestion des erreurs et retries
- Rapport d'import avec statistiques

**Fichier de sortie**: `mealie-workflow/import_reports/mealie_import_report_{timestamp}.json`

**Configuration**:
- `batch_size`: 5 (nombre de recettes par lot)
- `delay_between_imports`: 3 (secondes entre les imports)
- `verify_imports`: true (vérifier les imports)

### Étape 4: Vérification qualité

**Checker**: `WorkflowQualityChecker`

**Fonctionnalités**:
- **Niveau 1**: Qualité structurelle (format JSON, champs requis, UUIDs, types de données)
- **Niveau 2**: Qualité du contenu (doublons, cohérence, spécificité, ingrédients, instructions, images)
- **Niveau 3**: Qualité métier (nutrition, catégories, utilisabilité pour les agents)

**Fichier de sortie**: `quality_reports/mealie_quality_report_{timestamp}.json`

**Scores**:
- Score global (0-100)
- Score structurel (0-100)
- Score contenu (0-100)
- Score métier (0-100)

**Recommandations**: Génère des recommandations pour améliorer la qualité

## Workflow Orchestrator

### Classe: `MealieWorkflowOrchestrator`

**Skills intégrés**:
- `RecipeScraperSkill`
- `DataStructurerSkill`
- `IngredientOptimizerSkill`
- `RecipeImporterSkill`
- `WorkflowQualityChecker`

### Méthodes

#### `run_complete_workflow(sources: List[str] = None) -> Dict`

Lance le workflow complet de scraping à l'import avec toutes les fonctionnalités.

**Étapes**:
1. Scraping des recettes depuis les sources
2. Structuration des données scrapées
3. Optimisation des ingrédients
4. Import des recettes dans Mealie
5. Vérification qualité

**Retour**: Dict avec les résultats complets du workflow

#### `run_step_by_step(step: str, **kwargs) -> Dict`

Exécute une étape spécifique du workflow.

**Étapes disponibles**:
- `scraping` - Scraping des recettes
- `structuring` - Structuration des données
- `optimization` - Optimisation des ingrédients
- `importing` - Import dans Mealie
- `quality` - Vérification qualité

#### `get_workflow_status() -> Dict`

Retourne le statut actuel du workflow avec les étapes complétées et la progression globale.

#### `calculate_workflow_statistics() -> Dict`

Calcule les statistiques complètes du workflow (scraping, structuration, optimisation, import, qualité, taux de conversion).

#### `save_workflow_report(results: Dict = None) -> Optional[str]`

Sauvegarde un rapport complet du workflow avec statistiques et résumé.

## Commandes CLI

### Workflow complet

```bash
mealie-import-orchestrator full --source https://www.marmiton.org/recettes/recette_carbonara_traditionnelle_340808.aspx
```

### Étape par étape

```bash
# Scraping
mealie-import-orchestrator step scraping --source https://www.marmiton.org/recettes/recette_carbonara_traditionnelle_340808.aspx

# Structuration
mealie-import-orchestrator step structuring --scraped_filename scraped_data/latest_scraped_recipes_mcp.json

# Optimisation
mealie-import-orchestrator step optimization --structured_filename structured_data/latest_mealie_structured_recipes.json

# Import
mealie-import-orchestrator step importing --structured_filename structured_data/optimized_structured_recipes_{timestamp}.json

# Qualité
mealie-import-orchestrator step quality --scraped_filename scraped_data/latest_scraped_recipes_mcp.json --structured_filename structured_data/latest_mealie_structured_recipes.json --import_filename import_reports/mealie_import_report_{timestamp}.json
```

### Statut

```bash
mealie-import-orchestrator status
```

## Résultats du workflow

### Statistiques

- **Scraping**: Nombre de recettes scrapées, sources utilisées, ingrédients/instructions moyens
- **Structuration**: Recettes structurées, catégories/tags créés, calories moyennes
- **Optimisation**: Recettes optimisées, succès de l'optimisation
- **Import**: Recettes importées, catégories/tags dans Mealie, ingrédients/instructions moyens
- **Qualité**: Score global, scores par niveau, issues et recommandations

### Taux de conversion

- `scraping_to_structuring`: % de recettes scrapées qui ont été structurées
- `structuring_to_import`: % de recettes structurées qui ont été importées
- `overall_efficiency`: % de recettes scrapées qui ont été importées avec succès

### Fichiers générés

- `scraped`: Fichier JSON des données scrapées
- `structured`: Fichier JSON des données structurées (ou optimisées)
- `import_report`: Fichier JSON du rapport d'import
- `quality_report`: Fichier JSON du rapport de qualité

## Configuration

### Variables d'environnement

- `MEALIE_BASE_URL`: URL de l'instance Mealie (ex: `http://127.0.0.1:9925`)
- `MEALIE_LOCAL_API_KEY`: Token API Mealie
- `SCRAPING_USE_JINA_MCP`: Force l'utilisation de JinaMCPProvider (`true`/`false`)

### Profils Mealie

- **dev**: Instance locale de développement
- **prod**: Instance de production

Fichier: `mealie-workflow/config/mealie-profiles.json`

## Exemple de résultat

```json
{
  "success": true,
  "workflow": {
    "start_time": "2026-04-15T18:35:19.123456",
    "end_time": "2026-04-15T18:35:20.123456",
    "total_time": 1.0,
    "scraping_time": 0.2,
    "structuring_time": 0.0,
    "optimization_time": 0.0,
    "importing_time": 0.08,
    "quality_time": 0.004
  },
  "results": {
    "scraping": { "success": true, "total_recipes": 1, ... },
    "structuring": { "success": true, "total_recipes": 1, ... },
    "optimization": { "success": true, "optimized_count": 0, ... },
    "importing": { "success": true, "total_imported": 1, ... },
    "quality": { "success": true, "global_score": 88.67, ... }
  },
  "statistics": {
    "scraping": { "total_recipes": 1, ... },
    "structuring": { "total_recipes": 1, ... },
    "optimization": { "optimized_count": 0, ... },
    "importing": { "total_imported": 1, ... },
    "quality": { "global_score": 88.67, ... },
    "conversion_rates": {
      "scraping_to_structuring": 100.0,
      "structuring_to_import": 100.0,
      "overall_efficiency": 100.0
    }
  },
  "files": {
    "scraped": "scraped_data/latest_scraped_recipes_mcp.json",
    "structured": "structured_data/optimized_structured_recipes_20260415_183519.json",
    "import_report": "import_reports/mealie_import_report_20260415_183520.json"
  },
  "message": "Workflow complet terminé avec succès!"
}
```

## Améliorations futures

1. **QualityDashboard** - Intégrer pour afficher les résultats de qualité de manière visuelle
2. **AdvancedRecipeCleaner** - Intégrer pour nettoyer les recettes (doublons, corrections)
3. **Étape cleanup** - Ajouter une étape de nettoyage dans le workflow
4. **Commandes CLI** - Mettre à jour les commandes CLI pour supporter toutes les étapes
5. **Cache** - Ajouter un cache pour éviter de scraper les mêmes URLs
6. **Rate limiting** - Ajouter un rate limiting pour éviter d’être bloqué par les sites

## Fichiers modifiés

- `mealie-workflow/workflow_orchestrator.py` - Ajout des étapes optimization et quality
- `mealie-workflow/skills/ingredient_optimizer_skill.py` - Ajout de la méthode `optimize_ingredients_in_file`
- `mealie-workflow/src/structuring/mealie_structurer.py` - Support des deux noms de champs pour ingrédients/instructions

## Tests réussis

Le workflow complet a été testé avec succès avec l'URL Marmiton :
- Scraping : 1 recette scrapée avec 7 ingrédients et 9 instructions
- Structuration : 1 recette structurée
- Optimisation : 0 recettes optimisées (ingrédients déjà bien structurés)
- Import : 1 recette importée dans Mealie
- Qualité : Score global 88.67/100 (Structure: 93.33, Contenu: 80, Métier: 95.56)

Taux de conversion : 100% (scraping → structuration → import)
