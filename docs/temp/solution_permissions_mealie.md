# 🔧 SOLUTION : Permissions Mealie pour Import IA

## 🎯 Problème identifié

L'utilisateur "Mistral" n'a pas les permissions nécessaires pour accéder aux cookbooks (`/api/households/cookbooks` retourne 401).

## 🔍 Diagnostic

- ✅ Token valide (fonctionne pour `/api/app/about`)
- ❌ Permissions insuffisantes (401 sur `/api/households/cookbooks`)
- 🏷️ L'utilisateur n'est pas admin du groupe/household

## 🛠️ Solution officielle (documentation Mealie)

### Option 1 : Devenir admin via CLI (recommandé)

1. **Accéder au conteneur Mealie** :
```bash
docker exec -it mealie bash
```

2. **Exécuter le script admin** :
```bash
python /opt/mealie/lib64/python3.12/site-packages/mealie/scripts/make_admin.py
```

3. **Suivre les instructions** pour donner les droits admin à l'utilisateur "Mistral"

### Option 2 : Via l'interface web (si vous avez accès admin)

1. **Connectez-vous avec un compte admin**
2. **Allez dans Paramètres du groupe**
3. **Gérez les permissions de l'utilisateur "Mistral"**
4. **Activez les permissions** :
   - ✅ Can Manage (gérer)
   - ✅ Can Manage Household (gérer le foyer)
   - ✅ Can Organize (organiser)

### Option 3 : Vérifier les permissions actuelles

```bash
# Vérifier le statut de l'utilisateur
curl -H "Authorization: Bearer TOKEN" "https://mealie-.../api/users/self"
```

## 🚀 Une fois les permissions obtenues

### Test de connexion

```bash
# Test des cookbooks (devrait fonctionner)
curl -H "Authorization: Bearer TOKEN" "https://mealie-.../api/households/cookbooks"
```

### Exécuter le système Import IA

```bash
python cookbook_import_ia.py
```

## 📋 Étapes recommandées

1. **🔓 Devenir admin** (option 1)
2. **✅ Tester les permissions** cookbooks
3. **📚 Exécuter l'import** IA
4. **🎉 Vérifier le cookbook** "Import IA"

## 🎯 Résultat attendu

Après avoir obtenu les permissions admin :

- ✅ `GET /api/households/cookbooks` → 200 OK
- ✅ `POST /api/households/cookbooks` → 201 Created  
- ✅ `PUT /api/households/cookbooks/{id}` → 200 OK
- 📚 Cookbook "Import IA" créé
- 🗂️ Recettes organisées automatiquement

## 🔐 Sécurité

Les permissions admin permettent de :
- Gérer les cookbooks
- Organiser les recettes  
- Gérer le groupe et le household
- Accéder à toutes les fonctionnalités API

## 🆘 Si problème persiste

1. **Vérifiez le nom d'utilisateur** exact ("Mistral")
2. **Redémarrez Mealie** après changement de permissions
3. **Contactez l'admin** du groupe Mealie

---

**🎉 Le système Import IA fonctionnera parfaitement une fois les permissions admin obtenues !**
