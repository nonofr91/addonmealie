#!/usr/bin/env python3
"""
Système pour organiser les recettes importées par l'IA dans un cookbook "Import IA"
Utilise l'endpoint /api/households/cookbooks
"""

import os
import sys
import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Optional

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

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

class CookbookImportIA:
    """Système pour gérer le cookbook Import IA"""
    
    def __init__(self):
        self.cookbook_name = "Import IA"
        self.cookbook_slug = "import-ia"
        self.cookbook_id = None
    
    def create_or_get_cookbook(self) -> str:
        """Crée ou récupère le cookbook Import IA"""
        print(f"📚 Création/Récupération du cookbook '{self.cookbook_name}'")
        
        # 1. Vérifier si le cookbook existe déjà
        try:
            response = requests.get(f"{API_URL}/households/cookbooks", headers=headers)
            if response.status_code == 200:
                data = response.json()
                cookbooks = data.get('items', [])
                
                for cookbook in cookbooks:
                    if cookbook.get('name', '').lower() == self.cookbook_name.lower():
                        self.cookbook_id = cookbook.get('id')
                        print(f"   ✅ Cookbook existant trouvé - ID: {self.cookbook_id}")
                        return self.cookbook_id
        
        except Exception as e:
            print(f"   ⚠️ Erreur vérification: {e}")
        
        # 2. Créer le cookbook s'il n'existe pas
        try:
            cookbook_data = {
                "name": self.cookbook_name,
                "slug": self.cookbook_slug,
                "description": "Recettes importées automatiquement par l'IA",
                "public": False,  # Privé
                "categories": []  # Pas de catégories spécifiques
            }
            
            response = requests.post(f"{API_URL}/households/cookbooks", json=cookbook_data, headers=headers)
            
            if response.status_code == 201:
                created_cookbook = response.json()
                self.cookbook_id = created_cookbook.get('id')
                print(f"   ✅ Cookbook créé - ID: {self.cookbook_id}")
                return self.cookbook_id
            else:
                print(f"   ❌ Erreur création: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Exception création: {e}")
            return None
    
    def add_recipe_to_cookbook(self, recipe_id: str) -> bool:
        """Ajoute une recette au cookbook Import IA"""
        if not self.cookbook_id:
            print("❌ Aucun cookbook disponible")
            return False
        
        try:
            # Récupérer les détails du cookbook
            response = requests.get(f"{API_URL}/households/cookbooks/{self.cookbook_id}", headers=headers)
            if response.status_code != 200:
                print(f"   ❌ Erreur récupération cookbook: {response.status_code}")
                return False
            
            cookbook = response.json()
            cookbook_name = cookbook.get('name', '')
            
            # Vérifier si la recette est déjà dans le cookbook
            current_recipes = cookbook.get('recipes', [])
            recipe_ids = [recipe.get('id') for recipe in current_recipes]
            
            if recipe_id in recipe_ids:
                print(f"   ✅ Recette déjà dans le cookbook")
                return True
            
            # Ajouter la recette au cookbook
            if not current_recipes:
                current_recipes = []
            
            # Ajouter l'ID de la recette
            current_recipes.append({"id": recipe_id})
            
            # Mettre à jour le cookbook
            update_data = {
                "recipes": current_recipes
            }
            
            patch_response = requests.put(f"{API_URL}/households/cookbooks/{self.cookbook_id}", json=update_data, headers=headers)
            
            if patch_response.status_code == 200:
                print(f"   ✅ Recette ajoutée au cookbook '{cookbook_name}'")
                return True
            else:
                print(f"   ❌ Erreur ajout au cookbook: {patch_response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    def import_and_add_to_cookbook(self, url: str) -> Optional[str]:
        """Importe une recette et l'ajoute directement au cookbook Import IA"""
        print(f"📥 Import vers cookbook: {url}")
        
        try:
            # 1. Scraper la recette
            scrape_data = {
                "url": url,
                "includeTags": True,
                "includeCategories": True
            }
            
            response = requests.post(
                f"{API_URL}/recipes/create/url",
                json=scrape_data,
                headers=headers,
                timeout=60
            )
            
            if response.status_code != 201:
                print(f"   ❌ Erreur scraping: {response.status_code}")
                return None
            
            slug = response.text.strip('"')
            print(f"   ✅ Recette scrapée: {slug}")
            
            # 2. Récupérer l'ID de la recette
            recipe_response = requests.get(f"{API_URL}/recipes/{slug}", headers=headers)
            if recipe_response.status_code != 200:
                print(f"   ❌ Erreur récupération ID: {recipe_response.status_code}")
                return None
            
            recipe = recipe_response.json()
            recipe_id = recipe.get('id')
            recipe_name = recipe.get('name', '')
            
            if not recipe_id:
                print(f"   ❌ ID de recette non trouvé")
                return None
            
            print(f"   ✅ Recette: {recipe_name} (ID: {recipe_id})")
            
            # 3. Ajouter au cookbook Import IA
            if self.add_recipe_to_cookbook(recipe_id):
                return recipe_id
            else:
                return None
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return None
    
    def batch_import_to_cookbook(self, urls: List[str]) -> Dict:
        """Importe plusieurs recettes vers le cookbook Import IA"""
        print(f"📚 IMPORT BATCH VERS COOKBOOK '{self.cookbook_name}'")
        print("=" * 50)
        
        # S'assurer que le cookbook existe
        self.create_or_get_cookbook()
        
        if not self.cookbook_id:
            print("❌ Impossible de créer/récupérer le cookbook")
            return {"success": 0, "failed": 0, "total": 0}
        
        results = {"success": 0, "failed": 0, "total": len(urls)}
        
        for i, url in enumerate(urls, 1):
            print(f"\n📝 {i}/{len(urls)}")
            
            recipe_id = self.import_and_add_to_cookbook(url)
            if recipe_id:
                results["success"] += 1
            else:
                results["failed"] += 1
            
            time.sleep(2)  # Pause entre les imports
        
        return results
    
    def list_cookbook_recipes(self) -> List[Dict]:
        """Liste toutes les recettes dans le cookbook Import IA"""
        if not self.cookbook_id:
            print("❌ Aucun cookbook disponible")
            return []
        
        print(f"📋 RECETTES DANS LE COOKBOOK '{self.cookbook_name}':")
        
        try:
            # Récupérer les détails du cookbook
            response = requests.get(f"{API_URL}/households/cookbooks/{self.cookbook_id}", headers=headers)
            if response.status_code != 200:
                print("❌ Erreur récupération cookbook")
                return []
            
            cookbook = response.json()
            cookbook_recipes = cookbook.get('recipes', [])
            
            # Afficher les recettes
            for recipe in cookbook_recipes:
                name = recipe.get('name', '')
                recipe_id = recipe.get('id', '')
                slug = recipe.get('slug', '')
                img_status = "🖼️" if recipe.get('image', {}) else "❌"
                
                print(f"   • {name}")
                print(f"      Slug: {slug}")
                print(f"      ID: {recipe_id}")
                print(f"      Image: {img_status}")
                print("")
            
            print(f"📊 Total: {len(cookbook_recipes)} recettes dans le cookbook")
            return cookbook_recipes
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return []
    
    def organize_existing_recipes(self) -> int:
        """Organise les recettes existantes dans le cookbook Import IA"""
        print(f"🗂️ ORGANISATION DES RECETTES EXISTANTES")
        
        # S'assurer que le cookbook existe
        self.create_or_get_cookbook()
        
        if not self.cookbook_id:
            print("❌ Impossible de créer le cookbook")
            return 0
        
        # Récupérer toutes les recettes
        try:
            response = requests.get(f"{API_URL}/recipes?perPage=50", headers=headers)
            if response.status_code != 200:
                print("❌ Erreur récupération recettes")
                return 0
            
            data = response.json()
            recipes = data.get('items', [])
            
            organized_count = 0
            
            for recipe in recipes:
                slug = recipe.get('slug', '')
                name = recipe.get('name', '')
                recipe_id = recipe.get('id', '')
                
                # Vérifier si c'est une recette importée par l'IA
                is_ia_import = (
                    "(1)" in name or 
                    "(2)" in name or
                    "How to Cook" in name or
                    "Lentil recipes" == name or
                    recipe.get('orgURL', '').startswith('https://www.')
                )
                
                if is_ia_import and recipe_id:
                    if self.add_recipe_to_cookbook(recipe_id):
                        organized_count += 1
                        print(f"   ✅ {name} organisée")
            
            print(f"\n🎯 {organized_count} recettes organisées dans le cookbook Import IA")
            return organized_count
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return 0
    
    def show_system_status(self):
        """Affiche le statut complet du système"""
        print(f"📊 STATUT DU SYSTÈME COOKBOOK IMPORT IA")
        print("=" * 50)
        
        # Vérifier le cookbook
        cookbook_created = self.create_or_get_cookbook()
        if cookbook_created:
            print(f"✅ Cookbook '{self.cookbook_name}' disponible (ID: {self.cookbook_id})")
        else:
            print(f"❌ Cookbook '{self.cookbook_name}' indisponible")
            return
        
        # Compter les recettes dans le cookbook
        cookbook_recipes = self.list_cookbook_recipes()
        
        # Compter toutes les recettes
        try:
            response = requests.get(f"{API_URL}/recipes?perPage=50", headers=headers)
            if response.status_code == 200:
                data = response.json()
                all_recipes = data.get('items', [])
                print(f"📋 Total recettes dans Mealie: {len(all_recipes)}")
                print(f"📚 Recettes dans cookbook Import IA: {len(cookbook_recipes)}")
                if len(all_recipes) > 0:
                    print(f"📈 Pourcentage organisé: {len(cookbook_recipes)/len(all_recipes)*100:.1f}%")
        except:
            print("❌ Erreur comptage total")

def main():
    """Fonction principale"""
    print("📚 SYSTÈME COOKBOOK IMPORT IA")
    print("   • Organisation automatique des imports IA")
    print("   • Utilisation des cookbooks Mealie")
    print("   • Interface française")
    print("=" * 60)
    
    system = CookbookImportIA()
    
    # 1. Afficher le statut
    system.show_system_status()
    
    # 2. Organiser les recettes existantes
    print(f"\n🗂️ Organisation des recettes existantes...")
    organized = system.organize_existing_recipes()
    
    # 3. Importer de nouvelles recettes françaises (test)
    french_urls = [
        "https://www.ricardocuisine.com/recettes/4970-lentilles-corail-lait-coco",
        "https://www.ricardocuisine.com/recettes/7620-poulet-riz-curry",
        "https://www.ricardocuisine.com/recettes/6579-boeuf-bourguignon",
        "https://www.ricardocuisine.com/recettes/7485-clafoutis-cerises"
    ]
    
    print(f"\n📥 Import de nouvelles recettes françaises...")
    results = system.batch_import_to_cookbook(french_urls)
    
    print(f"\n📊 RÉSULTATS IMPORT:")
    print(f"✅ Réussies: {results['success']}")
    print(f"❌ Échouées: {results['failed']}")
    print(f"📋 Total: {results['total']}")
    
    # 4. Afficher le contenu final
    print(f"\n📋 CONTENU FINAL DU COOKBOOK:")
    final_recipes = system.list_cookbook_recipes()
    
    print(f"\n🎉 SYSTÈME TERMINÉ!")
    print(f"📚 Cookbook '{system.cookbook_name}' prêt avec {len(final_recipes)} recettes")
    print(f"🤖 Toutes les futures imports IA seront automatiquement organisées ici")
    print(f"📖 Votre livre de recettes 'Import IA' est maintenant opérationnel!")

if __name__ == "__main__":
    main()
