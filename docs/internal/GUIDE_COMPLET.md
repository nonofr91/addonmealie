# 🎯 Guide Complet : Scraper & Importer les Recettes Marmiton dans Mealie

> ⚠️ **DEPRECATED** - Ce guide est obsolète. Les outils référencés (`simple_scraper.py`, `import_to_mealie.py`, `mealie_mcp_test`) ont été déplacés ou remplacés.
>
> **Documentation actuelle :**
> - Import hybride : `mealie-workflow/docs/README.md`
> - MCP Mealie : `mealie-mcp-server/README.md` et `mealie-mcp-server/API_COVERAGE.md`
> - Architecture : `docs/ARCHITECTURE.md`

## 📋 Vue d'ensemble

Ce système complet vous permet de :
1. **Scraper** les URLs des recettes depuis Marmiton
2. **Importer** automatiquement ces recettes dans Mealie
3. **Traiter** les ingrédients avec le parser amélioré

---

## 🚀 Étape 1 : Scraper les URLs

### Installation rapide
```bash
sudo apt update && sudo apt install python3-bs4 python3-requests
```

### Scraper les 5 premières pages (test)
```bash
cd /home/bruno/CascadeProjects/windsurf-project-7
python3 simple_scraper.py
```

**Résultat :**
- ✅ 161 URLs trouvées
- 📁 Sauvegardées dans `marmiton_urls.json`
- ⏱️ Durée : ~10 secondes

### Scraper plus de pages
Modifiez `simple_scraper.py` :
```python
# Changez cette ligne pour scraper plus de pages
recipe_urls = scrape_pages(1, 20)  # Pages 1 à 20
```

---

## 📊 Statistiques de scraping

### Pages testées (1-5)
| Page | Recettes | Cumul |
|------|----------|-------|
| 1    | 42       | 42    |
| 2    | 30       | 72    |
| 3    | 29       | 101   |
| 4    | 30       | 131   |
| 5    | 30       | 161   |

### Estimation complète
- **Pages totales** : 571
- **Recettes/page** : ~30
- **Total estimé** : ~17,000 recettes
- **Temps complet** : ~3-4 heures

---

## 📥 Étape 2 : Importer dans Mealie

### Import manuel (une recette)
```python
# Utiliser le MCP Mealie ou le module d'import canonique
# Le MCP Mealie est disponible dans mealie-mcp-server/
# Voir mealie-mcp-server/README.md pour la configuration

# Exemple avec le MCP :
# from mealie_mcp_package import create_recipe_from_url
# create_recipe_from_url(
#     url="https://www.marmiton.org/recettes/recette_blanquette-de-veau-facile_19219.aspx"
# )
```

### Import batch
Utiliser le workflow d'import dans `mealie-workflow/` :
```bash
cd mealie-workflow
python3 import_hybrid.py --limit 20
```

Options disponibles :
- `--limit N` : Limiter à N recettes
- `--source marmiton` : Source des recettes
- `--dry-run` : Simulation sans import

Documentation complète : `mealie-workflow/docs/README.md`

---

## 🔧 Étape 3 : Traitement des ingrédients

### Parser amélioré (déjà activé)
Le parser reconnaît maintenant :
- ✅ **"gousse"** comme unité pour l'ail
- ✅ **Unités françaises** (c.à soupe, c.à café, etc.)
- ✅ **Quantités complexes** (1 1/2, 2/3, etc.)
- ✅ **Food-only** (sel, poivre, etc.)

### Validation automatique
```python
# Validation via MCP Mealie
# Voir mealie-mcp-server/API_COVERAGE.md pour les outils disponibles

# Ou utiliser le module d'import hybride :
from mealie_workflow.importing.validator import validate_recipe_structure
validate_recipe_structure(slug="nom-de-recette")
```

---

## 📁 Fichiers disponibles

### Scripts principaux
- `simple_scraper.py` - Scraping rapide
- `scraper_marmiton.py` - Version complète avec menu
- `import_to_mealie.py` - Import batch dans Mealie

