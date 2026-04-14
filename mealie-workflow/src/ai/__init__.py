"""AI Provider Abstraction Layer for mealie-workflow.

This module provides a flexible abstraction layer for different AI providers,
allowing the project to switch between Cascade (for local development) and
external AI providers (OpenAI, Anthropic, etc.) for production deployment.
"""

from .base import AIProvider
from .factory import create_ai_provider

__all__ = ["AIProvider", "create_ai_provider"]
