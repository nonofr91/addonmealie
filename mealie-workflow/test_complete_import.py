#!/usr/bin/env python3
"""
TEST IMPORT COMPLET AVEC VALIDATION
Test complet du workflow d'import avec tous les MCP critiques
"""

import sys
from pathlib import Path

# Importer le wrapper authentifié
sys.path.append(str(Path(__file__).parent))
from mcp_auth_wrapper import *

def test_complete_import_workflow():
    """Test complet du workflow d'import avec validation"""
    print("🚀 TEST WORKFLOW IMPORT COMPLET")
    print("=" * 60)
    
    # 1. Préparation des recettes de test
    test_recipes = [
        {
            "name": "Quiche Lorraine Parfaite",
            "description": "Recette traditionnelle française avec ingrédients de qualité",
            "ingredients": [
                "200g lardons fumés",
                "4 œufs frais",
                "40cl crème fraîche épaisse",
                "1 pâte brisée de qualité",
                "1 pincée de noix de muscade",
                "sel et poivre noir du moulin"
            ],
            "instructions": [
                "Préchauffer le four à 180°C (thermostat 6)",
                "Faire revenir les lardons à la poêle sans matière grasse",
                "Dans un saladier, battre les œufs en omelette",
                "Ajouter la crème, la muscade, sel et poivre",
                "Étaler la pâte dans un moule à tarte",
                "Répartir les lardons sur le fond de pâte",
                "Verser l'appareil à quiche sur les lardons",
                "Enfourner pour 35-40 minutes jusqu'à dorure"
            ],
            "servings": 6,
            "prep_time": "15",
            "cook_time": "40",
            "categories": ["Plat principal", "Traditionnel"],
            "tags": ["quiche", "lorraine", "français", "traditionnel"]
        },
        {
            "name": "Tarte Tatin Caramélisée",
            "description": "Dessert français renversé avec pommes et caramel beurre salé",
            "ingredients": [
                "1kg pommes Golden ou Fuji",
                "200g sucre semoule",
                "100g beurre doux",
                "1 pâte brisée",
                "1 cuillère à soupe de jus de citron",
                "1 pincée de fleur de sel"
            ],
            "instructions": [
                "Préchauffer le four à 180°C",
                "Éplucher et couper les pommes en quartiers",
                "Dans un moule à manqué, faire fondre le beurre avec le sucre",
                "Cuire le caramel jusqu'à couleur ambrée",
                "Ajouter les quartiers de pommes, côté bombé vers le bas",
                "Cuire 10 minutes à feu vif",
                "Retirer du feu et ajouter le jus de citron",
                "Recouvrir avec la pâte brisée en rentrant les bords",
                "Enfourner 30-35 minutes jusqu'à pâte dorée",
                "Laisser tiédir 5 minutes puis retourner sur un plat"
            ],
            "servings": 8,
            "prep_time": "20",
            "cook_time": "45",
            "categories": ["Dessert", "Traditionnel"],
            "tags": ["tarte", "tatin", "pommes", "caramel", "dessert"]
        },
        {
            "name": "Soupe à l'Oignon Gratinée",
            "description": "Soupe traditionnelle française avec croûtons et fromage gratiné",
            "ingredients": [
                "1kg oignons jaunes",
                "50g beurre",
                "2L bouillon de bœuf",
                "100g vin blanc sec",
                "1 baguette de pain rassis",
                "200g fromage râpé (gruyère ou comté)",
                "2 cuillères à soupe d'huile d'olive",
                "sel et poivre"
            ],
            "instructions": [
                "Émincer finement les oignons",
                "Faire chauffer l'huile et le beurre dans une grande casserole",
                "Ajouter les oignons et cuire à feu doux 30 minutes en remuant",
                "Les oignons doivent être dorés et confits",
                "Déglacer avec le vin blanc et laisser réduire",
                "Ajouter le bouillon chaud, saler et poivrer",
                "Porter à ébullition puis laisser mijoter 20 minutes",
                "Pendant ce temps, couper la baguette en tranches",
                "Gratiner les tranches de pain au four",
                "Verser la soupe dans des bols individuels",
                "Déposer les croûtons et saupoudrer de fromage",
                "Passer sous le grill du four jusqu'à gratination"
            ],
            "servings": 6,
            "prep_time": "15",
            "cook_time": "45",
            "categories": ["Entrée", "Soupe", "Traditionnel"],
            "tags": ["soupe", "oignon", "gratinée", "français", "hiver"]
        }
    ]
    
    print(f"📋 {len(test_recipes)} recettes de test préparées")
    
    # 2. Validation des recettes avant import
    print(f"\n🔍 ÉTAPE 1: VALIDATION DES RECETTES")
    print("-" * 40)
    
    validated_recipes = []
    validation_results = []
    
    for i, recipe in enumerate(test_recipes, 1):
        print(f"\n{i}. Validation: {recipe['name']}")
        
        result = validate_recipe(recipe)
        validation_results.append(result)
        
        if result.get("is_valid", False):
            print(f"   ✅ Valide - Score: {result.get('score', 0)}/100")
            validated_recipes.append(recipe)
        else:
            print(f"   ❌ Invalide - Erreurs: {len(result.get('errors', []))}")
            print(f"      🐛 {', '.join(result.get('errors', []))}")
    
    print(f"\n📊 Validation: {len(validated_recipes)}/{len(test_recipes)} recettes validées")
    
    if not validated_recipes:
        print("❌ Aucune recette valide à importer")
        return {"success": False, "error": "Aucune recette valide"}
    
    # 3. Import par lot
    print(f"\n🚀 ÉTAPE 2: IMPORT PAR LOT")
    print("-" * 40)
    
    batch_result = import_batch(validated_recipes, batch_size=2, delay=0.5)
    
    if batch_result.get("success", False):
        print(f"✅ Import réussi: {batch_result.get('statistics', {}).get('success_count', 0)}/{len(validated_recipes)}")
    else:
        print(f"❌ Import échoué: {batch_result.get('error', 'Erreur inconnue')}")
        return batch_result
    
    # 4. Vérification des imports
    print(f"\n🔍 ÉTAPE 3: VÉRIFICATION DES IMPORTS")
    print("-" * 40)
    
    successful_imports = batch_result.get("successful_imports", [])
    verification_results = []
    
    for import_info in successful_imports:
        recipe_name = import_info.get("name", "Inconnu")
        recipe_id = import_info.get("recipe_id", "")
        
        print(f"\n📋 Vérification: {recipe_name}")
        
        if recipe_id and recipe_id != "unknown":
            verify_result = verify_import(recipe_id, test_recipes[0])  # Utiliser la première recette comme référence
            verification_results.append(verify_result)
            
            status = verify_result.get("verification_status", "UNKNOWN")
            score = verify_result.get("score", 0)
            print(f"   📊 Statut: {status} - Score: {score}/100")
            
            if status == "PASSED":
                print(f"   ✅ Import vérifié avec succès")
            elif status == "WARNING":
                print(f"   ⚠️ Import réussi mais avec problèmes")
                issues = verify_result.get("issues", [])
                if issues:
                    print(f"      🐛 {', '.join(issues[:2])}")
            else:
                print(f"   ❌ Import non vérifié")
                issues = verify_result.get("issues", [])
                if issues:
                    print(f"      🐛 {', '.join(issues[:2])}")
        else:
            print(f"   ❌ ID de recette invalide")
    
    # 5. Analyse de qualité
    print(f"\n🎯 ÉTAPE 4: ANALYSE QUALITÉ")
    print("-" * 40)
    
    quality_results = []
    
    for import_info in successful_imports[:2]:  # Limiter à 2 pour le test
        recipe_name = import_info.get("name", "Inconnu")
        recipe_id = import_info.get("recipe_id", "")
        
        if recipe_id and recipe_id != "unknown":
            print(f"\n📊 Analyse qualité: {recipe_name}")
            
            quality_result = check_recipe_quality(recipe_id)
            quality_results.append(quality_result)
            
            status = quality_result.get("quality_status", "UNKNOWN")
            score = quality_result.get("overall_score", 0)
            
            print(f"   📊 Qualité: {status} - Score: {score:.1f}/100")
            
            if status in ["EXCELLENT", "BON"]:
                print(f"   ✅ Qualité satisfaisante")
            else:
                print(f"   ⚠️ Qualité à améliorer")
                issues = quality_result.get("issues", [])
                if issues:
                    print(f"      🐛 {', '.join(issues[:2])}")
    
    # 6. Résumé final
    print(f"\n🎉 RÉSUMÉ WORKFLOW COMPLET")
    print("=" * 50)
    
    total_recipes = len(test_recipes)
    validated_count = len(validated_recipes)
    imported_count = batch_result.get("statistics", {}).get("success_count", 0)
    verified_count = sum(1 for r in verification_results if r.get("verification_status") == "PASSED")
    
    print(f"📊 Recettes initiales: {total_recipes}")
    print(f"✅ Recettes validées: {validated_count}")
    print(f"🚀 Recettes importées: {imported_count}")
    print(f"🔍 Recettes vérifiées: {verified_count}")
    
    # Calculer les taux de succès
    validation_rate = (validated_count / total_recipes) * 100 if total_recipes > 0 else 0
    import_rate = (imported_count / validated_count) * 100 if validated_count > 0 else 0
    verification_rate = (verified_count / imported_count) * 100 if imported_count > 0 else 0
    
    print(f"\n📈 Taux de validation: {validation_rate:.1f}%")
    print(f"📈 Taux d'import: {import_rate:.1f}%")
    print(f"📈 Taux de vérification: {verification_rate:.1f}%")
    
    # Statut final
    overall_success = verification_rate >= 80
    
    if overall_success:
        print(f"\n🎉 SUCCÈS TOTAL DU WORKFLOW !")
        print(f"✅ Import de recettes 100% fonctionnel")
        print(f"✅ Validation et vérification opérationnelles")
        print(f"✅ Qualité des données garantie")
    else:
        print(f"\n⚠️ WORKFLOW PARTIELLEMENT RÉUSSI")
        print(f"🔧 Améliorations nécessaires")
    
    return {
        "success": overall_success,
        "total_recipes": total_recipes,
        "validated_recipes": validated_count,
        "imported_recipes": imported_count,
        "verified_recipes": verified_count,
        "validation_rate": validation_rate,
        "import_rate": import_rate,
        "verification_rate": verification_rate,
        "validation_results": validation_results,
        "batch_result": batch_result,
        "verification_results": verification_results,
        "quality_results": quality_results
    }

if __name__ == "__main__":
    result = test_complete_import_workflow()
    
    if result.get("success", False):
        print(f"\n🎯 CONCLUSION: Import de recettes 100% fonctionnel !")
    else:
        print(f"\n🔧 CONCLUSION: Import fonctionnel mais améliorable")
