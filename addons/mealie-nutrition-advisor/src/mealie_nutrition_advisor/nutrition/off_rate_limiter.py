"""Rate limiter partagé pour les requêtes Open Food Facts."""

import time
import threading

# Rate limiting pour Open Food Facts (service gratuit)
# OFF n'a pas de limite officielle documentée, mais on utilise 0.5s pour éviter les 503
_OFF_RATE_LIMIT = 0.5  # secondes entre chaque requête (2 req/s)
_last_off_request = 0
_lock = threading.Lock()


def wait_for_off_rate_limit() -> None:
    """Attend si nécessaire pour respecter le rate limit de OFF."""
    global _last_off_request
    
    with _lock:
        current_time = time.time()
        time_since_last = current_time - _last_off_request
        if time_since_last < _OFF_RATE_LIMIT:
            time.sleep(_OFF_RATE_LIMIT - time_since_last)
        _last_off_request = time.time()
