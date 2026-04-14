"""Base interface for AI providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class AIProvider(ABC):
    """Abstract base class for AI providers.
    
    This interface defines the contract that all AI providers must implement,
    allowing the application to switch between different providers (Cascade,
    OpenAI, Anthropic, etc.) without modifying the business logic.
    """
    
    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> str:
        """Complete a text prompt.
        
        Args:
            prompt: The text prompt to complete
            **kwargs: Additional provider-specific parameters
            
        Returns:
            The completed text
        """
        pass
    
    @abstractmethod
    def analyze_ingredient(self, ingredient_text: str) -> Dict[str, Any]:
        """Analyze an ingredient text string.
        
        Args:
            ingredient_text: The ingredient text to analyze
            
        Returns:
            A dictionary with structured ingredient data (quantity, unit, food, etc.)
        """
        pass
    
    @abstractmethod
    def structure_recipe(self, raw_recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Structure a raw recipe into a standardized format.
        
        Args:
            raw_recipe: Raw recipe data from scraping or other sources
            
        Returns:
            A dictionary with structured recipe data (ingredients, instructions, etc.)
        """
        pass
