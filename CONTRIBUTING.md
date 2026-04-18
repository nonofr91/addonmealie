# Contribuer au projet Mealie Addons

Merci de votre intérêt pour contribuer au projet Mealie Addons ! Ce document explique comment participer au développement.

## Comment contribuer

### Signaler des bugs

Ouvrez une issue sur GitHub avec :
- Un titre descriptif
- La version de l'addon concernée
- Les étapes pour reproduire le bug
- Le comportement attendu vs observé
- Des logs ou captures d'écran si pertinents

### Proposer des fonctionnalités

Avant de proposer une nouvelle fonctionnalité :
1. Vérifiez si une issue similaire existe déjà
2. Ouvrez une issue pour discuter de la fonctionnalité
3. Attendez l'approbation avant de commencer le développement

### Soumettre une Pull Request

1. Forker le dépôt
2. Créer une branche : `git checkout -b feature/ma-fonctionnalite`
3. Faire les changements et commiter
4. Pusher vers votre fork : `git push origin feature/ma-fonctionnalite`
5. Ouvrir une Pull Request sur GitHub

## Processus de développement

### Branching

- `main` : branche principale stable
- `feature/xxx` : nouvelles fonctionnalités
- `fix/xxx` : corrections de bugs
- `docs/xxx` : modifications de documentation

### Commits

Utilisez des messages de commit clairs et descriptifs :
```
feat: ajouter le support de l'export PDF
fix: corriger l'erreur de parsing des ingrédients
docs: mettre à jour le guide d'installation
```

### Code review

Toutes les Pull Requests doivent être revues avant d'être mergées. Le mainteneur peut :
- Demander des modifications
- Poser des questions
- Approuver ou rejeter la PR

## Standards de code

### Python

- Python 3.12+
- Suivre PEP 8
- Utiliser type hints quand possible
- Ajouter des docstrings pour les fonctions publiques

### Formatting

Utilisez `black` pour le formatting :
```bash
pip install black
black .
```

### Linting

Utilisez `ruff` pour le linting :
```bash
pip install ruff
ruff check .
```

## Tests

### Exécuter les tests

```bash
pytest tests/
```

### Ajouter des tests

Les nouvelles fonctionnalités doivent inclure des tests. Placez les tests dans le dossier `tests/` avec une structure qui reflète celle du code source.

### Couverture de tests

Visez une couverture de tests minimale de 70% pour le nouveau code.

## Documentation

### Mettre à jour les README

Quand vous modifiez une fonctionnalité, mettez à jour :
- Le README de l'addon concerné
- La documentation utilisateur si nécessaire
- Le changelog si applicable

### Documentation API

Pour les modifications de l'API, mettez à jour la documentation des endpoints dans le README de l'addon.

## Code of Conduct

### Être respectueux

Traitez tous les contributeurs avec respect, indépendamment de leur expérience, identité ou niveau de contribution.

### Être constructif

Les critiques doivent être constructives et orientées vers l'amélioration du code et du projet.

### Être inclusif

Le projet accueille les contributeurs de tous horizons. Le harcèlement sous toutes ses formes n'est pas toléré.

## Licence et droits

En contribuant à ce projet, vous acceptez que vos contributions soient licensiées sous la licence MIT du projet.

## Obtenir de l'aide

- GitHub Issues : pour les bugs et questions
- GitHub Discussions : pour les discussions générales
- Email : pour les questions sensibles

## Reconnaissance

Les contributeurs seront reconnus dans le fichier CONTRIBUTORS.md une fois leurs contributions mergées.
