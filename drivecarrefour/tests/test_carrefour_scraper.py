"""
Tests unitaires pour le module CarrefourScraper.
"""

import pytest
from pathlib import Path
import tempfile

from scrapers.carrefour_scraper import CarrefourScraper


@pytest.fixture
def temp_cache_dir():
    """Crée un répertoire temporaire pour le cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def scraper(temp_cache_dir):
    """Crée une instance de CarrefourScraper pour les tests."""
    # Désactive le cache pour les tests
    scraper = CarrefourScraper(cache_enabled=False)
    yield scraper
    # Fermeture propre
    pytest.asyncio.run(scraper.close())


# ==================== TESTS DES FONCTIONS DE PARSING ====================

class TestPriceParsing:
    """Tests pour la fonction _parse_price."""
    
    @pytest.mark.parametrize("price_str,expected", [
        ("2,99 €", 2.99),
        ("5€", 5.0),
        ("1,5", 1.5),
        ("10,00 €", 10.0),
        ("0,99€", 0.99),
        ("  3,50 €  ", 3.50),
        ("", None),
        ("Gratuit", None),
        ("2.99 €", 2.99),  # Avec point comme séparateur décimal
        ("2,99", 2.99),
        ("5", 5.0),
    ])
    def test_parse_price(self, scraper, price_str, expected):
        """Test le parsing des chaînes de prix."""
        result = scraper._parse_price(price_str)
        assert result == expected


class TestWeightParsing:
    """Tests pour la fonction _parse_weight."""
    
    @pytest.mark.parametrize("weight_str,expected", [
        ("500 g", 0.5),
        ("1 kg", 1.0),
        ("250 ml", 0.25),
        ("1 L", 1.0),
        ("100 cL", 1.0),
        ("10 ml", 0.01),
        ("  2 kg  ", 2.0),
        ("", None),
        ("500", None),  # Pas d'unité
        ("500grammes", 0.5),  # Sans espace
        ("1 kilogramme", 1.0),
        ("25 centilitres", 0.25),
    ])
    def test_parse_weight(self, scraper, weight_str, expected):
        """Test le parsing des chaînes de poids."""
        result = scraper._parse_weight(weight_str)
        assert result == expected


class TestQuantityParsing:
    """Tests pour la fonction _parse_quantity."""
    
    @pytest.mark.parametrize("text,expected", [
        ("6 œufs", 6),
        ("Barquette de 12", 12),
        ("Pack de 24 bouteilles", 24),
        ("1", 1),
        ("", None),
        ("Aucun nombre", None),
        ("5kg", 5),
    ])
    def test_parse_quantity(self, scraper, text, expected):
        """Test l'extraction de la quantité."""
        result = scraper._parse_quantity(text)
        assert result == expected


class TestUnitInference:
    """Tests pour la fonction _infer_unit."""
    
    @pytest.mark.parametrize("packaging,weight_str,expected", [
        ("6 pièces", "", "pièce"),
        ("Barquette de 12", "", "pièce"),
        ("", "500 g", "g"),
        ("", "1 kg", "kg"),
        ("", "1 L", "L"),
        ("", "250 ml", "mL"),
        ("1 unité", "", "pièce"),
        ("", "", None),
    ])
    def test_infer_unit(self, scraper, packaging, weight_str, expected):
        """Test l'inférence de l'unité."""
        result = scraper._infer_unit(packaging, weight_str)
        assert result == expected


# ==================== TESTS ASYNCHRONES ====================

@pytest.mark.asyncio
async def test_search_products(scraper):
    """Test la recherche de produits sur Carrefour."""
    # Recherche simple
    products = await scraper.search_products("oeufs")
    assert isinstance(products, list)
    assert len(products) > 0
    
    # Vérification de la structure des produits
    for product in products:
        assert "name" in product
        assert "url" in product
        assert product["name"] is not None
        assert product["url"] is not None


@pytest.mark.asyncio
async def test_search_products_with_cache():
    """Test la recherche avec cache activé."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / "cache"
        cache_dir.mkdir()
        
        async with CarrefourScraper(cache_enabled=True) as scraper:
            scraper.CACHE_DIR = cache_dir
            scraper.cache = None  # Réinitialiser
            
            # Première recherche (sans cache)
            products1 = await scraper.search_products("farine")
            assert len(products1) > 0
            
            # Deuxième recherche (avec cache)
            products2 = await scraper.search_products("farine")
            assert len(products2) > 0
            
            # Les résultats devraient être identiques (même si on ne vérifie pas le cache ici)
            assert len(products1) == len(products2)


@pytest.mark.asyncio
async def test_search_products_not_found():
    """Test la recherche avec un produit introuvable."""
    async with CarrefourScraper(cache_enabled=False) as scraper:
        products = await scraper.search_products("produit_inexistant_xyz_123")
        # Même si aucun produit n'est trouvé, la fonction doit retourner une liste vide
        assert isinstance(products, list)


@pytest.mark.asyncio
async def test_fetch_with_retry():
    """Test la fonction _fetch avec retry."""
    async with CarrefourScraper(cache_enabled=False) as scraper:
        # Test avec une URL valide
        html = await scraper._fetch("https://www.carrefour.fr")
        assert isinstance(html, str)
        assert len(html) > 1000  # Une page HTML fait au moins 1000 caractères


@pytest.mark.asyncio
async def test_fetch_with_cache():
    """Test la fonction _fetch avec cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / "cache"
        cache_dir.mkdir()
        
        async with CarrefourScraper(cache_enabled=True) as scraper:
            scraper.CACHE_DIR = cache_dir
            scraper.cache = None  # Réinitialiser
            
            # Premier appel (remplit le cache)
            html1 = await scraper._fetch("https://www.carrefour.fr/s?q=test")
            
            # Deuxième appel (utilise le cache)
            html2 = await scraper._fetch("https://www.carrefour.fr/s?q=test")
            
            # Les résultats devraient être identiques
            assert html1 == html2


# ==================== TESTS D'INTÉGRATION ====================

@pytest.mark.asyncio
async def test_full_workflow():
    """Test le workflow complet : recherche -> parsing."""
    async with CarrefourScraper(cache_enabled=False) as scraper:
        # Recherche
        products = await scraper.search_products("lait")
        
        # Vérification
        assert len(products) > 0
        
        # Vérification des champs
        for product in products[:3]:  # On vérifie les 3 premiers
            assert product["name"] is not None
            assert isinstance(product["price"], (float, type(None)))
            assert isinstance(product["weight"], (float, type(None)))
            assert isinstance(product["url"], str)
            assert product["url"].startswith("https://")


# ==================== TESTS D'ERREURS ====================

@pytest.mark.asyncio
async def test_invalid_url():
    """Test avec une URL invalide."""
    async with CarrefourScraper(cache_enabled=False) as scraper:
        with pytest.raises(Exception):
            await scraper._fetch("https://url_invalide.xyz")


@pytest.mark.asyncio
async def test_http_error_404():
    """Test avec une page 404."""
    async with CarrefourScraper(cache_enabled=False) as scraper:
        with pytest.raises(ValueError, match="Page non trouvée"):
            await scraper._fetch("https://www.carrefour.fr/page_inexistante")
