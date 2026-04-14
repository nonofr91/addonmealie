"""OpenAI AI provider implementation."""

import os
from typing import Dict, Any

from ..base import AIProvider


class OpenAIProvider(AIProvider):
    """AI provider using OpenAI API.
    
    This provider uses the OpenAI API for AI-powered operations in production
    deployment via Coolify.
    """
    
    def __init__(self):
        """Initialize the OpenAI provider."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY must be set in environment variables "
                "when using OpenAI provider."
            )
    
    def complete(self, prompt: str, **kwargs) -> str:
        """Complete a text prompt using OpenAI.
        
        Args:
            prompt: The text prompt to complete
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            The completed text
        """
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return response.choices[0].message.content
        except ImportError:
            raise ImportError(
                "OpenAI package not installed. Install it with: pip install openai"
            )
    
    def analyze_ingredient(self, ingredient_text: str) -> Dict[str, Any]:
        """Analyze an ingredient text using OpenAI.
        
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
        """Structure a raw recipe using OpenAI.
        
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
