# Workflow d’import de recettes

## Vue d’ensemble

Le workflow d’import de recettes est composé de trois étapes :
1. **Scraping** : Extraction des recettes depuis les sources web
2. **Structuration** : Transformation des données scrapées en format Mealie
3. **Import** : Import des recettes structurées dans Mealie

## Pipeline existant

Le pipeline canonique est déjà implémenté et fonctionne parfaitement :
- `mealie-workflow/skills/recipe_scraper_skill.py` - Scraping via MCP Jina
- `mealie-workflow/skills/data_structurer_skill.py` - Structuration Mealie
- `mealie-workflow/skills/recipe_importer_skill.py` - Import via MCP Mealie
- `mealie-workflow/workflow_orchestrator.py` - Orchestration des trois étapes

## Import depuis un fichier structuré

Le pipeline fonctionne parfaitement pour l’import de fichiers structurés JSON avec ingrédients normalisés et instructions optimisées.

### Exemple

```bash
# Import depuis un fichier structuré JSON
mealie-import-orchestrator step importing --structured-filename data/carbonara_marmiton.json
```

### Format du fichier structuré

Le fichier JSON doit avoir la structure suivante :

```json
{
  "metadata": {
    "version": "1.0",
    "total_recipes": 1,
    "format": "mealie_compatible"
  },
  "recipes": [
    {
      "name": "Nom de la recette",
      "slug": "slug-de-la-recette",
      "description": "Description de la recette",
      "prepTime": "PT15M",
      "cookTime": "PT20M",
      "totalTime": "PT35M",
      "recipeServings": 4.0,
      "recipeIngredient": [
        {
          "quantity": 400.0,
          "unit": "g",
          "food": "Pâtes (spaghetti)",
          "display": "400g de pâtes (spaghetti)",
          "originalText": "400g de pâtes (spaghetti)"
        }
      ],
      "recipeInstructions": [
        {
          "id": "1",
          "title": "Titre de l'étape",
          "text": "Instruction détaillée"
        }
      ]
    }
  ]
}
```

## Scraping depuis une URL

Le scraping via MCP Jina nécessite l’environnement Cascade. Les MCP Jina ne sont pas disponibles localement.

### Limitation actuelle

```bash
# Ceci ne fonctionne pas localement car les MCP Jina ne sont pas disponibles
mealie-import-orchestrator full --source https://www.marmiton.org/recettes/recette_carbonara-traditionnelle_340808.aspx
```

### Solution

Pour scraper depuis une URL, il faut utiliser les MCP Jina via Cascade directement. Le scraping doit être effectué depuis l’environnement Cascade, pas localement.

## Étapes individuelles

### Étape 1 : Scraping

```bash
mealie-import-orchestrator step scraping --source https://www.marmiton.org/recettes/recette_carbonara-traditionnelle_340808.aspx
```

### Étape 2 : Structuration

```bash
mealie-import-orchestrator step structuring --scraped-filename mealie-workflow/scraped_data/latest_scraped_recipes_mcp.json
```

### Étape 3 : Import

```bash
mealie-import-orchestrator step importing --structured-filename mealie-workflow/structured_data/mealie_structured_recipes_YYYYMMDD_HHMMSS.json
```

## Capacités déjà implémentées

D’après les sessions précédentes, les capacités suivantes sont déjà implémentées :

- ✅ Scraping de recettes depuis URLs (via MCP Jina)
- ✅ Structuration IA des ingrédients (AIRecipeAnalyzer)
- ✅ Import unitaire et batch
- ✅ Validation post-import
- ✅ Cleanup et correction
- ✅ Normalisation des ingrédients
- ✅ Optimisation des instructions

## Références

- Session 2026-04-12 : Architecture IA et AIRecipeAnalyzer
- `docs/specs/import-ia-phase4-evaluation.md` : Évaluation des capacités d’import
- `docs/specs/restoration-complete-summary.md` : Restauration des outils d’ingrédients
