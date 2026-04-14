# 📚 Guide : Cookbook "Import IA" pour Mealie

## 🎯 Objectif

Organiser automatiquement toutes les recettes importées par l'IA dans un cookbook dédié "Import IA" pour une meilleure gestion.

## 📋 Prérequis

1. **Token API Mealie valide** (le token actuel est expiré)
2. Python 3.7+ avec les bibliothèques : `requests`, `json`, `time`

## 🔧 Installation des dépendances

```bash
pip install requests
```

## 🚀 Utilisation

### 1. Mettre à jour le token

Éditez le fichier `cookbook_import_ia.py` et remplacez la variable `API_TOKEN` :

```python
API_TOKEN = "VOTRE_NOUVEAU_TOKEN_ICI"
```

### 2. Exécuter le système

```bash
python cookbook_import_ia.py
```

## 🏗️ Fonctionnalités

### ✅ Création automatique du cookbook

Le système crée automatiquement un cookbook nommé **"Import IA"** s'il n'existe pas.

### 📥 Import et organisation

- Détecte les recettes importées par l'IA
- Les ajoute automatiquement au cookbook "Import IA"
- Supporte les imports batch d'URLs

### 🗂️ Organisation des recettes existantes

Le système identifie les recettes déjà importées par l'IA :
- Noms avec "(1)", "(2)", etc.
- Recettes avec "How to Cook" dans le nom
- Recettes provenant d'URLs externes

## 📊 Endpoints API utilisés

### Cookbooks
- `GET /api/households/cookbooks` - Lister les cookbooks
- `POST /api/households/cookbooks` - Créer un cookbook
- `GET /api/households/cookbooks/{id}` - Voir un cookbook
- `PUT /api/households/cookbooks/{id}` - Mettre à jour un cookbook

### Recettes
- `POST /api/recipes/create/url` - Importer une recette depuis une URL
- `GET /api/recipes/{slug}` - Récupérer une recette
- `GET /api/recipes` - Lister toutes les recettes

## 🔄 Workflow d'import

1. **Vérification** : Le système vérifie si le cookbook "Import IA" existe
2. **Création** : Si non, il le crée avec les paramètres par défaut
3. **Détection** : Identifie les recettes à organiser
4. **Ajout** : Ajoute chaque recette identifiée au cookbook
5. **Confirmation** : Affiche le résumé de l'opération

## 📝 Structure du cookbook

```json
{
  "name": "Import IA",
  "slug": "import-ia",
  "description": "Recettes importées automatiquement par l'IA",
  "public": false,
  "recipes": [
    {"id": "uuid-recette-1"},
    {"id": "uuid-recette-2"}
  ]
}
```

## 🎨 Personnalisation

### Modifier le nom du cookbook

Changez les variables dans la classe `CookbookImportIA` :

```python
self.cookbook_name = "Mon Livre IA"
self.cookbook_slug = "mon-livre-ia"
```

### Ajouter des catégories

Modifiez la création du cookbook :

```python
cookbook_data = {
    "name": self.cookbook_name,
    "slug": self.cookbook_slug,
    "description": "Recettes importées automatiquement par l'IA",
    "public": False,
    "categories": ["Plats principaux", "Desserts", "Entrées"]
}
```

## 🔍 Détection des recettes IA

Le système utilise plusieurs critères pour identifier les recettes importées par l'IA :

1. **Noms avec numéros** : `(1)`, `(2)`, etc.
2. **Mots-clés anglais** : `How to Cook`, `Lentil recipes`
3. **URLs externes** : `orgURL` commençant par `https://www.`
4. **Absence de caractères français** : pas d'accents français

## 📈 Rapport d'activité

Après exécution, le système affiche :

- 📊 Nombre total de recettes dans Mealie
- 📚 Nombre de recettes dans le cookbook Import IA
- 📈 Pourcentage d'organisation
- ✅ Recettes réussies/échouées

## 🛠️ Résolution des problèmes

### Erreur 401 - "Could not validate credentials"

**Solution** : Mettez à jour votre token API Mealie

### Erreur 405 - "Method Not Allowed"

**Solution** : Vérifiez que vous utilisez les bons endpoints (cookbooks au lieu de categories)

### Recette non ajoutée

**Vérifiez** :
- L'ID de la recette est valide
- Le cookbook existe bien
- Les permissions de l'utilisateur

## 🚀 Automatisation future

Pour rendre le système entièrement automatique :

1. **Intégrer avec le scraper** : Modifier le script de scraping pour ajouter automatiquement au cookbook
2. **Webhook** : Configurer un webhook Mealie pour déclencher l'organisation
3. **Planification** : Utiliser cron pour exécuter périodiquement

## 📞 Support

En cas de problème :

1. Vérifiez la connexion API avec curl
2. Consultez les logs Mealie
3. Testez manuellement avec l'interface web

---

**🎉 Votre livre de recettes "Import IA" est prêt !**

Toutes les futures imports IA seront automatiquement organisées dans ce cookbook dédié.
