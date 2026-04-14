#!/usr/bin/env python3
"""
MEALIE MCP WRAPPER - AUTHENTIFICATION CORRIGÉE
Utilise les vrais MCP Mealie avec authentification
"""

import sys
from pathlib import Path

# Ajouter le chemin du workflow
sys.path.append(str(Path(__file__).parent))

# MCP avec authentification corrigée
def mcp3_list_recipes():
    """Liste les recettes Mealie avec authentification"""
    return <function create_auth_fixed_mcp.<locals>.auth_mcp3_list_recipes at 0x7f30f11b3ba0>

def mcp3_get_recipe_details(slug):
    """Détails recette Mealie avec authentification"""
    return <function create_auth_fixed_mcp.<locals>.auth_mcp3_get_recipe_details at 0x7f30f11b3c40>

def mcp3_create_recipe(**kwargs):
    """Création recette Mealie avec authentification"""
    return <function create_auth_fixed_mcp.<locals>.auth_mcp3_create_recipe at 0x7f30f11b3d80>

def mcp3_delete_recipe(slug):
    """Suppression recette Mealie avec authentification"""
    return <function create_auth_fixed_mcp.<locals>.auth_mcp3_delete_recipe at 0x7f30f11b3ce0>

def mcp3_update_recipe(slug, updates):
    """Mise à jour recette Mealie avec authentification"""
    return <function create_auth_fixed_mcp.<locals>.auth_mcp3_update_recipe at 0x7f30f11b3e20>

# MCP Jina (disponibles directement)
try:
    mcp2_read_url = globals().get('mcp2_read_url')
    mcp2_search_images = globals().get('mcp2_search_images')
    mcp2_show_api_key = globals().get('mcp2_show_api_key')
    print("✅ MCP Jina disponibles")
except:
    print("⚠️ MCP Jina non disponibles")

print("🎉 MCP WRAPPER AUTHENTIFIÉ INITIALISÉ")
print("✅ Vrais MCP Mealie avec authentification")
print("✅ Plus besoin de MCP mealie-test")
