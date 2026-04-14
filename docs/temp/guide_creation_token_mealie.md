# 🔑 Guide Officiel : Création Token API Mealie

## 📋 Documentation officielle

Selon la documentation Mealie officielle :

> **Getting a Token**
> 
> Mealie supports long-live api tokens in the user frontend. These can be created on the `/user/profile/api-tokens` page.

## 🚀 Étapes pour créer un token API

### 1. **Connectez-vous à Mealie**
- Allez sur votre instance Mealie : `https://mealie-ffkfjdtvq2irbm3s5553sako.int.cubixmedia.fr`
- Connectez-vous avec votre compte utilisateur

### 2. **Accédez à la page des tokens**
- Cliquez sur votre nom d'utilisateur en haut à gauche
- Allez dans votre profil
- Naviguez vers la page : `/user/profile/api-tokens`
- Ou directement : `https://mealie-ffkfjdtvq2irbm3s5553sako.int.cubixmedia.fr/user/profile/api-tokens`

### 3. **Créez un nouveau token**
- Cliquez sur "Create API Token" ou "Créer un token API"
- Donnez un nom à votre token (ex: "Import IA Script")
- Copiez immédiatement le token généré

### 4. **Testez votre nouveau token**

Utilisez le script `test_new_token.py` :

```bash
# Éditez le fichier
nano test_new_token.py

# Remplacez NEW_TOKEN avec votre token copié
NEW_TOKEN = "votre_nouveau_token_ici"

# Testez
python test_new_token.py
```

### 5. **Utilisez le token**

Si le test réussit, utilisez `import_ia_avec_nouveau_token.py` :

```bash
# Éditez le fichier
nano import_ia_avec_nouveau_token.py

# Remplacez NEW_TOKEN_ICI avec votre token
API_TOKEN = "votre_nouveau_token_ici"

# Exécutez
python import_ia_avec_nouveau_token.py
```

## 🔍 Points importants

### ✅ Token long-lived
- Les tokens Mealie sont "long-lived" (durent longtemps)
- Pas besoin de les renouveler fréquemment

### 🛡️ Sécurité
- **Copiez immédiatement** le token après création
- Ne partagez jamais votre token
- Stockez-le dans un endroit sécurisé

### 📋 Permissions
- Le token hérite des permissions de l'utilisateur qui le crée
- Assurez-vous que votre utilisateur a les permissions nécessaires :
  - Gérer les recettes
  - Accéder aux cookbooks
  - Si possible, droits admin

## 🔧 Si problème de permissions

Si votre utilisateur n'a pas les permissions nécessaires :

1. **Contactez un admin** du groupe Mealie
2. **Demandez les permissions** :
   - Can Manage (gérer)
   - Can Manage Household (gérer le foyer)
   - Can Organize (organiser)

3. **Ou utilisez la solution CLI** (si vous avez accès au serveur) :
```bash
docker exec -it mealie bash
python /opt/mealie/lib64/python3.12/site-packages/mealie/scripts/make_admin.py
```

## 📞 Documentation complète

- **API Usage** : https://docs.mealie.io/documentation/getting-started/api-usage
- **Interactive API Docs** : https://mealie-ffkfjdtvq2irbm3s5553sako.int.cubixmedia.fr/docs
- **FAQ** : https://docs.mealie.io/documentation/getting-started/faq

## 🎯 Résultat attendu

Après avoir créé et utilisé votre nouveau token :

- ✅ Test de connexion réussi
- ✅ Permissions cookbooks fonctionnelles
- ✅ Cookbook "Import IA" créé
- ✅ Recettes organisées automatiquement

---

**🎉 Une fois le token créé, tout fonctionnera parfaitement !**
