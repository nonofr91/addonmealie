# 📧 Solution : Créer un utilisateur sans email dans Mealie

## 🎯 Problème identifié

Les invitations par email ne fonctionnent pas car les paramètres email ne sont pas configurés dans Mealie.

## 🔧 Solutions alternatives

### Solution 1 : Création directe dans l'admin panel

1. **Allez dans Admin Panel**
2. **Cherchez "Users Management"**
3. **Cherchez un bouton "Create User" ou "Add User"**
4. **Remplissez directement le formulaire** sans passer par l'email

### Solution 2 : Utiliser l'API (si vous avez un token admin)

Si vous avez accès à l'API avec un compte admin :

```python
import requests

# Utilisez votre token admin existant
headers = {
    "Authorization": "Bearer VOTRE_TOKEN_ADMIN",
    "Content-Type": "application/json"
}

# Créez l'utilisateur directement
user_data = {
    "username": "import-ia",
    "fullName": "Import IA System", 
    "email": "import-ia@local.local",  # email fictif
    "password": "MotDePasseSecurise123!",
    "group": "Home",
    "household": "Family"
}

response = requests.post(
    "https://mealie-ffkfjdtvq2irbm3s5553sako.int.cubixmedia.fr/api/users/register",
    json=user_data,
    headers=headers
)

print(response.status_code)
print(response.text)
```

### Solution 3 : Activer les inscriptions publiques

1. **Allez dans les paramètres du groupe**
2. **Activez "Allow Signup"** (Autoriser les inscriptions)
3. **Allez sur la page d'inscription** : `/users/register`
4. **Créez le compte manuellement**

### Solution 4 : Utiliser la CLI (accès serveur)

Si vous avez accès au serveur Docker :

```bash
# Connectez-vous au conteneur
docker exec -it mealie bash

# Créez un utilisateur admin
python /opt/mealie/lib64/python3.12/site-packages/mealie/scripts/make_admin.py
```

### Solution 5 : Configuration email rapide

Si vous voulez configurer les emails rapidement :

1. **Utilisez un service SMTP gratuit** comme SMTP2GO
2. **Configurez les variables d'environnement** :
```bash
# Dans votre docker-compose.yml ou .env
EMAIL_HOST=smtp.smtp2go.com
EMAIL_PORT=2525
EMAIL_USERNAME=votre-email@smtp2go.com
EMAIL_PASSWORD=votre-mot-de-passe
EMAIL_FROM=noreply@votredomaine.com
```

## 🚀 **Solution recommandée pour vous**

### Option A : Vérifier si vous pouvez créer directement

1. **Cherchez dans Admin Panel** :
   - Users → Create User
   - Users → Add User
   - Data Management → Users

2. **Cherchez ces boutons** :
   - "Create New User"
   - "Add User"
   - "New User"

### Option B : Activer les inscriptions publiques

1. **Allez dans Group Settings**
2. **Cherchez "Allow Signup"**
3. **Activez l'option**
4. **Allez sur** : `https://mealie-.../users/register`
5. **Créez le compte "import-ia"**

### Option C : Utiliser votre compte existant

Si votre compte actuel a des permissions admin :

1. **Testez si vous pouvez créer des utilisateurs** via l'API
2. **Utilisez le script Python** ci-dessus

## 🔍 **Comment vérifier vos permissions**

Testez votre token actuel :

```bash
curl -H "Authorization: Bearer VOTRE_TOKEN" "https://mealie-.../api/groups/self"
```

Si ça fonctionne, vous pouvez peut-être créer des utilisateurs directement.

## 📋 **Étapes immédiates**

1. **Cherchez "Create User"** dans votre admin panel
2. **Si pas trouvé**, activez "Allow Signup" dans les paramètres
3. **Créez le compte** `import-ia` manuellement
4. **Connectez-vous** avec ce nouveau compte
5. **Créez le token API** depuis ce compte

---

**🎯 Une fois l'utilisateur créé sans email, tout fonctionnera !**
