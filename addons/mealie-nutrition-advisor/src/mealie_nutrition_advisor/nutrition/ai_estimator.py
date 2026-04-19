"""LLM fallback estimator — used when Open Food Facts returns no result."""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

from ..models.nutrition import NutritionFacts, NutritionSource
from .mistral_rate_limiter import wait_for_mistral_rate_limit

logger = logging.getLogger(__name__)

AI_PROVIDER = os.environ.get("AI_PROVIDER", "mock")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
MISTRAL_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")

ESTIMATION_PROMPT = """Tu es un nutritionniste expert. 
Estime les valeurs nutritionnelles pour 100g de l'aliment suivant : "{ingredient}"

Réponds UNIQUEMENT avec un objet JSON valide (sans markdown, sans explications) :
{{
  "calories_kcal": <float>,
  "protein_g": <float>,
  "fat_g": <float>,
  "saturated_fat_g": <float>,
  "carbohydrate_g": <float>,
  "sugar_g": <float>,
  "fiber_g": <float>,
  "sodium_mg": <float>,
  "confidence": <float entre 0 et 1>
}}"""

MOCK_DATA: dict[str, dict] = {
    "default": {"calories_kcal": 150, "protein_g": 5, "fat_g": 5, "saturated_fat_g": 1,
                "carbohydrate_g": 20, "sugar_g": 3, "fiber_g": 2, "sodium_mg": 100, "confidence": 0.3},
    "viande": {"calories_kcal": 200, "protein_g": 25, "fat_g": 10, "saturated_fat_g": 3,
               "carbohydrate_g": 0, "sugar_g": 0, "fiber_g": 0, "sodium_mg": 70, "confidence": 0.4},
    "légume": {"calories_kcal": 35, "protein_g": 2, "fat_g": 0.3, "saturated_fat_g": 0,
               "carbohydrate_g": 7, "sugar_g": 3, "fiber_g": 3, "sodium_mg": 10, "confidence": 0.4},
    "fruit": {"calories_kcal": 55, "protein_g": 0.5, "fat_g": 0.2, "saturated_fat_g": 0,
              "carbohydrate_g": 13, "sugar_g": 10, "fiber_g": 2, "sodium_mg": 2, "confidence": 0.4},
    "fromage": {"calories_kcal": 350, "protein_g": 20, "fat_g": 28, "saturated_fat_g": 18,
                "carbohydrate_g": 2, "sugar_g": 0.5, "fiber_g": 0, "sodium_mg": 600, "confidence": 0.4},
    "farine": {"calories_kcal": 350, "protein_g": 10, "fat_g": 1, "saturated_fat_g": 0.2,
               "carbohydrate_g": 74, "sugar_g": 1, "fiber_g": 3, "sodium_mg": 2, "confidence": 0.5},
    "beurre": {"calories_kcal": 720, "protein_g": 0.5, "fat_g": 80, "saturated_fat_g": 50,
               "carbohydrate_g": 0.7, "sugar_g": 0.7, "fiber_g": 0, "sodium_mg": 600, "confidence": 0.5},
    "huile": {"calories_kcal": 880, "protein_g": 0, "fat_g": 100, "saturated_fat_g": 14,
              "carbohydrate_g": 0, "sugar_g": 0, "fiber_g": 0, "sodium_mg": 0, "confidence": 0.5},
    "sucre": {"calories_kcal": 400, "protein_g": 0, "fat_g": 0, "saturated_fat_g": 0,
              "carbohydrate_g": 100, "sugar_g": 100, "fiber_g": 0, "sodium_mg": 0, "confidence": 0.5},
    "riz": {"calories_kcal": 360, "protein_g": 7, "fat_g": 0.5, "saturated_fat_g": 0.1,
            "carbohydrate_g": 80, "sugar_g": 0.1, "fiber_g": 1.3, "sodium_mg": 5, "confidence": 0.5},
    "pâtes": {"calories_kcal": 370, "protein_g": 13, "fat_g": 1.5, "saturated_fat_g": 0.3,
              "carbohydrate_g": 75, "sugar_g": 3, "fiber_g": 3, "sodium_mg": 6, "confidence": 0.5},
}


