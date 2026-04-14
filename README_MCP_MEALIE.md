# 🤖 Serveur MCP Mealie - Import IA

## 🎯 Objectif

Serveur MCP (Model Context Protocol) pour interagir directement avec Mealie depuis Cascade, permettant une gestion complète des recettes via des outils MCP.

## 🚀 Fonctionnalités

### Outils MCP disponibles

#### 📚 Gestion des Recettes
- **`scrape_recipe`** - Importe une recette depuis une URL
- **`create_recipe`** - Crée une recette manuellement  
- **`search_recipes`** - Recherche des recettes

#### 🗂️ Import IA (Spécial)
- **`import_ia_bulk`** - Importe en masse des recettes françaises
- **`get_import_ia_status`** - Affiche le statut du cookbook Import IA
- **`organize_import_ia`** - Organise les recettes dans le cookbook Import IA

#### 📋 Planification & Courses
- **`create_mealplan`** - Crée des plans de repas
- **`list_shopping_lists`** - Liste les listes de courses
- **`add_recipe_to_shopping_list`** - Ajoute des ingrédients aux courses

#### 📊 Nutrition
- **`get_recipe_nutrition`** - Informations nutritionnelles

## ⚙️ Configuration

### Installation des dépendances

```bash
cd mealie-mcp-server
uv sync
```

### Configuration Cascade

Utilisez le serveur canonique du sous-projet `mealie-mcp-server/`.

Copiez d'abord `mealie-mcp-server/.env.template`, puis configurez vos variables d'environnement Mealie.

Exemple de configuration MCP :

```json
{
  "mcpServers": {
    "mealie-mcp-server": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/bruno/CascadeProjects/windsurf-project-7/mealie-mcp-server",
        "run",
        "src/server.py"
      ],
      "env": {
        "MEALIE_BASE_URL": "https://your-mealie-instance.com",
        "MEALIE_API_KEY": "your-mealie-api-key"
      }
    }
  }
}
```

La documentation détaillée de référence est `mealie-mcp-server/README.md`.

## 🇫🇷 Utilisation Import IA

### 1. Vérifier le statut

```
Utilise l'outil get_import_ia_status pour voir l'état actuel
```

### 2. Importer en masse

```
Utilise l'outil import_ia_bulk avec une liste d'URLs françaises
Urls: [
  "https://www.ricardocuisine.com/recettes/4970-lentilles-corail-lait-coco",
  "https://www.ricardocuisine.com/recettes/5984-pates-carbonara-classique"
]
auto_organize: true
```

### 3. Organiser les recettes

```
Utilise l'outil organize_import_ia pour organiser les recettes existantes
force_reorganize: false
```

## 🔧 Secrets et configuration

- Ne pas versionner de token API dans les scripts ou les fichiers JSON de configuration.
- Utiliser les variables d'environnement du serveur canonique (`MEALIE_BASE_URL`, `MEALIE_API_KEY`).
- Les variantes racine `mealie_mcp_*` ont été déplacées vers `tmp/to-delete/` (artefacts legacy déclassés).

## 📊 Exemples d'utilisation

### Importer une recette

```
scrape_recipe avec:
- url: "https://www.ricardocuisine.com/recettes/4970-lentilles-corail-lait-coco"
- include_tags: true
- include_categories: true
```

### Importer en masse

```
import_ia_bulk avec:
- urls: ["url1", "url2", "url3"]
- auto_organize: true
```

### Vérifier le statut

```
get_import_ia_status sans paramètres
```

## 🐛 Gestion des bugs

### Bug de scraping identifié

Le scraper Mealie a un problème : il retourne des recettes incorrectes mais stocke les bonnes URLs. 

**Solution** : Le système fonctionne malgré tout, il suffit d'organiser les recettes importées dans le cookbook Import IA.

### Logs et debug

Le serveur inclut des logs détaillés pour identifier les problèmes.

## 🎉 Avantages du serveur canonique

1. **Intégration native** dans Cascade
2. **Outils structurés** avec validation
3. **Gestion d'erreurs** robuste
4. **Interface unifiée** pour toutes les opérations
5. **Extensibilité** facile

## 🔄 Prochaines améliorations

- [ ] Détection automatique des recettes françaises
- [ ] Conversion d'unités intégrée
- [ ] Export vers d'autres formats
- [ ] Intégration avec les webhooks Mealie

---

**🚀 Le serveur MCP Mealie est prêt à être utilisé dans Cascade !**
