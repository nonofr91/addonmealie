# Architecture d'Abstraction des Providers IA

## Contexte
Le projet mealie-import-orchestrator utilise actuellement l'IA de Cascade pour les tâches de structuration et d'analyse. Pour permettre le déploiement en production et éviter la dépendance exclusive à Cascade, il faut prévoir une architecture flexible permettant de brancher différentes IA externes (OpenAI, Anthropic, etc.).

## Architecture Proposée

### Pattern : Strategy Pattern + Factory Pattern

```
mealie-workflow/
├── src/
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── base.py              # Interface abstraite AIProvider
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── cascade_provider.py    # Implémentation Cascade
│   │   │   ├── openai_provider.py     # Implémentation OpenAI
│   │   │   ├── anthropic_provider.py   # Implémentation Anthropic
│   │   │   └── mock_provider.py        # Implémentation mock pour tests
│   │   └── factory.py            # Factory pour créer le provider approprié
```

### Interface Abstraite

```python
# src/ai/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any

class AIProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> str:
        """Compléter un prompt texte"""
        pass
    
    @abstractmethod
    def analyze_ingredient(self, ingredient_text: str) -> Dict[str, Any]:
        """Analyser un ingrédient texte"""
        pass
    
    @abstractmethod
    def structure_recipe(self, raw_recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Structurer une recette brute"""
        pass
```

### Factory Pattern

```python
# src/ai/factory.py
import os
from .base import AIProvider
from .providers.cascade_provider import CascadeProvider
from .providers.openai_provider import OpenAIProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.mock_provider import MockProvider

def create_ai_provider() -> AIProvider:
    provider_type = os.getenv("AI_PROVIDER", "cascade")
    
    providers = {
        "cascade": CascadeProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "mock": MockProvider,
    }
    
    provider_class = providers.get(provider_type, CascadeProvider)
    return provider_class()
```

### Configuration via Variables d'Environnement

```bash
# .env (développement local)
AI_PROVIDER=cascade  # Options: cascade, openai, anthropic, mock

# Configuration spécifique au provider
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-opus
```

### Sécurité des Clés API en Production (Coolify)

**Décision de sécurité :** Utiliser les variables d'environnement Coolify pour les clés API IA.

**Avantages :**
- Clés non présentes dans le code versionné
- Clés changeables sans rebuild l'image Docker
- Environnements différents (dev, staging, prod) avec des clés différentes
- Rotation des clés facilitée

**Configuration Coolify :**
```bash
# Variables d'environnement Coolify
AI_PROVIDER=openai
OPENAI_API_KEY=<clé secrète Coolify>
OPENAI_MODEL=gpt-4
MEALIE_BASE_URL=<URL Mealie Coolify>
MEALIE_API_KEY=<clé secrète Coolify>
```

**Important :** Jamais de clés API dans le code ou les fichiers versionnés. Toutes les clés sensibles doivent être configurées via Coolify.

### Implémentation Cascade Provider

```python
# src/ai/providers/cascade_provider.py
from ..base import AIProvider
from cascade_sdk import CascadeClient  # SDK fictif pour Cascade

class CascadeProvider(AIProvider):
    def __init__(self):
        self.client = CascadeClient()  # Utilise les MCP Cascade
    
    def complete(self, prompt: str, **kwargs) -> str:
        # Utilise les MCP Cascade pour compléter
        return self.client.complete(prompt)
    
    def analyze_ingredient(self, ingredient_text: str) -> Dict[str, Any]:
        # Utilise le skill ingredient-manager
        return self.client.analyze_ingredient(ingredient_text)
    
    def structure_recipe(self, raw_recipe: Dict[str, Any]) -> Dict[str, Any]:
        # Utilise le workflow de structuration
        return self.client.structure_recipe(raw_recipe)
```

### Implémentation OpenAI Provider

```python
# src/ai/providers/openai_provider.py
import os
from openai import OpenAI
from ..base import AIProvider

class OpenAIProvider(AIProvider):
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
    
    def complete(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    def analyze_ingredient(self, ingredient_text: str) -> Dict[str, Any]:
        # Implémentation spécifique OpenAI
        prompt = f"Analyse cet ingrédient: {ingredient_text}"
        response = self.complete(prompt)
        return self._parse_response(response)
    
    def structure_recipe(self, raw_recipe: Dict[str, Any]) -> Dict[str, Any]:
        # Implémentation spécifique OpenAI
        prompt = f"Structure cette recette: {raw_recipe}"
        response = self.complete(prompt)
        return self._parse_response(response)
```

### Implémentation Mock Provider (Tests)

```python
# src/ai/providers/mock_provider.py
from ..base import AIProvider

class MockProvider(AIProvider):
    def complete(self, prompt: str, **kwargs) -> str:
        return "Mock response for testing"
    
    def analyze_ingredient(self, ingredient_text: str) -> Dict[str, Any]:
        return {"quantity": 1, "unit": "cup", "food": "flour"}
    
    def structure_recipe(self, raw_recipe: Dict[str, Any]) -> Dict[str, Any]:
        return {"name": "Mock Recipe", "ingredients": [], "instructions": []}
```

## Avantages

1. **Flexibilité** : Changer de provider IA sans modifier le code métier
2. **Testabilité** : Mock provider pour les tests unitaires
3. **Production** : Possibilité d'utiliser des IA externes payantes en production
4. **Développement** : Utiliser Cascade pour le développement local
5. **Extensibilité** : Facile d'ajouter de nouveaux providers

## Implémentation Prioritaire

1. Créer l'interface abstraite `AIProvider`
2. Implémenter le `CascadeProvider` (refactor du code existant)
3. Implémenter le `MockProvider` pour les tests
4. Créer la factory pour sélectionner le provider
5. Ajouter la configuration via variables d'environnement
6. Implémenter `OpenAIProvider` et `AnthropicProvider` selon les besoins

## Fichiers à Créer/Modifier

- `mealie-workflow/src/ai/base.py` (nouveau)
- `mealie-workflow/src/ai/factory.py` (nouveau)
- `mealie-workflow/src/ai/providers/cascade_provider.py` (nouveau)
- `mealie-workflow/src/ai/providers/openai_provider.py` (nouveau)
- `mealie-workflow/src/ai/providers/anthropic_provider.py` (nouveau)
- `mealie-workflow/src/ai/providers/mock_provider.py` (nouveau)
- `mealie-workflow/.env.template` (ajouter variables AI_PROVIDER, etc.)
