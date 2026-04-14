# 🧹 PLAN DE NETTOYAGE ET EXPANSION DES RECETTES

## 📋 **ÉTAT ACTUEL**

### ✅ **Déjà Nettoyé**
- **Doublons** : Éliminés (4 → 2 recettes)
- **Temps** : Corrigés (7 valeurs)
- **Templates** : Améliorés (2 recettes)
- **Score** : 86.8/100 - Prêt pour production

### ⚠️ **Reste à Nettoyer**
- **Images** : Chemins locaux (0/100)
- **Plus de variété** : Seulement 2 recettes uniques
- **Sources** : 4 sites configurés, peu utilisés

---

## 🧹 **PLAN DE NETTOYAGE COMPLET**

### Phase 1: **Nettoyage Profond** (Jour 1)

#### 1. **Images Réelles**
```python
# Problème actuel
"image": "scraped_images/boeuf_bourguignon.jpg"  # ❌ Local

# Solution
"image": "https://example.com/images/boeuf-bourguignon.jpg"  # ✅ URL réelle
```

**Actions**:
- Implémenter `mcp2_search_images` pour chaque recette
- Télécharger les images dans un dossier structuré
- Générer des URLs valides

#### 2. **Validation Cross-Source**
```python
# Vérifier que chaque URL a le bon contenu
if "tarte-tatin" in url:
    assert "pommes" in ingredients
    assert "caramel" in instructions
```

#### 3. **Standardisation des Données**
- **Unités** : "g" vs "grammes" → standardiser
- **Temps** : Format cohérent partout
- **Instructions** : Numérotation, clarté

### Phase 2: **Expansion des Sources** (Jours 2-3)

#### 🌐 **Ajout de Nouvelles Sources**
```json
{
  "sources": {
    "marmiton": {"priority": 1, "recipes": 50},
    "750g": {"priority": 2, "recipes": 30},
    "cuisineactuelle": {"priority": 3, "recipes": 25},
    "meilleurduchef": {"priority": 4, "recipes": 20},
    "chefnini": {"priority": 5, "recipes": 15},
    "recettes.qc.ca": {"priority": 6, "recipes": 10},
    "allrecipes.com": {"priority": 7, "recipes": 8}
  }
}
```

#### 📊 **Cibles par Type de Plat**
```json
{
  "target_recipes": [
    {"name": "boeuf-bourguignon", "category": "plat_principal"},
    {"name": "tarte-tatin", "category": "dessert"},
    {"name": "quiche-lorraine", "category": "plat_principal"},
    {"name": "ratatouille", "category": "accompagnement"},
    {"name": "lasagnes", "category": "plat_principal"},
    {"name": "mousse-chocolat", "category": "dessert"},
    {"name": "poulet-curry", "category": "plat_principal"},
    {"name": "salade-caesar", "category": "entrée"}
  ]
}
```

### Phase 3: **Import en Masse** (Jour 4)

#### 🚀 **Stratégie d'Import**
```python
# Import par lots pour éviter la surcharge
batch_size = 10
delay_between_batches = 5  # secondes

for batch in recipe_batches:
    import_batch(batch)
    time.sleep(delay_between_batches)
    verify_import(batch)
```

#### 📈 **Objectifs Quantitatifs**
- **Semaine 1** : 50 recettes nettoyées
- **Semaine 2** : 100 recettes additionnelles
- **Semaine 3** : 200 recettes total
- **Mois 1** : 500+ recettes de qualité

---

## 🔧 **OUTILS DE NETTOYAGE ET EXPANSION**

### 1. **Recipe Cleaner Avancé**
```python
class AdvancedRecipeCleaner:
    def clean_images(self, recipes):
        """Remplace les images locales par URLs réelles"""
        
    def standardize_units(self, recipes):
        """Standardise les unités (g, kg, ml, cl)"""
        
    def validate_content(self, recipes):
        """Vérifie la cohérence nom/contenu"""
        
    def enrich_metadata(self, recipes):
        """Ajoute catégories, tags, nutrition"""
```

### 2. **Multi-Source Scraper**
```python
class MultiSourceScraper:
    def scrape_all_sources(self):
        """Scrape toutes les sources configurées"""
        
    def merge_duplicates(self, recipes):
        """Fusionne les recettes similaires"""
        
    def rank_by_quality(self, recipes):
        """Classe les recettes par qualité"""
```

### 3. **Batch Import Manager**
```python
class BatchImportManager:
    def create_import_batches(self, recipes, batch_size=10):
        """Crée des lots d'import optimisés"""
        
    def import_with_retry(self, batch, max_retries=3):
        """Import avec gestion d'erreurs"""
        
    def verify_batch_integrity(self, batch):
        """Vérifie l'intégrité post-import"""
```

---

## 📊 **MÉTRIQUES DE SUCCÈS**

### 🎯 **KPIs de Nettoyage**
- **Qualité moyenne** : >90/100
- **Images réelles** : 100%
- **Doublons** : 0%
- **Temps cohérents** : 100%

### 📈 **KPIs d'Expansion**
- **Recettes/jour** : 20-50
- **Sources actives** : 5-7 sites
- **Taux de succès** : >95%
- **Import/heure** : 10-15 recettes

### 🔄 **Monitoring Continu**
```python
# Dashboard temps réel
{
  "daily_imports": 25,
  "success_rate": 96.5,
  "quality_score": 91.2,
  "active_sources": 6,
  "total_recipes": 342
}
```

---

## 🚀 **PLAN D'EXÉCUTION**

### Semaine 1: **Nettoyage Intensif**
- [ ] Implémenter `mcp2_search_images`
- [ ] Standardiser toutes les unités
- [ ] Valider tous les contenus
- [ ] Atteindre 90+ de qualité

### Semaine 2: **Expansion Sources**
- [ ] Ajouter 3 nouvelles sources
- [ ] Scraper 50 nouvelles recettes
- [ ] Nettoyer et valider
- [ ] Importer par lots

### Semaine 3: **Optimisation**
- [ ] Optimiser les temps d'import
- [ ] Monitorer les performances
- [ ] Ajuster les paramètres
- [ ] Documenter les procédures

### Semaine 4: **Production**
- [ ] Basculer en mode production
- [ ] Monitoring 24/7
- [ ] Rapports hebdomadaires
- [ ] Plan d'expansion continue

---

## 🎯 **RÉSULTATS ATTENDUS**

### 📊 **Après 1 Mois**
- **500+ recettes** de qualité
- **0% doublons**
- **100% images réelles**
- **Score qualité** >90/100

### 🚀 **Après 3 Mois**
- **2000+ recettes**
- **10+ sources**
- **Import automatisé**
- **Agents MCP** opérationnels

---

## 🔄 **FEEDBACK LOOP**

### 📈 **Amélioration Continue**
1. **Monitorer** les KPIs quotidiens
2. **Identifier** les problèmes émergents
3. **Ajuster** les paramètres
4. **Documenter** les leçons apprises

### 🎯 **Prochaines Étapes**
- **Machine Learning** pour détecter les recettes similaires
- **API externe** pour enrichir les données nutritionnelles
- **Interface utilisateur** pour validation manuelle
- **Export multi-format** (PDF, JSON, XML)

---

Ce plan assure un nettoyage complet et une expansion maîtrisée pour construire une base de recettes de qualité ! 🎉
