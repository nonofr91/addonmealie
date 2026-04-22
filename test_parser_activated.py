#!/usr/bin/env python3
"""Test l'import avec le parser hybride activé."""

import requests
import json

# Configuration
API_URL = "http://localhost:8002/import"

# Recette de test
test_recipe = {
    "url": "https://www.marmiton.org/recettes/recette_simplissimes-nouilles-sautees-au-poulet_37164.aspx",
    "name": "Test Parser Hybride",
    "description": "Test du parser hybride activé",
    "yield": "4",
    "ingredients": [
        "4 filets de poulet coupés en dés",
        "1 oignon très finement émincé",
        "2 cuillères à soupe d'huile d'olive",
        "4 cuillères à soupe de sauce soja",
        "brin de persil plat et de coriandre ciselés",
        "1 paquet de nouilles chinoises",
        "500 g de julienne de légumes"
    ],
    "instructions": [
        "Mélanger le poulet avec l'oignon, l'huile et la sauce soja",
        "Cuire les nouilles 3-4 minutes",
        "Faire sauter le poulet",
        "Ajouter les légumes et les nouilles"
    ]
}

print("🧪 Test de l'import avec parser hybride activé")
print("=" * 60)

try:
    response = requests.post(API_URL, json=test_recipe, timeout=60)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200 and response.json().get("success"):
        print("\n✅ Import réussi avec parser hybride activé")
        slug = response.json().get("slug")
        print(f"Slug: {slug}")
    else:
        print("\n❌ Import échoué")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
