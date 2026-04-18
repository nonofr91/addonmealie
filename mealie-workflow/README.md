# Mealie Workflow

Scripts et outils pour l'import de recettes, l'audit de qualité et la gestion des recettes Mealie via MCP.

## 🎯 Objectif

Fournir un ensemble de scripts Python pour automatiser les tâches courantes autour de Mealie : import batch, nettoyage de données, validation de qualité et gestion des recettes.

## 📁 Structure

```
mealie-workflow/
├── config/                    # Configuration
│   ├── mealie_config.json     # Configuration Mealie
│   ├── sources_config.json    # Sources de scraping
│   └── mealie-profiles.json   # Profils Mealie
├── src/                       # Source code
│   ├── importing/             # Logique d'import
│   ├── quality/               # Audit de qualité
│   └── scraping/              # Scraping web
├── scripts/                   # Scripts CLI
├── tests/                     # Tests
└── docs/                      # Documentation interne
```

## 🔧 Scripts principaux

### Import de recettes

- `multi_source_scraper.py` : Scraping multi-sources de recettes
- `mcp3_import_batch.py` : Import batch via MCP Mealie
- `test_complete_import.py` : Test complet du workflow d'import

### Qualité et validation

- `quality_checker.py` : Audit de qualité des recettes
- `quality_improver.py` : Amélioration automatique des recettes
- `quality_dashboard.py` : Dashboard de qualité
- `mcp3_validate_recipe.py` : Validation via MCP
- `mcp3_fix_invalid_recipes.py` : Correction des recettes invalides

### Gestion des recettes

- `mealie_recipe_manager.py` : Gestion CRUD des recettes
- `mealie_recipe_deleter.py` : Suppression de recettes
- `mcp3_delete_recipe.py` : Suppression via MCP
- `mcp3_update_recipe.py` : Mise à jour via MCP

### Nettoyage

- `advanced_recipe_cleaner.py` : Nettoyage avancé des recettes
- `mcp3_cleanup_duplicates.py` : Suppression des doublons

### Recherche et analyse

- `mcp3_search_recipes.py` : Recherche de recettes
- `analyze_missing_tools.py` : Analyse des outils manquants
- `critical_import_diagnostic.py` : Diagnostic d'import critique

## 🚀 Utilisation

### Configuration

1. Copier la configuration :
```bash
cp config/mealie_config.json.example config/mealie_config.json
```

2. Configurer l'URL et la clé API Mealie :
```json
{
  "mealie_url": "https://your-mealie-instance.com",
  "api_key": "your-api-key"
}
```

### Import de recettes

```bash
python scripts/mcp3_import_batch.py
```

### Audit de qualité

```bash
python scripts/quality_checker.py
```

### Nettoyage des doublons

```bash
python scripts/mcp3_cleanup_duplicates.py
```

## 📦 Dépendances

- Python 3.12+
- mealie-mcp-server
- Requests
- BeautifulSoup4

Installer les dépendances :
```bash
pip install -r requirements.txt
```

## 🔗 Intégration MCP

Les scripts utilisent le serveur MCP Mealie pour communiquer avec Mealie. Assurez-vous que le serveur MCP est configuré et accessible.

Voir [mealie-mcp-server/](../mealie-mcp-server/) pour plus d'informations sur le MCP.

## 📝 Notes

- Ces scripts sont destinés à un usage avancé
- Pour l'import simple, utilisez [mealie-import-orchestrator](../addons/mealie-import-orchestrator/)
- Les scripts peuvent être adaptés selon vos besoins spécifiques

## 🤝 Contribuer

Les contributions pour améliorer ces scripts sont les bienvenues. Voir [CONTRIBUTING.md](../CONTRIBUTING.md) pour les guidelines.
