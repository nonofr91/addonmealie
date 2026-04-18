# Labs

Ce dossier accueille les expérimentations structurées et les fonctionnalités en cours de développement qui ne sont pas encore prêtes pour publication.

## Règles

- ✅ **Promotion** : une expérimentation utile doit être promue dans le module canonique (`addons/`, `packages/`, `scripts/`)
- ✅ **Suppression** : une expérimentation abandonnée doit être supprimée
- ✅ **Pas de source de vérité** : `labs/` n'est pas une source de vérité produit
- ✅ **Documentation** : chaque expérimentation doit avoir un README expliquant l'objectif et l'état

## Workflow

1. Créer un dossier pour l'expérimentation : `labs/ma-feature/`
2. Ajouter un README.md avec :
   - Objectif de l'expérimentation
   - État actuel (WIP, prototype, etc.)
   - Critères de promotion vers le module canonique
3. Développer dans `labs/ma-feature/`
4. Quand prêt :
   - Déplacer le code dans le module canonique approprié
   - Supprimer le dossier `labs/ma-feature/`
   - Mettre à jour la documentation

## Alternatives

Pour les fonctionnalités plus structurées, utilisez des **branches de feature** :
```bash
git checkout -b feature/nouvelle-fonctionnalite
# Développer
git commit -m "WIP: nouvelle fonctionnalité"
git push origin feature/nouvelle-fonctionnalite
# Créer un PR en mode "draft" pour ne pas publier
```

## Exemple de structure

```
labs/
  experimental-api/
    README.md
    src/
    tests/
  prototype-ui/
    README.md
    components/
```
