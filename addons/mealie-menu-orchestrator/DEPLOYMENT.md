# Guide de déploiement - Mealie Menu Orchestrator

## Prérequis

- Docker et Docker Compose installés
- Accès à Coolify (pour le déploiement en production)
- Nutrition Advisor déployé (port 8001)
- Budget Advisor déployé (port 8003)
- Mealie accessible avec clé API

## Développement local

### 1. Configuration

```bash
cd addons/mealie-menu-orchestrator
cp .env.template .env
# Éditer .env avec vos configurations
```

### 2. Installation des dépendances

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 3. Démarrage de l'API

```bash
python3 -m mealie_menu_orchestrator.api
```

L'API sera accessible sur http://localhost:8004

### 4. Démarrage de l'UI Streamlit

```bash
streamlit run src/mealie_menu_orchestrator/ui.py --server.headless=true --browser.gatherUsageStats=false --server.fileWatcherType=none
```

L'UI sera accessible sur http://localhost:8501

## Déploiement Docker local

### 1. Build de l'image

```bash
docker build -t mealie-menu-orchestrator:0.1.0 .
```

### 2. Démarrage avec docker-compose

```bash
docker-compose -f docker-compose.coolify.yml up -d
```

## Déploiement sur Coolify

### 1. Préparation du repository

S'assurer que tous les fichiers sont commités:

```bash
git add .
git commit -m "feat: menu orchestrator addon initial implementation"
git push origin main
```

### 2. Création de l'application dans Coolify

1. Créer une nouvelle application "Dockerfile"
2. Connecter au repository GitHub
3. Sélectionner le Dockerfile dans `addons/mealie-menu-orchestrator/`
4. Configurer les variables d'environnement

### 3. Variables d'environnement requises

```
MEALIE_BASE_URL=https://mealie-ffkfjdtvq2irbm3s5553sako.int.cubixmedia.fr
MEALIE_API_KEY=votre_clé_api_mealie
NUTRITION_ADVISOR_URL=https://nutrition-advisor-url
NUTRITION_ADVISOR_KEY=votre_clé_api_nutrition
BUDGET_ADVISOR_URL=https://budget-advisor-url
BUDGET_ADVISOR_KEY=votre_clé_api_budget
API_HOST=0.0.0.0
API_PORT=8004
ADDON_SECRET_KEY=votre_clé_secrète
ENABLE_MENU_GENERATION=true
ENABLE_VARIETY_TRACKING=true
ENABLE_SEASONALITY=false
WEIGHT_NUTRITION=0.25
WEIGHT_BUDGET=0.25
WEIGHT_VARIETY=0.25
WEIGHT_SEASON=0.25
```

### 4. Déploiement

- Déployer l'application API
- Déployer une deuxième application UI avec la commande:
  ```
  streamlit run src/mealie_menu_orchestrator/ui.py --server.headless=true --browser.gatherUsageStats=false --server.fileWatcherType=none
  ```

### 5. Configuration du réseau

S'assurer que toutes les applications (Mealie, Nutrition Advisor, Budget Advisor, Menu Orchestrator) sont sur le même réseau Docker pour la communication interne.

## Tests

### Test de santé de l'API

```bash
curl http://localhost:8004/health
```

### Test de génération de menu

```bash
curl -X POST http://localhost:8004/menus/generate \
  -H "Content-Type: application/json" \
  -H "X-Addon-Key: votre_clé_secrète" \
  -d '{
    "start_date": "2026-01-01",
    "end_date": "2026-01-07",
    "budget_limit": 200.0
  }'
```

### Test de récupération de menu

```bash
curl http://localhost:8004/menus/{menu_id} \
  -H "X-Addon-Key: votre_clé_secrète"
```

## Dépannage

### L'API ne démarre pas

- Vérifier que les variables d'environnement sont correctement définies
- Vérifier que Nutrition Advisor et Budget Advisor sont accessibles
- Consulter les logs de l'application

### Les scores sont tous à 0

- Vérifier que Nutrition Advisor et Budget Advisor retournent des données
- Consulter les logs pour voir les erreurs de connexion aux services externes

### L'UI Streamlit ne se connecte pas à l'API

- Vérifier que l'URL de l'API dans la configuration de l'UI est correcte
- Vérifier que le service API est en cours d'exécution
- Consulter les logs de l'UI pour les erreurs de connexion

## Maintenance

### Mise à jour de l'application

1. Mettre à jour le code
2. Committer et pousser les changements
3. Déclencher un nouveau déploiement dans Coolify

### Nettoyage des menus en mémoire

Le stockage actuel est en mémoire. Les menus sont perdus au redémarrage. Pour un stockage persistant, il faudrait:
- Ajouter une base de données (SQLite, PostgreSQL)
- Implémenter une persistance dans Mealie (tags, métadonnées)
- Utiliser un stockage externe (Redis)

## Sécurité

- Ne jamais exposer les clés API dans le code
- Utiliser des secrets Coolify pour les variables d'environnement sensibles
- Configurer le firewall pour limiter l'accès aux ports internes
- Utiliser HTTPS en production
