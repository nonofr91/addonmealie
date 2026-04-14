# Local Addon Dev Flow

## But

Définir le parcours développeur local canonique pour tester un addon externe Mealie contre une instance locale Docker avant validation dans Coolify.

## Portée

Cette spec décrit le flux local recommandé pour :

- démarrer Mealie en local
- configurer un addon pour viser cette instance
- exécuter les commandes locales supportées
- constater les limites actuelles avant validation plateforme

## Pré-requis

- Docker et Docker Compose disponibles localement
- stack locale `packages/mealie-dev-stack/`
- addon cible disponible dans le repo, en priorité `addons/mealie-import-orchestrator/`
- configuration locale externalisée via `.env`

## Parcours recommandé

### 1. Démarrer Mealie en local

- aller dans `packages/mealie-dev-stack/`
- copier `.env.template` vers `.env`
- lancer `docker compose up -d`
- vérifier que Mealie répond localement sur le port configuré

## 2. Préparer l'accès API local

- ouvrir l'interface locale de Mealie
- créer ou récupérer une clé API depuis l'instance locale
- conserver cette clé hors du repo, dans le `.env` local de l'addon ou dans l'environnement du shell

## 3. Configurer l'addon localement

Pour `addons/mealie-import-orchestrator/` :

- copier `.env.template` vers `.env`
- renseigner `MEALIE_BASE_URL` avec l'URL locale de Mealie, par défaut `http://localhost:9925/api`
- renseigner `MEALIE_API_KEY`
- renseigner `MEALIE_IMPORT_ORCHESTRATOR_REPO_ROOT` avec la racine absolue du monorepo si nécessaire
- laisser `MEALIE_IMPORT_ORCHESTRATOR_ENABLE_SCRAPING=false` tant qu'un backend de scraping serveur n'est pas réellement prêt

## 4. Exécuter les commandes locales supportées

### Vérification minimale

- lancer `mealie-import-orchestrator status`
- vérifier que l'addon charge correctement le workflow canonique

### Exécution par étape

- utiliser `step structuring --scraped-filename ...` pour tester une structuration sur fichier existant
- utiliser `step importing --structured-filename ...` pour tester un import sur fichier structuré existant

### Limite actuelle

- ne pas considérer `full` ou `step scraping` comme supportés par défaut en runtime addon local tant que le backend de scraping n'est pas industrialisé dans ce mode d'exécution

## 5. Vérifier les résultats

- observer la sortie standard de l'addon
- vérifier les fichiers produits par le workflow canonique
- vérifier dans Mealie local que les effets attendus sont visibles
- corriger localement avant toute validation dans Coolify

## 6. Passer à la validation Coolify

- ne promouvoir vers Coolify qu'un flux déjà vérifié localement
- utiliser Coolify pour valider packaging, variables d'environnement, réseau et runtime conteneurisé réel

## Résultats attendus

À la fin du parcours local :

- Mealie local fonctionne dans Docker
- l'addon cible sait joindre Mealie localement
- au moins une commande supportée est exécutable sans dépendance à Coolify
- les limites actuelles sont connues avant d'entrer en validation plateforme

## Source de vérité

- stack locale : `packages/mealie-dev-stack/`
- addon v1 : `addons/mealie-import-orchestrator/`
- stratégie d'environnements : `docs/decisions/development-environment-strategy.md`
