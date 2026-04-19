# Stratégie de Branching pour le Développement

## Problème

La branche `main` ne doit pas être polluée pendant le développement de nouvelles fonctionnalités. Les commits sur `main` doivent être réservés aux changements stables et validés.

## Stratégie

### Branches de fonctionnalité (feature branches)

Pour toute nouvelle fonctionnalité ou modification significative :

1. **Créer une branche de fonctionnalité** depuis `main` :
   ```bash
   git checkout -b feature/nom-de-la-fonctionnalite
   ```

2. **Développer et commiter** sur cette branche :
   ```bash
   git add .
   git commit -m "Description du changement"
   ```

3. **Tester et valider** la fonctionnalité

4. **Merger dans main** uniquement après validation :
   ```bash
   git checkout main
   git merge feature/nom-de-la-fonctionnalite
   git push origin main
   ```

5. **Supprimer la branche de fonctionnalité** après le merge :
   ```bash
   git branch -d feature/nom-de-la-fonctionnalite
   ```

### Nommage des branches

- `feature/nom-de-la-fonctionnalite` : nouvelles fonctionnalités
- `fix/nom-du-bug` : corrections de bugs
- `docs/nom-de-la-documentation` : modifications de documentation uniquement
- `refactor/nom-du-refactor` : refactoring sans changement de comportement

### Quand commiter sur main directement

- Corrections de typos mineures dans la documentation
- Mises à jour de configuration triviales
- Changements qui ne nécessitent pas de validation

## Exemple de workflow

```bash
# Développer une nouvelle fonctionnalité
git checkout -b feature/advanced-profiles
# ... développement et tests ...
git add .
git commit -m "feat: ajouter les profils avancés avec pathologies"
# ... validation ...
git checkout main
git merge feature/advanced-profiles
git push origin main
git branch -d feature/advanced-profiles
```

## Règles

- **Jamais** de développement actif sur `main`
- Les branches de fonctionnalité doivent être courtes (quelques jours à quelques semaines)
- Les commits doivent être atomiques et bien décrits
- Les PR (Pull Requests) sont recommandés pour les changements importants

## Outils

- Utiliser `git status` avant tout commit pour vérifier l'état
- Utiliser `git branch -a` pour voir toutes les branches
- Utiliser `git log --oneline --graph` pour visualiser l'historique

