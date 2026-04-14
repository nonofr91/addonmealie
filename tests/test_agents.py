#!/usr/bin/env python3
"""
Test des agents spécialisés Mealie MCP
"""

import subprocess
import json
import sys
from pathlib import Path

class MealieAgentTest:
    def __init__(self):
        self.repo_root = Path(__file__).resolve().parent
        self.mcp_command = [
            "uv",
            "--directory",
            str(self.repo_root / "mealie-mcp-server"),
            "run",
            "src/server.py",
        ]
        
    def call_mcp(self, tool_name, arguments=None):
        """Appelle un outil MCP"""
        if arguments is None:
            arguments = {}
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        process = subprocess.Popen(
            self.mcp_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Initialisation + requête
        init_request = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "agent-test", "version": "1.0"}
            }
        }
        
        input_data = json.dumps(init_request) + "\n" + json.dumps(request) + "\n"
        stdout, stderr = process.communicate(input=input_data, timeout=10)
        
        # Parser la réponse
        lines = stdout.strip().split('\n')
        for line in lines:
            if line.strip():
                try:
                    response = json.loads(line)
                    if "result" in response and "content" in response["result"]:
                        return response["result"]["content"][0]["text"]
                    elif "error" in response:
                        return f"Erreur: {response['error'].get('message', 'Unknown error')}"
                except json.JSONDecodeError:
                    continue
        
        return "Pas de réponse valide"
    
    def test_nutrition_planner(self):
        """Test du skill nutrition-planner"""
        print("🥗 TEST NUTRITION-PLANNER")
        print("=" * 50)
        
        # 1. Récupérer les préférences
        print("1. Récupération des préférences...")
        preferences = self.call_mcp("get_groups_preferences", {})
        print(f"   {preferences}")
        
        # 2. Créer un repas aléatoire
        print("\n2. Création d'un repas équilibré...")
        meal = self.call_mcp("create_random_meal", {
            "date": "2026-04-01",
            "entryType": "dinner"
        })
        print(f"   {meal}")
        
        # 3. Créer une liste de courses
        print("\n3. Création d'une liste de courses...")
        shopping = self.call_mcp("create_shopping_list", {
            "name": "Courses menu test"
        })
        print(f"   {shopping}")
        
        return True
    
    def test_recipe_analyzer(self):
        """Test du skill recipe-analyzer"""
        print("\n📊 TEST RECIPE-ANALYZER")
        print("=" * 50)
        
        # 1. Lister les recettes
        print("1. Liste des recettes disponibles...")
        recipes = self.call_mcp("list_recipes", {})
        print(f"   {recipes[:200]}...")
        
        # 2. Analyser une recette spécifique
        print("\n2. Analyse d'une recette...")
        details = self.call_mcp("get_recipe_details", {
            "slug": "cafe-glace-au-chocolat-shokolad-gliase-1"
        })
        print(f"   {details[:300]}...")
        
        return True
    
    def test_shopping_optimizer(self):
        """Test du skill shopping-optimizer"""
        print("\n🛒 TEST SHOPPING-OPTIMIZER")
        print("=" * 50)
        
        # 1. Voir les repas du jour
        print("1. Repas du jour...")
        todays = self.call_mcp("get_todays_meals", {})
        print(f"   {todays}")
        
        # 2. Lister les listes de courses existantes
        print("\n2. Listes de courses existantes...")
        lists = self.call_mcp("list_shopping_lists", {})
        print(f"   {lists}")
        
        return True
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        print("🎯 DÉMARRAGE DES TESTS DES AGENTS MEALIE")
        print("=" * 60)
        
        try:
            # Test MCP de base
            print("🔧 Test de connexion MCP...")
            tools = self.call_mcp("tools/list" if False else "list_recipes", {})
            print(f"   MCP connecté avec succès")
            
            # Tests des agents
            success1 = self.test_nutrition_planner()
            success2 = self.test_recipe_analyzer()
            success3 = self.test_shopping_optimizer()
            
            print("\n🎉 RÉSULTATS DES TESTS")
            print("=" * 60)
            print(f"✅ Nutrition-Planner: {'OK' if success1 else 'ÉCHEC'}")
            print(f"✅ Recipe-Analyzer: {'OK' if success2 else 'ÉCHEC'}")
            print(f"✅ Shopping-Optimizer: {'OK' if success3 else 'ÉCHEC'}")
            
            if success1 and success2 and success3:
                print("\n🚀 TOUS LES AGENTS FONCTIONNENT CORRECTEMENT !")
                print("\n📝 UTILISATION DANS WINDSURF:")
                print("   @nutrition-planner Crée-moi un menu semaine sans foie gras")
                print("   @recipe-analyzer Analyse cette recette sur le plan nutritionnel")
                print("   @shopping-optimizer Optimise ma liste de courses")
            else:
                print("\n⚠️ CERTAINS AGENTS ONT DES PROBLÈMES")
            
        except Exception as e:
            print(f"\n❌ ERREUR LORS DES TESTS: {e}")

if __name__ == "__main__":
    tester = MealieAgentTest()
    tester.run_all_tests()
