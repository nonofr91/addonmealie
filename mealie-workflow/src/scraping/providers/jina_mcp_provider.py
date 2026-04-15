#!/usr/bin/env python3
"""
Provider de scraping via MCP Jina (Cascade)
Utilise les MCP Jina disponibles via Cascade
"""

import sys
from pathlib import Path
from typing import Optional, List

# Ajouter le chemin du wrapper MCP
sys.path.append(str(Path(__file__).resolve().parents[3]))
from mcp_auth_wrapper import *

# Ajouter le chemin du module scraping
sys.path.insert(0, str(Path(__file__).parent.parent))
from base import ScrapingProvider


class JinaMCPProvider(ScrapingProvider):
    """Provider de scraping via MCP Jina"""
    
    def __init__(self):
        self.name = "Jina MCP (Cascade)"
    
    def extract_url(self, url: str) -> Optional[str]:
        """Extrait le contenu via MCP Jina"""
        try:
            print(f"   🌐 Extraction via MCP Jina (Cascade): {url}")
            result = mcp2_read_url(url)
            
            if result and len(result) > 100:
                print(f"   ✅ Contenu extrait: {len(result)} caractères")
                return result
            else:
                print(f"   ⚠️ Contenu trop court: {len(result) if result else 0} caractères")
                return None
        except Exception as e:
            print(f"   ❌ Erreur MCP Jina: {e}")
            return None
    
    def search_images(self, query: str, num: int = 3) -> List[str]:
        """Recherche des images via MCP Jina"""
        try:
            print(f"   🖼️ Recherche images: {query}")
            images = mcp2_search_images(query, return_url=True, num=num)
            return images if images else []
        except Exception as e:
            print(f"   ❌ Erreur recherche images: {e}")
            return []
    
    def get_provider_name(self) -> str:
        return self.name
    
    def is_available(self) -> bool:
        """Vérifie si les MCP Jina sont disponibles"""
        try:
            # Test simple : essayer de lire une URL
            test_result = mcp2_read_url("https://example.com")
            return test_result is not None
        except Exception:
            return False
