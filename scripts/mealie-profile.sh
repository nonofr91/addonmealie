#!/bin/bash
# Script pour basculer entre les profils Mealie (local/coolify)

PROFILE_FILE="mealie-workflow/config/mealie-profiles.json"

show_current_profile() {
    if [ -f "$PROFILE_FILE" ]; then
        ACTIVE=$(python3 -c "import json; print(json.load(open('$PROFILE_FILE'))['active_profile'])")
        NAME=$(python3 -c "import json; print(json.load(open('$PROFILE_FILE'))['profiles']['$ACTIVE']['name'])")
        URL=$(python3 -c "import json; print(json.load(open('$PROFILE_FILE'))['profiles']['$ACTIVE']['url'])")
        echo "📍 Profil actuel: $ACTIVE"
        echo "📝 Nom: $NAME"
        echo "🌐 URL: $URL"
    else
        echo "❌ Fichier de profils non trouvé: $PROFILE_FILE"
    fi
}

switch_profile() {
    PROFILE=$1
    if [ -z "$PROFILE" ]; then
        echo "Usage: $0 {local|coolify|status}"
        exit 1
    fi

    if [ ! -f "$PROFILE_FILE" ]; then
        echo "❌ Fichier de profils non trouvé: $PROFILE_FILE"
        exit 1
    fi

    # Vérifier que le profil existe
    if ! python3 -c "import json; json.load(open('$PROFILE_FILE'))['profiles']['$PROFILE']" 2>/dev/null; then
        echo "❌ Profil inconnu: $PROFILE"
        echo "Profils disponibles: local, coolify"
        exit 1
    fi

    # Changer le profil actif
    python3 <<EOF
import json
with open('$PROFILE_FILE', 'r') as f:
    config = json.load(f)
config['active_profile'] = '$PROFILE'
with open('$PROFILE_FILE', 'w') as f:
    json.dump(config, f, indent=2)
EOF

    echo "✅ Profil changé vers: $PROFILE"
    show_current_profile
    echo ""
    echo "⚠️ N'oubliez pas d'exporter les variables d'environnement:"
    echo "   export MEALIE_BASE_URL=\$(python3 -c \"import json; print(json.load(open('$PROFILE_FILE'))['profiles']['$PROFILE']['url'])\")"
    echo "   export MEALIE_API_KEY=<token_pour_$PROFILE>"
}

# Point d'entrée
case "${1:-status}" in
    status)
        show_current_profile
        ;;
    local|coolify)
        switch_profile "$1"
        ;;
    *)
        echo "Usage: $0 {local|coolify|status}"
        exit 1
        ;;
esac
