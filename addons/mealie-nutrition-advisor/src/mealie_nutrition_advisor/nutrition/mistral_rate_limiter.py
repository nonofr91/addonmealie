"""Rate limiter partagé pour les requêtes Mistral AI."""

import time
import threading

# Rate limiting pour Mistral (compte free)
# D'après la doc Mistral, le compte free a une limite de 1 req/s
_MISTRAL_RATE_LIMIT = 1.0  # secondes entre chaque requête (1 req/s)
_last_mistral_request = 0
_lock = threading.Lock()


def wait_for_mistral_rate_limit() -> None:
    """Attend si nécessaire pour respecter le rate limit de Mistral."""
    global _last_mistral_request
    
    with _lock:
        current_time = time.time()
        time_since_last = current_time - _last_mistral_request
        if time_since_last < _MISTRAL_RATE_LIMIT:
            time.sleep(_MISTRAL_RATE_LIMIT - time_since_last)
        _last_mistral_request = time.time()
