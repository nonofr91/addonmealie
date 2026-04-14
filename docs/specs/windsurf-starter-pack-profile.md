# Windsurf Starter Pack Profile

## Objectif

Créer un profil Windsurf réutilisable pour initialiser rapidement des nouveaux projets avec gouvernance intégrée.

## Configuration du profil

### Fichiers de base
- `AGENTS_STARTER_PACK.md` - Gouvernance neutre à adapter
- `README_STARTER_PACK.md` - Documentation du starter pack
- `.windsurf/rules/generic-domain.md` - Règles génériques
- `scripts/setup-starter-pack.py` - Script d'initialisation interactive

### Workflows inclus
- `/task-intake` - Qualification des demandes
- `/bootstrap-project` - Initialisation depuis ce starter pack
- `/bug-investigation` - Diagnostic de bugs
- `/repo-hygiene` - Validation structurelle
- `/cleanup-task` - Nettoyage post-tâche
- `/promote-experiment` - Promotion d'expérimentations

### Skills disponibles
- `repo-governance` - Gouvernance de repo
- `contract-review` - Revue de contrats

## Utilisation du profil

### 1. Création du profil Windsurf
1. Ouvrir Windsurf
2. Créer un nouveau profil : "Windsurf Starter Pack"
3. Copier les fichiers du starter pack dans le workspace du profil
4. Configurer les extensions Windsurf nécessaires

### 2. Initialisation d'un nouveau projet
1. Ouvrir une nouvelle fenêtre avec le profil "Windsurf Starter Pack"
2. Exécuter `python scripts/setup-starter-pack.py`
3. Répondre aux questions interactives
4. Le script configure automatiquement :
   - README.md adapté au projet
   - AGENTS.md avec le contexte spécifique
   - Règle métier dédiée
   - Première décision d'architecture

### 3. Validation
1. Exécuter `/repo-hygiene` pour vérifier la structure
2. Commencer le développement avec `/task-intake`

## Avantages du profil

- **Immédiat** : Disponible instantanément dans Windsurf
- **Isolé** : Chaque projet a son propre environnement
- **Réutilisable** : Plusieurs projets peuvent utiliser le même profil
- **Configurable** : Adaptation interactive au domaine spécifique
- **Gouverné** : Règles et workflows intégrés dès le début

## Maintenance

- Mettre à jour les workflows et skills dans le profil
- Documenter les améliorations dans `docs/specs/`
- Partager les décisions d'architecture dans `docs/decisions/`

## Évolutions possibles

1. **Extension Windsurf native** : Intégration directe dans l'écosystème
2. **Templates par domaine** : Pré-configuration pour e-commerce, IoT, etc.
3. **Intégration CI/CD** : Pipelines de validation automatiques
4. **Skills spécialisés** : Expertises métier par domaine

---

*Cette approche combine l'immédiateté du profil Windsurf avec la flexibilité du starter pack configurable.*
