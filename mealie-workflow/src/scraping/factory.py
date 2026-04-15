#!/usr/bin/env python3
"""
Factory pour les providers de scraping
Pattern Factory pour créer le provider approprié
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Ajouter le chemin du module scraping
sys.path.insert(0, str(Path(__file__).parent))

from base import ScrapingProvider
from providers.jina_mcp_provider import JinaMCPProvider
from providers.requests_provider import RequestsProvider


def create_scraping_provider() -> ScrapingProvider:
    """
    Crée le provider de scraping approprié
    
    Priorité :
    1. RequestsProvider par défaut (local, ne dépend pas de Cascade)
    2. JinaMCPProvider si SCRAPING_USE_JINA_MCP=true
    
    Returns:
        Instance du provider de scraping
    """
    import os
    
    # Vérifier si on force l'utilisation de Jina MCP
    use_jina_mcp = os.getenv('SCRAPING_USE_JINA_MCP', 'false').lower() == 'true'
    
    if use_jina_mcp:
        jina_provider = JinaMCPProvider()
        if jina_provider.is_available():
            print("✅ Provider Jina MCP (Cascade) disponible")
            return jina_provider
        else:
            print("⚠️ Provider Jina MCP demandé mais non disponible, fallback vers RequestsProvider")
    
    # Utiliser RequestsProvider par défaut
    print("✅ Provider Requests (Local) par défaut")
    requests_provider = RequestsProvider()
    if requests_provider.is_available():
        return requests_provider
    
    # Aucun provider disponible
    raise RuntimeError("Aucun provider de scraping disponible")


def create_scraping_provider_forced(provider_name: str) -> ScrapingProvider:
    """
    Force l'utilisation d'un provider spécifique
    
    Args:
        provider_name: Nom du provider ('jina_mcp' ou 'requests')
    
    Returns:
        Instance du provider demandé
    
    Raises:
        ValueError: Si le provider n'existe pas
    """
    providers = {
        'jina_mcp': JinaMCPProvider,
        'requests': RequestsProvider
    }
    
    if provider_name not in providers:
        raise ValueError(f"Provider inconnu: {provider_name}. Options: {list(providers.keys())}")
    
    provider_class = providers[provider_name]
    provider = provider_class()
    
    if not provider.is_available():
        raise RuntimeError(f"Provider {provider_name} n'est pas disponible")
    
    return provider
