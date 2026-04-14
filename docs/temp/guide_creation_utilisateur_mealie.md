# 👤 Guide Officiel : Création Utilisateur Mealie

## 📋 Documentation officielle

Selon la documentation Mealie officielle :

> **Users**
> 
> Add new users with sign-up links or simply create a new user in the admin panel.

## 🚀 Méthodes pour créer un utilisateur

### Méthode 1 : Via le panneau admin (recommandé)

1. **Connectez-vous avec un compte admin**
2. **Allez dans la section admin** :
   - Paramètres du site
   - Gestion des utilisateurs/households/groups
3. **Créez un nouvel utilisateur** directement dans l'interface

### Méthode 2 : Via les liens d'inscription

1. **Générez un lien d'inscription** depuis le panneau admin
2. **Partagez le lien** avec le nouvel utilisateur
3. **L'utilisateur s'inscrit** avec le lien

### Méthode 3 : Via l'API (si vous avez les permissions)

```python
import requests

headers = {
    "Authorization": "Bearer VOTRE_TOKEN_ADMIN",
    "Content-Type": "application/json"
}

user_data = {
    "username": "nouvel_utilisateur",
    "fullName": "Nouvel Utilisateur",
    "email": "utilisateur@exemple.com",
    "password": "mot_de_passe_securise",
    "group": "Home",  # ou votre groupe
    "household": "Family"  # ou votre household
}

response = requests.post("https://mealie-.../api/users/register", json=user_data, headers=headers)
```

## 🔍 Étapes détaillées (Méthode 1)

### 1. **Accès au panneau admin**
- Connectez-vous avec votre compte admin existant
- Cliquez sur votre nom d'utilisateur en haut à gauche
- Cherchez "Admin Panel" ou "Paramètres du site"

### 2. **Navigation vers la gestion des utilisateurs**
- Cherchez la section "Users", "Households", and "Groups"
- Cliquez sur "Users" pour voir la liste des utilisateurs

### 3. **Création du nouvel utilisateur**
- Cliquez sur "Add User" ou "Create User"
- Remplissez les informations :
  - **Username** : nom d'utilisateur unique
  - **Full Name** : nom complet
  - **Email** : adresse email
  - **Password** : mot de passe
  - **Group** : groupe (ex: "Home")
  - **Household** : foyer (ex: "Family")

### 4. **Configuration des permissions**
- Assurez-vous que le nouvel utilisateur a les permissions nécessaires :
  - ✅ Can Manage (gérer)
  - ✅ Can Manage Household (gérer le foyer)
  - ✅ Can Organize (organiser)
  - ✅ Admin (si possible)

## 🎯 **Pour notre projet Import IA**

### Création de l'utilisateur "Import IA"

1. **Informations suggérées** :
   - **Username** : `import-ia`
   - **Full Name** : `Import IA System`
   - **Email** : `import-ia@votredomaine.com`
   - **Password** : mot de passe sécurisé

2. **Permissions requises** :
   - ✅ Can Manage
   - ✅ Can Manage Household
   - ✅ Can Organize

3. **Après création** :
   - Connectez-vous avec ce nouvel utilisateur
   - Allez dans `/user/profile/api-tokens`
   - Créez un nouveau token "Import IA Script"
   - Utilisez ce token dans nos scripts

## 🔧 **Si vous n'avez pas de compte admin**

### Solution CLI (accès serveur requis)

```bash
# Connectez-vous au conteneur Mealie
docker exec -it mealie bash

# Créez un utilisateur admin
python /opt/mealie/lib64/python3.12/site-packages/mealie/scripts/make_admin.py
```

### Ou créez le premier utilisateur via l'interface

1. **Première inscription** : Si Mealie est neuf, le premier utilisateur devient automatiquement admin
2. **Lien d'inscription** : Utilisez le lien d'inscription par défaut

## 📞 **Références officielles**

- **Features Documentation** : https://docs.mealie.io/documentation/getting-started/features
- **Users Management** : Section "Users, Households, and Groups"
- **API Reference** : https://mealie-.../docs

## ✅ **Vérification après création**

Après avoir créé l'utilisateur :

1. **Testez la connexion** avec le nouvel utilisateur
2. **Vérifiez les permissions** dans le profil
3. **Créez le token API** depuis ce compte
4. **Testez le token** avec `test_new_token.py`

## 🎉 **Résultat attendu**

Une fois l'utilisateur créé avec les bonnes permissions :

- ✅ Token API fonctionnel
- ✅ Accès aux cookbooks
- ✅ Système Import IA opérationnel
- ✅ Cookbook "Import IA" créé automatiquement

---

**🚀 Une fois l'utilisateur "Import IA" créé, tout fonctionnera parfaitement !**
