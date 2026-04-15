# Système de Profils Mealie

Système pour basculer facilement entre les instances Mealie (local vs Coolify).

## Profils disponibles

### local (Développement)
- **URL** : http://127.0.0.1:9925
- **Usage** : Développement et tests rapides
- **Token** : MEALIE_LOCAL_API_KEY
- **Stack** : packages/mealie-dev-stack/

### coolify (Production)
- **URL** : https://mealie-ffkfjdtvq2irbm3s5553sako.int.cubixmedia.fr
- **Usage** : Validation et packaging réel
- **Token** : MEALIE_API_KEY

## Usage

### Voir le profil actuel
```bash
./scripts/mealie-profile.sh status
```

### Basculer vers un profil
```bash
# Pour le développement local
./scripts/mealie-profile.sh local

# Pour la production Coolify
./scripts/mealie-profile.sh coolify
```

### Configuration des variables d'environnement

Après avoir basculé vers un profil, exportez les variables correspondantes :

**Profil local** :
```bash
export MEALIE_BASE_URL="http://127.0.0.1:9925"
export MEALIE_LOCAL_API_KEY="<votre_token_local>"
```

**Profil Coolify** :
```bash
export MEALIE_BASE_URL="https://mealie-ffkfjdtvq2irbm3s5553sako.int.cubixmedia.fr"
export MEALIE_API_KEY="<votre_token_coolify>"
```

## Workflow recommandé

1. **Développement** : Toujours utiliser le profil `local`
2. **Validation** : Basculer vers `coolify` pour tester en conditions réelles
3. **Packaging** : Valider sur Coolify avant promotion

## Sécurité

- Ne jamais commiter de tokens dans le repo
- Utiliser `.env` ou variables d'environnement shell
- Les tokens sont différents pour chaque instance
- Le profil actuel est stocké dans `mealie-workflow/config/mealie-profiles.json`

## Intégration avec les outils

Le wrapper MCP (`mealie-workflow/mcp_auth_wrapper.py`) utilise automatiquement le profil actif si disponible, avec fallback sur les variables d'environnement directes.

## Distinction importante : MCP Cascade vs Wrapper HTTP

### MCP Cascade (Outils Cascade)
- **Instance actuelle** : Coolify (https://mealie-ffkfjdtvq2irbm3s5553sako.int.cubixmedia.fr)
- **Usage** : Outils Cascade dans l’IDE (mcp3_create_recipe, mcp3_get_recipes, etc.)
- **Configuration** : Externe à ce workspace, configurée dans l’environnement Cascade
- **Recettes actuelles** : 29 recettes sur l’instance Coolify
- **Limitation** : Ne peut pas être reconfiguré depuis ce workspace

### Wrapper HTTP (mealie-import-orchestrator)
- **Instance actuelle** : Dépend du profil actif (local ou coolify)
- **Usage** : Import via addon mealie-import-orchestrator
- **Configuration** : Via système de profils (`mealie-workflow/config/mealie-profiles.json`)
- **Recettes actuelles** : Dépend de l’instance ciblée
- **Avantage** : Fonctionne avec l’instance locale pour le développement

### Workflow recommandé
1. **Développement local** : Utiliser le profil `local` avec le wrapper HTTP
2. **Validation Coolify** : Basculer vers le profil `coolify` pour tester en conditions réelles
3. **Outils Cascade** : Utiliser les MCP Cascade pour interagir avec l’instance Coolify uniquement
