"""Factory for creating AI provider instances."""

import os
from typing import Type

from .base import AIProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.cascade_provider import CascadeProvider
from .providers.openai_provider import OpenAIProvider
from .providers.mock_provider import MockProvider


def create_ai_provider() -> AIProvider:
    """Create an AI provider instance based on environment configuration.
    
    The provider is selected using the AI_PROVIDER environment variable.
    Defaults to CascadeProvider for local development.
    
    Returns:
        An instance of the configured AI provider
        
    Raises:
        ValueError: If the configured provider is not available
    """
    provider_type = os.getenv("AI_PROVIDER", "cascade").lower()
    
    providers: dict[str, Type[AIProvider]] = {
        "anthropic": AnthropicProvider,
        "cascade": CascadeProvider,
        "openai": OpenAIProvider,
        "mock": MockProvider,
    }
    
    provider_class = providers.get(provider_type)
    
    if provider_class is None:
        raise ValueError(
            f"Unknown AI provider: {provider_type}. "
            f"Available providers: {', '.join(providers.keys())}"
        )
    
    return provider_class()
