"""Parser d'ingrédients utilisant Mistral AI pour les cas complexes."""

import json
import logging
from typing import Optional, Tuple

from mistralai import Mistral

logger = logging.getLogger(__name__)


class MistralIngredientParser:
    """Parser d'ingrédients utilisant l'API Mistral AI."""

    def __init__(self, api_key: Optional[str] = None, model: str = "mistral-small-latest"):
        """Initialise le parser Mistral.

        Args:
            api_key: Clé API Mistral (si None, désactivé)
            model: Modèle Mistral à utiliser
        """
        self.api_key = api_key
        self.model = model
        self.client = None
        self.enabled = False

        if api_key:
            try:
                self.client = Mistral(api_key=api_key)
                self.enabled = True
                logger.info(f"Mistral parser initialisé avec modèle {model}")
            except Exception as e:
                logger.warning(f"Impossible d'initialiser Mistral: {e}")
        else:
            logger.info("Mistral parser désactivé (pas de clé API)")

    def parse(self, note: str) -> Optional[Tuple[float, str, str]]:
        """Parse une note d'ingrédient avec Mistral AI.

        Args:
            note: Note d'ingrédient (ex: "200g de farine", "1 cuillère à soupe de sucre")

        Returns:
            Tuple (quantity, unit, name) ou None si erreur/désactivé
        """
        if not self.enabled or not self.client:
            return None

        try:
            prompt = f"""Parse cet ingrédient de recette et retourne uniquement un JSON valide:
"{note}"

Format JSON attendu (sans markdown, sans explication):
{{"quantity": nombre, "unit": "kg|g|l|ml|cl|unit|cuillère|tasse|pièce|pincée|...", "name": "nom de l'ingrédient en minuscules"}}

Règles:
- quantity: nombre décimal (ex: 0.5, 2, 10)
- unit: unité standardisée (kg pour kilogramme, g pour gramme, l pour litre, ml pour millilitre, cl pour centilitre, unit pour pièce/cuillère/tasse/etc.)
- name: nom de l'ingrédient uniquement, sans quantité ni unité
- Si impossible de parser, quantity=0, unit="unknown", name="{note}"
"""

            response = self.client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Bas pour plus de cohérence
                max_tokens=100,
            )

            content = response.choices[0].message.content.strip()

            # Nettoyer le contenu (enlever markdown si présent)
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # Parser le JSON
            data = json.loads(content)

            quantity = float(data.get("quantity", 0))
            unit = data.get("unit", "unknown").lower().strip()
            name = data.get("name", note).lower().strip()

            # Validation basique
            if quantity <= 0 or unit == "unknown":
                logger.debug(f"Mistral n'a pas pu parser: {note} → {content}")
                return None

            logger.debug(f"Mistral parsed: {note} → {quantity} {unit} {name}")
            return quantity, unit, name

        except json.JSONDecodeError as e:
            logger.warning(f"Mistral returned invalid JSON for '{note}': {content} - {e}")
            return None
        except Exception as e:
            logger.warning(f"Mistral parsing failed for '{note}': {e}")
            return None

    def health_check(self) -> bool:
        """Vérifie si le parser est fonctionnel."""
        if not self.enabled or not self.client:
            return False

        try:
            result = self.parse("200g de farine")
            return result is not None and result[0] > 0
        except Exception:
            return False
