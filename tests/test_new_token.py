#!/usr/bin/env python3
"""
Script pour tester un token Mealie via variables d'environnement
"""

import os
import sys
import requests

# Configuration depuis variables d'environnement
API_URL = os.getenv("MEALIE_BASE_URL")
API_TOKEN = os.getenv("MEALIE_API_KEY")

if not API_URL or not API_TOKEN:
    print("❌ Variables d'environnement manquantes")
    print("   Exportez MEALIE_BASE_URL et MEALIE_API_KEY")
    print("   Exemple:")
    print("   export MEALIE_BASE_URL=https://your-mealie-instance.com/api")
    print("   export MEALIE_API_KEY=your-api-key")
    sys.exit(1)

def test_token():
    """Test complet du token"""
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("🧪 TEST DU TOKEN MEALIE")
    print("=" * 40)
    print(f"🔗 API: {API_URL}")
    
    # Test 1: Connexion de base
    try:
        response = requests.get(f"{API_URL}/app/about", headers=headers)
        if response.status_code == 200:
            print("✅ Connexion API réussie")
        else:
            print(f"❌ Erreur connexion: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception connexion: {e}")
        return False
    
    # Test 2: Infos utilisateur
    try:
        response = requests.get(f"{API_URL}/users/self", headers=headers)
        if response.status_code == 200:
            user = response.json()
            print(f"✅ Utilisateur: {user.get('fullName', 'N/A')}")
            print(f"   Email: {user.get('email', 'N/A')}")
            print(f"   Admin: {user.get('admin', False)}")
        else:
            print(f"❌ Erreur utilisateur: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception utilisateur: {e}")
        return False
    
    # Test 3: Permissions cookbooks
    try:
        response = requests.get(f"{API_URL}/households/cookbooks", headers=headers)
        if response.status_code == 200:
            print("✅ Permissions cookbooks OK")
            return True
        else:
            print(f"❌ Erreur cookbooks: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception cookbooks: {e}")
        return False

if __name__ == "__main__":
    if test_token():
        print("\n🎉 Token valide ! Vous pouvez maintenant utiliser les scripts d'import")
    else:
        print("\n❌ Token invalide ou permissions insuffisantes")
