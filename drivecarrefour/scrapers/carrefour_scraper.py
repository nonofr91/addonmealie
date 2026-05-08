"""
Carrefour Web Scraper Module
Recupere les produits, prix, poids et disponibilite depuis carrefour.fr
"""

import re
from typing import List, Dict, Optional, AsyncGenerator
from pathlib import Path

import httpx
from selectolax.parser import HTMLParser
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential
from diskcache import Cache


class CarrefourScraper:
    """
    Scraper pour le site Carrefour.fr.
    Permet de rechercher des produits et d'extraire leurs informations (prix, poids, etc.).
    """
    
    BASE_URL = "https://www.carrefour.fr"
    SEARCH_ENDPOINT = "/s?q={query}"
    
    # Cache directory
    CACHE_DIR = Path.home() / ".cache" / "drivecarrefour"
    
    def __init__(self, cache_enabled: bool = True, cache_expire: int = 24 * 3600):
        """
        Initialise le scraper.
        
        Args:
            cache_enabled: Active/désactive le cache
            cache_expire: Durée de validité du cache en secondes (default: 24h)
        """
        self.ua = UserAgent()
        self.headers = {
            "User-Agent": self.ua.random,
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.com/",
        }
        self.timeout = 30.0
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=self.timeout,
            follow_redirects=True
        )
        
        # Configure cache
        self.cache_enabled = cache_enabled
        if cache_enabled:
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            self.cache = Cache(str(self.CACHE_DIR))
            self.cache.set_expire_time(cache_expire)
        else:
            self.cache = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def _fetch(self, url: str) -> str:
        """
        Récupère le contenu HTML d'une URL avec gestion des erreurs.
        
        Args:
            url: URL à récupérer
            
        Returns:
            Contenu HTML de la page
        """
        if self.cache_enabled and self.cache and url in self.cache:
            return self.cache[url]
            
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            html = response.text
            
            if self.cache_enabled and self.cache:
                self.cache[url] = html
                
            return html
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Page non trouvée: {url}")
            elif e.response.status_code == 403:
                raise PermissionError(f"Accès refusé (403). Vérifie les headers/User-Agent: {url}")
            else:
                raise

    def _parse_price(self, price_str: str) -> Optional[float]:
        """
        Convertit une chaîne de prix en float.
        Exemples: "2,99 €" -> 2.99, "5€" -> 5.0, "1,5" -> 1.5
        
        Args:
            price_str: Chaîne contenant le prix
            
        Returns:
            Prix en float ou None si non parsable
        """
        if not price_str:
            return None
        
        # Normalisation
        price_str = price_str.replace(",", ".").replace("€", "").strip()
        
        # Extraction du nombre
        match = re.search(r"(\d+\.\d+|\d+)", price_str)
        if match:
            return float(match.group(1))
        return None

    def _parse_weight(self, weight_str: str) -> Optional[float]:
        """
        Convertit une chaîne de poids en kilogrammes (float).
        Exemples: "500 g" -> 0.5, "1 kg" -> 1.0, "250 ml" -> 0.25
        
        Args:
            weight_str: Chaîne contenant le poids
            
        Returns:
            Poids en kg (ou L pour les liquides) ou None
        """
        if not weight_str:
            return None
        
        weight_str = weight_str.lower().replace(" ", "")
        
        # Extraction de la valeur numérique
        match = re.search(r"(\d+\.\d+|\d+)", weight_str)
        if not match:
            return None
        
        value = float(match.group(1))
        
        # Conversion selon l'unité
        if any(unit in weight_str for unit in ["kg", "kilogramme"]):
            return value
        elif any(unit in weight_str for unit in ["g", "gramme"]):
            return value / 1000
        elif any(unit in weight_str for unit in ["l", "litre"]):
            return value
        elif any(unit in weight_str for unit in ["ml", "millilitre"]):
            return value / 1000
        elif any(unit in weight_str for unit in ["cl", "centilitre"]):
            return value / 100
        
        return None

    def _parse_quantity(self, text: str) -> Optional[int]:
        """
        Extrait la quantité d'un conditionnement.
        Exemples: "6 œufs" -> 6, "Barquette de 12" -> 12
        
        Args:
            text: Texte contenant la quantité
            
        Returns:
            Quantité en int ou None
        """
        if not text:
            return None
        
        # Recherche de nombres dans le texte
        matches = re.findall(r"\d+", text)
        if matches:
            return int(matches[0])
        return None

    def _extract_product_from_node(self, node) -> Optional[Dict]:
        """
        Extrait les informations d'un produit depuis un node HTML.
        
        Args:
            node: Node selectolax représentant un produit
            
        Returns:
            Dictionnaire avec les infos du produit ou None
        """
        try:
            # Nom du produit
            name_node = node.css_first("h3.product-title, h2.product-title, .product-name")
            name = name_node.text(strip=True) if name_node else None
            if not name:
                return None
            
            # Marque
            brand_node = node.css_first("span.product-brand, .product-brand")
            brand = brand_node.text(strip=True) if brand_node else ""
            
            # Prix principal
            price_node = node.css_first("span.price-sales, .price-sales, .product-price")
            price = self._parse_price(price_node.text()) if price_node else None
            
            # Prix au kg/L/unité
            price_per_unit_node = node.css_first(
                "span.price-per-unit, .price-per-unit, .price-per-kg, .price-detail"