class AIEstimator:
    """Estime les valeurs nutritionnelles via LLM quand OFF échoue."""

    def __init__(self, provider: str = AI_PROVIDER) -> None:
        self.provider = provider

    def estimate(self, ingredient_name: str) -> Optional[NutritionFacts]:
        """Retourne une estimation nutritionnelle pour l'ingrédient donné."""
        if self.provider == "mock":
            return self._mock_estimate(ingredient_name)
        elif self.provider == "openai":
            return self._openai_estimate(ingredient_name)
        elif self.provider == "anthropic":
            return self._anthropic_estimate(ingredient_name)
        elif self.provider == "mistral":
            return self._mistral_estimate(ingredient_name)
        else:
            logger.warning("AI_PROVIDER inconnu '%s', fallback sur mock", self.provider)
            return self._mock_estimate(ingredient_name)

    def _mock_estimate(self, ingredient_name: str) -> NutritionFacts:
        """Estimation basée sur des mots-clés — pour les tests sans clé API."""
        name_lower = ingredient_name.lower()
        data = MOCK_DATA["default"]
        for keyword, kw_data in MOCK_DATA.items():
            if keyword in name_lower:
                data = kw_data
                break
        logger.debug("AI mock: estimation pour '%s' → %.0f kcal/100g", ingredient_name, data["calories_kcal"])
        return NutritionFacts(**data, source=NutritionSource.ai_estimate)

    def _openai_estimate(self, ingredient_name: str) -> Optional[NutritionFacts]:
        try:
            from openai import OpenAI
        except ImportError:
            logger.error("openai non installé. pip install 'mealie-nutrition-advisor[openai]'")
            return self._mock_estimate(ingredient_name)

        if not OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY manquante")
            return self._mock_estimate(ingredient_name)

        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            prompt = ESTIMATION_PROMPT.format(ingredient=ingredient_name)
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            return self._parse_llm_response(raw)
        except Exception as exc:
            logger.warning("OpenAI erreur pour '%s': %s", ingredient_name, exc)
            return self._mock_estimate(ingredient_name)

    def _anthropic_estimate(self, ingredient_name: str) -> Optional[NutritionFacts]:
        try:
            import anthropic
        except ImportError:
            logger.error("anthropic non installé. pip install 'mealie-nutrition-advisor[anthropic]'")
            return self._mock_estimate(ingredient_name)

        if not ANTHROPIC_API_KEY:
            logger.error("ANTHROPIC_API_KEY manquante")
            return self._mock_estimate(ingredient_name)

        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            prompt = ESTIMATION_PROMPT.format(ingredient=ingredient_name)
            message = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text if message.content else "{}"
            return self._parse_llm_response(raw)
        except Exception as exc:
            logger.warning("Anthropic erreur pour '%s': %s", ingredient_name, exc)
            return self._mock_estimate(ingredient_name)

    def _mistral_estimate(self, ingredient_name: str) -> Optional[NutritionFacts]:
        try:
            from mistralai.client import Mistral
        except ImportError:
            logger.error("mistralai non installé. pip install 'mealie-nutrition-advisor[mistral]'")
            return self._mock_estimate(ingredient_name)

        if not MISTRAL_API_KEY:
            logger.error("MISTRAL_API_KEY manquante")
            return self._mock_estimate(ingredient_name)

        try:
            # Rate limiting partagé pour Mistral (compte free)
            wait_for_mistral_rate_limit()

            client = Mistral(api_key=MISTRAL_API_KEY)
            prompt = ESTIMATION_PROMPT.format(ingredient=ingredient_name)
            response = client.chat.complete(
                model=MISTRAL_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content if response.choices else "{}"
            return self._parse_llm_response(raw)
        except Exception as exc:
            logger.warning("Mistral erreur pour '%s': %s", ingredient_name, exc)
            return self._mock_estimate(ingredient_name)

    @staticmethod
    def _parse_llm_response(raw: str) -> Optional[NutritionFacts]:
        try:
            data = json.loads(raw)
            return NutritionFacts(
                calories_kcal=float(data.get("calories_kcal", 0)),
                protein_g=float(data.get("protein_g", 0)),
                fat_g=float(data.get("fat_g", 0)),
                saturated_fat_g=float(data.get("saturated_fat_g", 0)),
                carbohydrate_g=float(data.get("carbohydrate_g", 0)),
                sugar_g=float(data.get("sugar_g", 0)),
                fiber_g=float(data.get("fiber_g", 0)),
                sodium_mg=float(data.get("sodium_mg", 0)),
                source=NutritionSource.ai_estimate,
                confidence=float(data.get("confidence", 0.5)),
            )
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            logger.warning("Impossible de parser la réponse LLM: %s", exc)
            return None
