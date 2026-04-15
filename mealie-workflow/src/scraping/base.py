#!/usr/bin/env python3
"""
Interface abstraite pour les providers de scraping
Pattern Strategy pour permettre différents providers de scraping
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union


class ScrapingProvider(ABC):
    """Interface abstraite pour les providers de scraping"""
    
    @abstractmethod
    def extract_url(self, url: str) -> Optional[Union[str, Dict[str, Any]]]:
        """
        Extrait le contenu d'une URL
        
        Args:
            url: URL à scraper
        
        Returns:
            Contenu extrait (str ou dict structuré) ou None en cas d'échec
        """
        pass
    
    @abstractmethod
    def search_images(self, query: str, num: int = 3) -> list[str]:
        """
        Recherche des images
        
        Args:
            query: Requête de recherche
            num: Nombre d'images à retourner
        
        Returns:
            Liste d'URLs d'images
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Retourne le nom du provider"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Vérifie si le provider est disponible"""
        pass
