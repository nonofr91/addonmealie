# Windsurf Starter Pack

Base de projet réutilisable pour construire des applications propres et maintenables avec Cascade.

## Objectifs

- Démarrer rapidement avec une gouvernance intégrée
- Structurer le repo pour limiter la pollution et les variantes concurrentes
- Fournir un socle Windsurf réutilisable : `AGENTS.md`, `Rules`, `Workflows`, `Skills`, structure canonique
- Éviter la duplication de logique et maintenir une source de vérité par capacité

## Couche Windsurf du projet

- `AGENTS.md` : gouvernance always-on du repo
- `.windsurf/rules/` : contraintes courtes et durables par type de fichier ou domaine
- `.windsurf/workflows/` : procédures manuelles réutilisables
- `.windsurf/skills/` : expertises métier et de gouvernance réutilisables
- `docs/specs/` : spécifications courtes
- `docs/decisions/` : décisions d'architecture et de gouvernance

## Structure recommandée

- `addons/` pour les addons externes publiables
- `packages/` pour le code partagé
- `scripts/` pour l'orchestration stable
- `tests/` pour les validations
- `labs/` pour les expérimentations structurées
- `tmp/` pour le temporaire
- `reports/` et `data/generated/` pour le généré

## Règles de conduite essentielles

- Ne pas créer de nouveau fichier métier à la racine
- Ne pas multiplier les fichiers `final`, `debug`, `copy`, `fixed`, `v2`, `v3`
- Produire une spec courte pour les changements non triviaux
- Nettoyer les artefacts et mettre à jour la documentation durable en fin de tâche

## Pour démarrer un nouveau projet

1. **Utiliser ce starter pack** comme base pour votre nouveau projet
2. **Exécuter `/bootstrap-project`** pour configurer le contexte spécifique
3. **Adapter le README.md** pour décrire votre projet et son domaine
4. **Créer la règle métier** dans `.windsurf/rules/` si votre domaine le justifie
5. **Utiliser `/repo-hygiene`** pour valider la structure

## Workflows essentiels

- `/task-intake` - Qualifier une demande avant planification
- `/bootstrap-project` - Initialiser un nouveau projet depuis ce starter pack
- `/bug-investigation` - Diagnostiquer un bug avant correction
- `/repo-hygiene` - Vérifier que les changements respectent la structure du repo
- `/cleanup-task` - Nettoyer les fichiers temporaires après une tâche
- `/promote-experiment` - Transformer une expérimentation en implémentation canonique

## Skills disponibles

- `repo-governance` - Appliquer les règles de structure du repo
- `contract-review` - Vérifier les contrats d'entrée/sortie d'un module

## Sécurité

- Garder les secrets hors du code versionné
- Utiliser `.env.template` quand un exemple de configuration est nécessaire
- Passer par des interfaces publiques et des intégrations externes

---

*Ce starter pack est conçu pour être adapté à tout type de projet tout en conservant une gouvernance robuste et une structure propre.*
