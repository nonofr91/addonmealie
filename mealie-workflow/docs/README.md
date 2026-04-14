# Workflow Mealie - Documentation

## Vue d'Ensemble

Le Workflow Mealie est un système complet pour scraper, structurer et importer des recettes dans Mealie en utilisant les outils MCP.

## Architecture

### Structure des Dossiers

```
mealie-workflow/
├── src/
│   ├── scraping/
│   │   └── recipe_scraper_mcp.py      # Scraper avec MCP
│   ├── structuring/
│   │   └── mealie_structurer.py       # Structuration Mealie
│   └── importing/
│       └── mealie_importer_mcp.py      # Import Mealie MCP
├── skills/
│   ├── recipe_scraper_skill.py        # Skill MCP scraping
│   ├── data_structurer_skill.py       # Skill MCP structuration
│   └── recipe_importer_skill.py       # Skill MCP import
├── config/
│   ├── mealie_config.json              # Configuration Mealie
│   └── sources_config.json            # Sources de scraping
├── docs/
│   └── README.md                      # Cette documentation
├── tests/
│   └── test_workflow.py                # Tests complets
└── workflow_orchestrator.py           # Orchestrateur principal
```

## Étapes du Workflow

### 1. Scraping (recipe_scraper_mcp.py)

**Objectif**: Extraire les recettes depuis les sources web

**Outils MCP**:
- `mcp2_read_url`: Pour extraire le contenu des pages
- `mcp2_search_images`: Pour trouver les images des recettes

**Sources configurées**:
- Marmiton
- 750g
- Cuisine Actuelle
- Meilleur du Chef

**Fonctionnalités**:
- Extraction automatique des ingrédients, instructions, temps, portions
- Téléchargement des images
- Gestion des erreurs et retries
- Sauvegarde en JSON

### 2. Structuration (mealie_structurer.py)

**Objectif**: Transformer les données scrapées en format compatible Mealie

**Format de sortie**:
- UUID pour instructions et ingrédients
- Format temps ISO (PT15M)
- Informations nutritionnelles
- Catégories et tags automatiques
- Métadonnées complètes

**Fonctionnalités**:
- Parsing intelligent des ingrédients (quantité/unité/aliment)
- Génération de slugs URL-friendly
- Estimation nutritionnelle
- Validation du format Mealie

### 3. Import (mealie_importer_mcp.py)

**Objectif**: Importer les recettes structurées dans Mealie

**Outils MCP**:
- `mealie-test`: Pour créer et vérifier les recettes

**Fonctionnalités**:
- Import par lots avec gestion d'erreurs
- Vérification post-import
- Gestion des catégories
- Rapports détaillés

## Skills MCP

### @recipe-scraper

```python
# Scraper toutes les sources
result = scrape_recipes(['marmiton', '750g'])

# Scraper une recette spécifique
result = scrape_recipe('https://www.marmiton.org/recette_tarte-tatin')

# Lister les sources
sources = list_sources()
```

### @data-structurer

```python
# Structurer les données scrapées
result = structure_data('scraped_data/latest_scraped_recipes_mcp.json')

# Structurer une recette individuelle
result = structure_recipe(scraped_recipe)

# Valider le format Mealie
validation = validate_mealie_data()
```

### @recipe-importer

```python
# Importer toutes les recettes
result = import_recipes('structured_data/latest_mealie_structured_recipes.json')

# Importer une recette individuelle
result = import_recipe(structured_recipe)

# Lister les recettes importées
imported = list_imported()
```

## Workflow Orchestrateur

### Lancement Complet

```python
from workflow_orchestrator import run_full_workflow

# Lancer tout le workflow
result = run_full_workflow(['marmiton', '750g'])
```

### Étape par Étape

```python
from workflow_orchestrator import run_workflow_step

# Scraper seulement
scrape_result = run_workflow_step('scraping', sources=['marmiton'])

# Structurer seulement
structure_result = run_workflow_step('structuring', scraped_filename='...')

# Importer seulement
import_result = run_workflow_step('importing', structured_filename='...')
```

### Statut et Monitoring

```python
from workflow_orchestrator import get_workflow_status, save_workflow_report

# Vérifier le statut
status = get_workflow_status()

# Sauvegarder un rapport
report_file = save_workflow_report()
```

## Configuration

### mealie_config.json

```json
{
  "mealie_api": {
    "url": "https://mealie-...",
    "token": "votre_token"
  },
  "scraping": {
    "delay_between_requests": 2,
    "timeout": 30,
    "max_retries": 3
  },
  "structuring": {
    "language": "fr",
    "cuisine": "Française",
    "max_instructions": 15
  },
  "importing": {
    "batch_size": 5,
    "delay_between_imports": 3,
    "verify_imports": true
  }
}
```

### sources_config.json

```json
{
  "sources": {
    "marmiton": {
      "base_url": "https://www.marmiton.org",
      "priority": 1,
      "language": "fr"
    }
  },
  "target_recipes": [
    {
      "name": "boeuf-bourguignon",
      "category": "plat_principal",
      "sources": ["meilleurduchef", "marmiton"]
    }
  ]
}
```

## Tests

### Lancer les Tests Complets

```bash
cd mealie-workflow
python test_workflow.py
```

### Tests Individuels

```bash
# Test du scraper
python src/scraping/recipe_scraper_mcp.py

# Test du structurer
python src/structuring/mealie_structurer.py

# Test de l'importeur
python src/importing/mealie_importer_mcp.py

# Test de l'orchestrateur
python workflow_orchestrator.py
```

## Fichiers Générés

### Données Scrapées
- `scraped_data/scraped_recipes_mcp_YYYYMMDD_HHMMSS.json`
- `scraped_data/latest_scraped_recipes_mcp.json`

### Données Structurées
- `structured_data/mealie_structured_recipes_YYYYMMDD_HHMMSS.json`
- `structured_data/latest_mealie_structured_recipes.json`

### Rapports d'Import
- `import_reports/mealie_import_report_YYYYMMDD_HHMMSS.json`
- `import_reports/latest_mealie_import_report.json`

### Rapports Workflow
- `workflow_reports/mealie_workflow_report_YYYYMMDD_HHMMSS.json`
- `workflow_reports/latest_mealie_workflow_report.json`

## Intégration avec les Agents MCP

Une fois les recettes importées, elles sont disponibles pour:

- **@nutrition-planner**: Création de menus équilibrés
- **@recipe-analyzer**: Analyse nutritionnelle détaillée
- **@shopping-optimizer**: Listes de courses intelligentes

## Dépannage

### Problèmes Communs

1. **Scraping échoué**
   - Vérifier la connexion internet
   - Vérifier les URLs dans sources_config.json
   - Augmenter le timeout dans mealie_config.json

2. **Structuration échouée**
   - Vérifier le format du fichier scraped
   - Valider les données avec `validate_mealie_data()`

3. **Import échoué**
   - Vérifier le token Mealie
   - Vérifier la connectivité API
   - Consulter les logs d'erreur

### Logs et Monitoring

Chaque étape génère des logs détaillés:
- Progression en temps réel
- Statistiques intermédiaires
- Messages d'erreur explicites
- Temps d'exécution

## Prochaines Étapes

1. **Branchement Git**: Créer une branche dédiée
2. **Tests Réels**: Tester avec Mealie en production
3. **Optimisation**: Améliorer les performances
4. **Documentation**: Guides utilisateur avancés
5. **Monitoring**: Dashboard de suivi

## Support

Pour toute question ou problème:
1. Consulter les logs d'exécution
2. Vérifier la configuration
3. Lancer les tests de diagnostic
4. Consulter cette documentation
