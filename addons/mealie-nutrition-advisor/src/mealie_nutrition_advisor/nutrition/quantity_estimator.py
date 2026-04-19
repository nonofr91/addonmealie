"""Estimate ingredient quantity using AI when no explicit weight is available."""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

from .mistral_rate_limiter import wait_for_mistral_rate_limit

logger = logging.getLogger(__name__)

AI_PROVIDER = os.environ.get("AI_PROVIDER", "mock")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
MISTRAL_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")

QUANTITY_ESTIMATION_PROMPT = """Tu es un expert en cuisine et nutrition.
Estime le poids en grammes de l'ingrédient suivant pour une recette de {servings} personnes : "{ingredient}"

Contexte important :
- Si c'est un aliment de base (viande, légume, fruit), estime le poids typique par personne
- Si c'est une épice ou un condiment, estime une petite quantité (1-5g)
- Si c'est un ingrédient principal, estime une portion raisonnable

Réponds UNIQUEMENT avec un objet JSON valide (sans markdown, sans explications) :
{{
  "weight_g": <float>,
  "confidence": <float entre 0 et 1>
}}"""

# Mock data pour les tests sans clé API
MOCK_QUANTITIES: dict[str, dict] = {
    "default": {"weight_g": 50, "confidence": 0.3},
    "sel": {"weight_g": 2, "confidence": 0.8},
    "poivre": {"weight_g": 1, "confidence": 0.8},
    "ail": {"weight_g": 5, "confidence": 0.8},
    "oignon": {"weight_g": 80, "confidence": 0.7},
    "huile": {"weight_g": 15, "confidence": 0.6},
    "beurre": {"weight_g": 15, "confidence": 0.6},
    "vinaigre": {"weight_g": 10, "confidence": 0.6},
    "herbe": {"weight_g": 3, "confidence": 0.6},
    "épice": {"weight_g": 2, "confidence": 0.6},
    "graisse": {"weight_g": 30, "confidence": 0.5},
    "os": {"weight_g": 100, "confidence": 0.5},
}


class QuantityEstimator:
    """Estimate ingredient weight in grams using AI context-aware estimation."""

    def __init__(self, provider: str = AI_PROVIDER) -> None:
        self.provider = provider

    def estimate(self, ingredient_text: str, servings: int = 4) -> Optional[int]:
        """Estimate weight in grams for an ingredient without explicit quantity.

        Args:
            ingredient_text: Text like "gigot d'agneau", "oignon", etc.
            servings: Number of recipe servings for context

        Returns:
            Estimated weight in grams, or None if estimation fails
        """
        if self.provider == "mock":
            return self._mock_estimate(ingredient_text)
        elif self.provider == "openai":
            return self._openai_estimate(ingredient_text, servings)
        elif self.provider == "anthropic":
            return self._anthropic_estimate(ingredient_text, servings)
        elif self.provider == "mistral":
            return self._mistral_estimate(ingredient_text, servings)
        else:
            logger.warning("AI_PROVIDER inconnu '%s', fallback sur mock", self.provider)
            return self._mock_estimate(ingredient_text)

    def _mock_estimate(self, ingredient_text: str) -> Optional[int]:
        """Estimation basée sur des mots-clés — pour les tests sans clé API."""
        name_lower = ingredient_text.lower()
        data = MOCK_QUANTITIES["default"]
        for keyword, kw_data in MOCK_QUANTITIES.items():
            if keyword in name_lower:
                data = kw_data
                break
        logger.debug("AI mock: estimation pour '%s' → %dg", ingredient_text, data["weight_g"])
        return int(data["weight_g"])

    def _openai_estimate(self, ingredient_text: str, servings: int) -> Optional[int]:
        try:
            from openai import OpenAI
        except ImportError:
            logger.error("openai non installé. pip install 'mealie-nutrition-advisor[openai]'")
            return self._mock_estimate(ingredient_text)

        if not OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY manquante")
            return self._mock_estimate(ingredient_text)

        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            prompt = QUANTITY_ESTIMATION_PROMPT.format(ingredient=ingredient_text, servings=servings)
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            return self._parse_llm_response(raw)
        except Exception as exc:
            logger.warning("OpenAI erreur pour '%s': %s", ingredient_text, exc)
            return self._mock_estimate(ingredient_text)

    def _anthropic_estimate(self, ingredient_text: str, servings: int) -> Optional[int]:
        try:
            import anthropic
        except ImportError:
            logger.error("anthropic non installé. pip install 'mealie-nutrition-advisor[anthropic]'")
            return self._mock_estimate(ingredient_text)

        if not ANTHROPIC_API_KEY:
            logger.error("ANTHROPIC_API_KEY manquante")
            return self._mock_estimate(ingredient_text)

        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            prompt = QUANTITY_ESTIMATION_PROMPT.format(ingredient=ingredient_text, servings=servings)
            message = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text if message.content else "{}"
            return self._parse_llm_response(raw)
        except Exception as exc:
            logger.warning("Anthropic erreur pour '%s': %s", ingredient_text, exc)
            return self._mock_estimate(ingredient_text)

    def _mistral_estimate(self, ingredient_text: str, servings: int) -> Optional[int]:
        try:
            from mistralai.client import Mistral
        except ImportError:
            logger.error("mistralai non installé. pip install mistralai")
            return self._mock_estimate(ingredient_text)

        if not MISTRAL_API_KEY:
            logger.error("MISTRAL_API_KEY manquante")
            return self._mock_estimate(ingredient_text)

        try:
            # Rate limiting partagé pour Mistral (compte free)
            wait_for_mistral_rate_limit()

            client = Mistral(api_key=MISTRAL_API_KEY)
            prompt = QUANTITY_ESTIMATION_PROMPT.format(ingredient=ingredient_text, servings=servings)
            response = client.chat.complete(
                model=MISTRAL_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content if response.choices else "{}"
            return self._parse_llm_response(raw)
        except Exception as exc:
            logger.warning("Mistral erreur pour '%s': %s", ingredient_text, exc)
            return self._mock_estimate(ingredient_text)

    @staticmethod
    def _parse_llm_response(raw: str) -> Optional[int]:
        try:
            data = json.loads(raw)
            weight_g = float(data.get("weight_g", 50))
            confidence = float(data.get("confidence", 0.5))
            logger.debug("AI estimation: %dg (confidence: %.2f)", weight_g, confidence)
            return int(weight_g)
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            logger.warning("Impossible de parser la réponse LLM: %s", exc)
            return None

    def __enter__(self) -> "QuantityEstimator":
        return self

    def __exit__(self, *args) -> None:
        pass
