"""AI Recipe Analyzer using AI Provider abstraction."""

import json
import re
from typing import Dict, List, Any, Optional

from .factory import create_ai_provider
from .base import AIProvider


class AIRecipeAnalyzer:
    """Recipe analyzer using AI Provider abstraction.
    
    This class provides intelligent recipe analysis and structuring
    using the configured AI provider (Cascade, OpenAI, Anthropic, Mock).
    """
    
    def __init__(self):
        """Initialize the AI Recipe Analyzer with the configured provider."""
        self.ai_provider = create_ai_provider()
    
    def analyze_ingredient(self, ingredient_text: str) -> Dict[str, Any]:
        """Analyze an ingredient text using AI.
        
        Args:
            ingredient_text: The ingredient text to analyze
            
        Returns:
            A dictionary with structured ingredient data
        """
        try:
            return self.ai_provider.analyze_ingredient(ingredient_text)
        except Exception as e:
            print(f"   ⚠️ Erreur analyse ingrédient: {e}")
            # Fallback to basic parsing
            return self._parse_ingredient_fallback(ingredient_text)
    
    def structure_recipe(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure a raw recipe using AI.
        
        Args:
            raw_data: Raw recipe data from scraping or other sources
            
        Returns:
            A dictionary with structured recipe data
        """
        try:
            return self.ai_provider.structure_recipe(raw_data)
        except Exception as e:
            print(f"   ⚠️ Erreur structuration recette: {e}")
            # Fallback to basic structuring
            return self._structure_recipe_fallback(raw_data)
    
    def analyze_and_parse(self, content: str, url: str) -> Optional[Dict[str, Any]]:
        """Analyze and parse recipe content using AI.
        
        Args:
            content: The recipe content to analyze
            url: The source URL
            
        Returns:
            A dictionary with parsed recipe data
        """
        try:
            # Use AI to structure the recipe
            raw_data = {
                "name": self._extract_name(content),
                "description": self._extract_description(content),
                "content": content,
                "source_url": url
            }
            
            structured = self.structure_recipe(raw_data)
            
            # Analyze ingredients if present
            if "recipeIngredient" in structured:
                structured["recipeIngredient"] = [
                    self.analyze_ingredient(ing) if isinstance(ing, str) else ing
                    for ing in structured["recipeIngredient"]
                ]
            
            return structured
            
        except Exception as e:
            print(f"   ❌ Erreur analyse et parsing: {e}")
            return None
    
    def _parse_ingredient_fallback(self, ingredient_text: str) -> Dict[str, Any]:
        """Fallback basic ingredient parsing."""
        # Try to extract quantity and unit using regex
        pattern = r'^(\d+(?:[\.,]\d+)?)\s*([a-zA-Z]+)?\s+(.+)$'
        match = re.match(pattern, ingredient_text.strip())
        
        if match:
            quantity = match.group(1).replace(',', '.')
            unit = match.group(2) or "unit"
            food = match.group(3)
        else:
            quantity = "1"
            unit = "unit"
            food = ingredient_text.strip()
        
        return {
            "quantity": float(quantity),
            "unit": unit,
            "food": food,
            "note": ingredient_text,
            "display": ingredient_text,
        }
    
    def _structure_recipe_fallback(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback basic recipe structuring."""
        return {
            "name": raw_data.get("name", "Untitled Recipe"),
            "description": raw_data.get("description", ""),
            "recipeIngredient": raw_data.get("recipeIngredient", []),
            "recipeInstructions": raw_data.get("recipeInstructions", []),
        }
    
    def _extract_name(self, content: str) -> str:
        """Extract recipe name from content."""
        # Look for h1, h2, or title patterns
        patterns = [
            r'<h1[^>]*>([^<]+)</h1>',
            r'<h2[^>]*>([^<]+)</h2>',
            r'<title[^>]*>([^<]+)</title>',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback to first line
        lines = content.split('\n')
        for line in lines[:5]:
            if line.strip():
                return line.strip()[:100]
        
        return "Untitled Recipe"
    
    def _extract_description(self, content: str) -> str:
        """Extract recipe description from content."""
        # Look for description or summary patterns
        patterns = [
            r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
            r'<p[^>]*>([^<]{50,200})</p>',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
