"""Mock AI provider for testing purposes."""

from typing import Dict, Any

from ..base import AIProvider


class MockProvider(AIProvider):
    """Mock AI provider for testing purposes.
    
    This provider returns predefined mock responses without calling any
    external AI service, making it ideal for unit tests and CI/CD pipelines.
    """
    
    def complete(self, prompt: str, **kwargs) -> str:
        """Return a mock completion response.
        
        Args:
            prompt: The text prompt to complete (ignored)
            **kwargs: Additional parameters (ignored)
            
        Returns:
            A mock completion response
        """
        return "Mock response for testing"
    
    def analyze_ingredient(self, ingredient_text: str) -> Dict[str, Any]:
        """Return a mock ingredient analysis.
        
        Args:
            ingredient_text: The ingredient text to analyze (ignored)
            
        Returns:
            A mock ingredient structure
        """
        return {
            "quantity": 1.0,
            "unit": "cup",
            "food": "flour",
            "note": ingredient_text,
            "display": ingredient_text,
        }
    
    def structure_recipe(self, raw_recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Return a mock structured recipe.
        
        Args:
            raw_recipe: Raw recipe data (ignored)
            
        Returns:
            A mock structured recipe
        """
        return {
            "name": "Mock Recipe",
            "description": "Mock recipe for testing",
            "recipeIngredient": [
                {"note": "1 cup flour", "display": "1 cup flour"},
                {"note": "2 eggs", "display": "2 eggs"},
            ],
            "recipeInstructions": [
                {"text": "Mix ingredients", "id": "1"},
                {"text": "Bake at 350°F", "id": "2"},
            ],
        }
