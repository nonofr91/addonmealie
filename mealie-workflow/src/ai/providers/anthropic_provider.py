"""Anthropic AI provider implementation."""

import os
from typing import Dict, Any

from ..base import AIProvider


class AnthropicProvider(AIProvider):
    """AI provider using Anthropic API (Claude).
    
    This provider uses the Anthropic API for AI-powered operations in production
    deployment via Coolify.
    """
    
    def __init__(self):
        """Initialize the Anthropic provider."""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus")
        
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY must be set in environment variables "
                "when using Anthropic provider."
            )
    
    def complete(self, prompt: str, **kwargs) -> str:
        """Complete a text prompt using Anthropic.
        
        Args:
            prompt: The text prompt to complete
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            The completed text
        """
        try:
            from anthropic import Anthropic
            
            client = Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 1024),
                temperature=kwargs.get("temperature", 0.7),
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except ImportError:
            raise ImportError(
                "Anthropic package not installed. Install it with: pip install anthropic"
            )
    
    def analyze_ingredient(self, ingredient_text: str) -> Dict[str, Any]:
        """Analyze an ingredient text using Anthropic.
        
        Args:
            ingredient_text: The ingredient text to analyze
            
        Returns:
            A dictionary with structured ingredient data
        """
        prompt = f"""Analyze this ingredient and extract structured data:
"{ingredient_text}"

Return JSON with:
- quantity: number
- unit: unit name (cup, tbsp, tsp, etc.)
- food: food name
- display: original text

Only return valid JSON, no other text."""
        
        response = self.complete(prompt, temperature=0.3)
        
        try:
            import json
            data = json.loads(response)
            return {
                "quantity": float(data.get("quantity", 1)),
                "unit": data.get("unit", "unit"),
                "food": data.get("food", ingredient_text.strip()),
                "note": ingredient_text,
                "display": ingredient_text,
            }
        except (json.JSONDecodeError, ValueError):
            # Fallback if JSON parsing fails
            return {
                "quantity": 1.0,
                "unit": "unit",
                "food": ingredient_text.strip(),
                "note": ingredient_text,
                "display": ingredient_text,
            }
    
    def structure_recipe(self, raw_recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Structure a raw recipe using Anthropic.
        
        Args:
            raw_recipe: Raw recipe data from scraping or other sources
            
        Returns:
            A dictionary with structured recipe data
        """
        prompt = f"""Structure this recipe data into a standardized format:
{raw_recipe}

Return JSON with:
- name: recipe name
- description: recipe description
- recipeIngredient: array of ingredient objects with note and display
- recipeInstructions: array of instruction objects with text and id

Only return valid JSON, no other text."""
        
        response = self.complete(prompt, temperature=0.3)
        
        try:
            import json
            data = json.loads(response)
            return {
                "name": data.get("name", raw_recipe.get("name", "Untitled Recipe")),
                "description": data.get("description", ""),
                "recipeIngredient": data.get("recipeIngredient", []),
                "recipeInstructions": data.get("recipeInstructions", []),
            }
        except (json.JSONDecodeError, ValueError):
            # Fallback if JSON parsing fails
            return {
                "name": raw_recipe.get("name", "Untitled Recipe"),
                "description": raw_recipe.get("description", ""),
                "recipeIngredient": raw_recipe.get("recipeIngredient", []),
                "recipeInstructions": raw_recipe.get("recipeInstructions", []),
            }
