# Mealie Platform Constraints

## Contexte

Le projet vise à construire des addons externes autour de Mealie en réutilisant les capacités du serveur MCP canonique et du pipeline existant, sans modifier l'image Mealie.

Pour garder un repo publiable et maintenable, il faut expliciter les contraintes de la plateforme cible avant de définir les futurs addons.

## Décision

Mealie doit être traité comme une plateforme externe stock dont l'image est immuable pour le projet.

Les addons et intégrations développés dans ce repo doivent rester externes à Mealie et s'appuyer uniquement sur des interfaces publiques, une configuration externalisée et des modules canoniques du repo.

## Rationale

### Alignement avec la gouvernance

- le repo a pour objectif de construire des addons externes à Mealie
- cette approche évite les forks, les personnalisations locales et les dépendances implicites à l'image Mealie
- elle permet de conserver une seule source de vérité par capacité métier

### Maintenabilité

- un addon externe peut évoluer sans coupler son cycle de vie à celui de l'image Mealie
- les frontières entre plateforme cible, MCP canonique, pipeline et addon restent explicites
- les montées de version Mealie sont plus simples à absorber si l'on dépend uniquement d'interfaces publiques

### Sécurité

- la configuration doit rester externalisée
- aucun secret ne doit être hardcodé dans le code versionné
- les addons ne doivent pas supposer d'accès privilégié au conteneur, au stockage interne ou à la base de données Mealie

## Contraintes retenues

### Image et exécution

- l'image Mealie n'est pas modifiée
- aucun code addon n'est embarqué dans le conteneur Mealie
- aucun addon ne dépend de paquets système ou de bibliothèques ajoutés dans l'image Mealie
- aucun addon ne dépend de chemins internes, de volumes ou de modules privés de Mealie

### Interfaces autorisées

- l'API publique de Mealie constitue l'interface d'intégration prioritaire
- le serveur canonique `mealie-mcp-server/` est la façade privilégiée quand une capacité MCP existe déjà
- les interfaces utilisateur spécifiques, workers, CLI et services vivent hors de Mealie

### Interfaces interdites ou non canoniques

- pas de fork ou patch de l'application Mealie
- pas d'écriture directe dans la base de données Mealie
- pas d'automatisation fondée sur le DOM ou le scraping de l'interface web comme stratégie principale
- pas de dépendance à des scripts historiques racine comme contrat stable de plateforme

### Configuration et sécurité

- l'URL Mealie, les tokens, timeouts et options d'exécution sont externalisés
- les secrets ne sont jamais versionnés ni affichés en clair dans les logs
- les addons valident leur configuration avant toute opération d'écriture

### Données et robustesse

- les payloads envoyés à Mealie doivent respecter les formats acceptés par ses interfaces publiques
- les traitements doivent viser l'idempotence autant que possible
- les addons doivent gérer proprement les erreurs partielles, les retries limités et la reprise d'exécution
- les rapports, logs et artefacts générés restent hors de Mealie

## Conséquences

- les addons futurs doivent être conçus comme des modules externes placés dans `addons/`
- `mealie-mcp-server/` reste la source de vérité pour la couche MCP et l'accès structuré à Mealie
- `mealie-workflow/` reste la source de vérité pour le pipeline métier existant
- un addon ne doit pas recopier la logique métier déjà canonique dans ces modules
- toute nouvelle spec d'addon doit expliciter ses entrées, sorties, effets de bord et dépendances à la plateforme Mealie
