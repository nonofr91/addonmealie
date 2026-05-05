#!/usr/bin/env python3
"""Module Ingredient Manager pour Mealie - Gestion intelligente des ingrédients avec IA"""

import os
import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class IngredientValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]


@dataclass
class IngredientStructureResult:
    food: str
    unit: Optional[str]
    quantity: float
    note: str
    confidence: float


class IngredientManager:
    def __init__(self, ai_provider: str = "mistral"):
        self.ai_provider = ai_provider
        self.ai_client = None
        self._init_ai_client()
    
    def _init_ai_client(self):
        try:
            if self.ai_provider == "mistral":
                from mistralai import Mistral
                api_key = os.getenv("MISTRAL_API_KEY")
                if api_key:
                    self.ai_client = Mistral(api_key=api_key)
        except Exception as e:
            print(f"⚠️ Erreur initialisation IA: {e}")
    
    def validate_ingredients_structure(self, ingredients: List[Dict]) -> List[IngredientValidationResult]:
        results = []
        for i, ingredient in enumerate(ingredients):
            errors = []
            warnings = []
            
            if not isinstance(ingredient, dict):
                errors.append(f"Ingrédient {i}: n'est pas un dict")
                results.append(IngredientValidationResult(False, errors, warnings))
                continue
            
            if 'food' not in ingredient or not ingredient['food']:
                errors.append(f"Ingrédient {i}: champ 'food' manquant")
            
            if 'food' in ingredient and self._is_uuid(ingredient['food']):
                errors.append(f"Ingrédient {i}: 'food' est un UUID")
            
            if 'unit' in ingredient and self._is_uuid(ingredient['unit']):
                errors.append(f"Ingrédient {i}: 'unit' est un UUID")
            
            results.append(IngredientValidationResult(len(errors) == 0, errors, warnings))
        return results
    
    def intelligent_ingredient_structurer(self, ingredient_text: str) -> IngredientStructureResult:
        if not self.ai_client:
            return self._basic_parsing(ingredient_text)
        
        try:
            prompt = f'Analyse: "{ingredient_text}". JSON: {{"food","unit","quantity","note","confidence"}}'
            response = self.ai_client.chat.complete(
                model="mistral-small-latest",
                messages=[{"role": "user", "content": prompt}]
            )
            import json
            result = json.loads(response.choices[0].message.content)
            return IngredientStructureResult(
                food=result.get('food', ingredient_text),
                unit=result.get('unit'),
                quantity=float(result.get('quantity', 0)),
                note=result.get('note', ''),
                confidence=float(result.get('confidence', 0.5))
            )
        except Exception as e:
            print(f"⚠️ Erreur IA: {e}")
            return self._basic_parsing(ingredient_text)
    
    def _basic_parsing(self, text: str) -> IngredientStructureResult:
        qty_match = re.search(r'^(\d+(?:[.,]\d+)?)\s*', text)
        quantity = float(qty_match.group(1).replace(',', '.')) if qty_match else 0.0
        unit_match = re.search(r'\d+\s*([a-zA-Z°]+)\s+', text)
        unit = unit_match.group(1) if unit_match else None
        food = text
        if qty_match:
            food = food[qty_match.end():]
        if unit_match:
            food = food[unit_match.end():]
        food = re.sub(r"^(de|du|des|d'|la|le|les)\s+", '', food, flags=re.IGNORECASE).strip()
        return IngredientStructureResult(food, unit, quantity, '', 0.3)
    
    def correct_existing_foods(self, foods: List[Dict]) -> List[Dict]:
        corrected = []
        for food in foods:
            name = food.get('name', '')
            corrected_name = re.sub(r"^(de|du|des|d'|la|le|les)\s+", '', name, flags=re.IGNORECASE)
            corrected_name = re.sub(r"\d+\s*(g|kg|ml|l|cl)\b", '', corrected_name, flags=re.IGNORECASE)
            corrected_name = re.sub(r'\s+', ' ', corrected_name).strip()
            if corrected_name != name:
                food['name'] = corrected_name
                print(f"   ✅ Food corrigé: '{name}' → '{corrected_name}'")
            corrected.append(food)
        return corrected
    
    def _is_uuid(self, value: str) -> bool:
        if not value or not isinstance(value, str):
            return False
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(uuid_pattern, value.lower()))
