# Plateforme Mealie Addons + Windsurf Starter Pack

Plateforme locale pour construire des améliorations externes à Mealie avec Cascade, ainsi qu'un starter pack Windsurf réutilisable pour des projets agentiques propres et maintenables.

## Objectifs

- Construire des addons externes autour de Mealie sans modifier l'image Mealie.
- Préserver une source de vérité unique par capacité métier.
- Structurer le repo pour limiter la pollution et les variantes concurrentes.
- Fournir un socle Windsurf réutilisable : `AGENTS.md`, `Rules`, `Workflows`, `Skills`, structure canonique et documentation de gouvernance.

## Capacités couvertes

- Import de recettes et pipeline hybride Python + IA
- Normalisation des recettes et ingrédients
- Analyse nutritionnelle
- Optimisation des listes de courses
- Gestion d'images
- Outillage MCP et workflows externes autour de Mealie

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
- Préférer les MCP disponibles avant d'ajouter une intégration Mealie ad hoc
- Produire une spec courte pour les changements non triviaux
- Nettoyer les artefacts et mettre à jour la documentation durable en fin de tâche

## Pour démarrer

1. Lire `AGENTS.md`
2. Utiliser `/task-intake` pour cadrer une nouvelle demande
3. Utiliser `Plan mode` pour les changements structurants
4. Utiliser les workflows de gouvernance avant et après les tâches à risque
5. Consulter `docs/decisions/windsurf-project-operating-model.md` pour le modèle opératoire du repo

## Réutiliser ce repo comme template

- Utiliser `/bootstrap-project` pour initialiser un nouveau repo à partir de ce starter pack.
- Conserver le noyau de gouvernance : `AGENTS.md`, `.gitignore`, `.windsurf/rules/`, workflows génériques, skills transverses et documentation canonique.
- Adapter le contexte produit dans `README.md`, `AGENTS.md` et la règle métier dédiée au nouveau domaine.
- Retirer les workflows, skills, scripts et données trop spécifiques au domaine source.
- Documenter le bootstrap du nouveau repo dans `docs/specs/` et sa première décision structurante dans `docs/decisions/`.

## Sécurité

- Garder les secrets hors du code versionné
- Utiliser `.env.template` quand un exemple de configuration est nécessaire
- Passer par des interfaces publiques et des intégrations externes à Mealie
