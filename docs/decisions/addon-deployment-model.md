# Addon Deployment Model

## Contexte

Mealie est actuellement déployé via Coolify auto-hébergé en utilisant le template Mealie fourni par Coolify, basé sur Docker.

Le projet vise à construire des addons externes autour de Mealie sans modifier son image.

Le mode de déploiement des addons doit donc être défini tôt, car il influence la structure du code, la configuration, le packaging et les frontières entre modules canoniques.

## Décision

Mealie reste déployé comme service séparé via le template Docker Coolify existant.

Les addons du repo sont déployés comme services Docker séparés dans Coolify, sans modification de l'image Mealie et sans embarquer de code addon dans le conteneur Mealie.

Le modèle de déploiement cible distingue plusieurs types de runtime d'addon :

- job ou cron pour les orchestrations ponctuelles
- worker pour les traitements asynchrones ou continus
- web service pour les API ou interfaces externes
- outil local uniquement quand une capacité ne doit pas être déployée côté serveur

## Rationale

### Alignement avec les contraintes plateforme

- l'image Mealie reste immuable
- les addons restent externes à Mealie
- l'intégration passe par des interfaces publiques, la configuration externalisée et le réseau Docker fourni par Coolify

### Maintenabilité

- le cycle de vie de Mealie reste indépendant de celui des addons
- chaque addon peut être versionné, buildé et déployé séparément
- les responsabilités entre Mealie, MCP, workflow et addon restent lisibles

### Exploitabilité

- Coolify fournit déjà le modèle opératoire attendu pour des services Docker séparés
- les secrets et variables d'environnement peuvent être gérés par service
- les logs et statuts d'exécution s'intègrent naturellement au mode de déploiement conteneurisé

## Contraintes retenues

### Mealie

- Mealie reste un service séparé géré par Coolify
- le template officiel Coolify constitue le point de départ canonique du déploiement Mealie
- aucune personnalisation d'image n'est requise pour supporter les addons

### Addons

- chaque addon publiable vit dans son propre conteneur ou service Coolify
- un addon ne dépend pas d'un accès shell, volume interne ou base de données Mealie
- un addon communique avec Mealie via l'API publique ou via une couche canonique externe comme `mealie-mcp-server/` si pertinent

### Réseau et configuration

- les addons utilisent de préférence l'URL interne ou réseau pertinente exposée par Coolify pour joindre Mealie
- les secrets Mealie sont fournis par variables d'environnement ou secrets Coolify
- aucun secret n'est versionné dans le repo

### Packaging

- à court terme, les addons peuvent être buildés depuis le monorepo si cela accélère l'itération
- à moyen terme, les briques réutilisables doivent converger vers `packages/` pour limiter le couplage aux chemins internes du repo
- tout addon doit pouvoir être empaqueté sans dépendre d'un contexte manuel implicite sur la machine de déploiement

### Observabilité et exécution

- les logs doivent être écrits vers stdout et stderr
- les jobs doivent exposer un code de sortie explicite
- les services longs doivent prévoir un healthcheck quand cela est pertinent
- les artefacts générés par un addon doivent vivre dans son propre espace, pas dans le stockage interne de Mealie

## Conséquences

- `mealie-import-orchestrator` est orienté en priorité vers un déploiement de type job ou cron Coolify
- un futur addon d'API ou de dashboard devra être conçu comme web service séparé
- les choix de développement doivent éviter les chemins magiques et les dépendances implicites au monorepo
- l'extraction progressive de logique partagée vers `packages/` devient une trajectoire d'architecture souhaitable
- la documentation de tout addon devra préciser son type de runtime, ses variables d'environnement, ses volumes éventuels et ses dépendances réseau