### Documentation
- `README_Scraper.md` - Guide détaillé du scraper
- `GUIDE_COMPLET.md` - Ce guide

### Données
- `marmiton_urls.json` - URLs scrapées

---

## 🎯 Exemples d'utilisation

### Scénario 1 : Test rapide
```bash
# 1. Scraper 5 pages
python3 simple_scraper.py

# 2. Importer 3 recettes
python3 import_to_mealie.py
# Choix : 1 (5 recettes)

# 3. Vérifier une recette
# Utiliser le MCP Mealie
# mcp3_get_recipe_detailed(slug="blanquette-de-veau-facile")

# Ou l'API REST de Mealie directement
import requests
response = requests.get(
    f"{MEALIE_BASE_URL}/api/recipes/blanquette-de-veau-facile",
    headers={"Authorization": f"Bearer {MEALIE_API_KEY}"}
)
```

### Scénario 2 : Import moyen
```bash
# 1. Scraper 20 pages
# Modifier simple_scraper.py : scrape_pages(1, 20)
python3 simple_scraper.py

# 2. Importer 50 recettes
python3 import_to_mealie.py
# Choix : 3 (50 recettes)
```

### Scénario 3 : Import complet
```bash
# 1. Scraper toutes les pages
python3 scraper_marmiton.py
# Choix : 3 (571 pages - attention, 3-4 heures!)

# 2. Importer tout
python3 import_to_mealie.py
# Choix : 4 (toutes les recettes)
```

---

## ⚠️ Points d'attention

### Performance
- **Pause obligatoire** : 2-5 secondes entre les imports
- **Timeout** : 10 secondes par requête
- **Mémoire** : OK pour 17,000 URLs (~1MB)

### Limites Marmiton
- **Protection anti-scraping** : Respectez les pauses
- **Structure variable** : Le parser s'adapte automatiquement
- **Contenu dynamique** : Parfois JavaScript requis

### Limites Mealie
- **Rate limiting** : Attendre entre les imports
- **Mémoire** : OK pour milliers de recettes
- **Validation** : Automatic avec le parser amélioré

---

## 📈 Résultats attendus

### Qualité des imports
- ✅ **Taux de réussite** : 95%+
- ✅ **Structuration** : 100% avec le parser amélioré
- ✅ **Catégorisation** : Automatique
- ✅ **Tags** : Intelligents et pertinents

### Exemple de recette importée
```json
{
  "name": "Blanquette de veau facile",
  "slug": "blanquette-de-veau-facile",
  "ingredients": [
    {"quantity": 800, "unit": "gramme", "food": "Veau"},
    {"quantity": 2, "unit": "gousse", "food": "Ail"},
    {"quantity": null, "unit": null, "food": "Sel"}
  ],
  "categories": ["Plats Principaux"],
  "tags": ["Viande", "Facile", "Import IA"]
}
```

---

## 🔄 Maintenance

### Mettre à jour le scraper
```bash
# Re-scraper pour obtenir les nouvelles recettes
python3 simple_scraper.py

# Ne duplique pas les URLs existantes
```

### Nettoyer les imports
```python
# Déduplication via le workflow
from mealie_workflow.cleaning.deduplicator import RecipeDeduplicator

dedup = RecipeDeduplicator()
duplicates = dedup.find_duplicates()
dedup.merge_duplicates(duplicates)
```

---

## 🎉 Prochaines améliorations

1. **Scraper d'autres catégories** (entrées, desserts)
2. **Filtres intelligents** (régime, difficulté)
3. **Import sélectif** (par tags)
4. **Monitoring automatique** des imports
5. **API directe** vers Marmiton si disponible

---

## 📞 Support et dépannage

### Problèmes courants
- **Timeout** : Augmenter les pauses
- **Erreur 403** : Attendre + changer User-Agent
- **Parser échoue** : Vérifier le format de la recette

### Logs et monitoring
```bash
# Vérifier les imports récents
grep "Import" import.log

# Vérifier les erreurs
grep "❌" import.log
```

---

**Bon scraping et bon appétit !** 🚀🍳
