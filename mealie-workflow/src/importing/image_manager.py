#!/usr/bin/env python3
"""Module Image Manager pour Mealie - Gestion intelligente des images avec IA"""

import os
import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ImageAnalysisResult:
    is_appropriate: bool
    confidence: float
    issues: List[str]
    suggested_replacement: Optional[str] = None


class ImageManager:
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
    
    def analyze_recipe_images(self, recipe_name: str, image_url: str) -> ImageAnalysisResult:
        """Analyse si une image est appropriée pour une recette"""
        if not image_url:
            return ImageAnalysisResult(False, 0.0, ["Pas d'image"])
        
        if not self.ai_client:
            return self._basic_analysis(recipe_name, image_url)
        
        try:
            prompt = f"""Recette: "{recipe_name}"
Image: {image_url}

L'image est-elle appropriée pour cette recette? Réponds en JSON:
{{"is_appropriate": true/false, "confidence": 0.0-1.0, "issues": [], "suggested_replacement": "url or null"}}"""
            
            response = self.ai_client.chat.complete(
                model="mistral-small-latest",
                messages=[{"role": "user", "content": prompt}]
            )
            import json
            result = json.loads(response.choices[0].message.content)
            return ImageAnalysisResult(
                is_appropriate=result.get('is_appropriate', True),
                confidence=float(result.get('confidence', 0.5)),
                issues=result.get('issues', []),
                suggested_replacement=result.get('suggested_replacement')
            )
        except Exception as e:
            print(f"⚠️ Erreur IA: {e}")
            return self._basic_analysis(recipe_name, image_url)
    
    def _basic_analysis(self, recipe_name: str, image_url: str) -> ImageAnalysisResult:
        """Analyse basique sans IA"""
        issues = []
        
        # Vérifier si l'URL contient des mots-clés génériques
        generic_keywords = ['placeholder', 'default', 'generic', 'no-image']
        if any(kw in image_url.lower() for kw in generic_keywords):
            issues.append("Image générique détectée")
        
        # Vérifier si le nom de la recette est dans l'URL
        recipe_keywords = recipe_name.lower().split()
        if not any(kw in image_url.lower() for kw in recipe_keywords[:3]):
            issues.append("Image ne semble pas liée à la recette")
        
        return ImageAnalysisResult(
            is_appropriate=len(issues) == 0,
            confidence=0.4,
            issues=issues
        )
    
    def search_and_replace_recipe_image(self, recipe_name: str, current_image_url: str) -> Optional[str]:
        """Recherche une meilleure image pour une recette"""
        analysis = self.analyze_recipe_images(recipe_name, current_image_url)
        
        if analysis.is_appropriate:
            return current_image_url
        
        if analysis.suggested_replacement:
            return analysis.suggested_replacement
        
        # Fallback: retourner l'URL originale si pas de meilleure option
        return current_image_url
