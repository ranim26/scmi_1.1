import logging
import os
from time import perf_counter
from django.db import connection, reset_queries

logger = logging.getLogger('slowrequests')


class SlowRequestMiddleware:
    """Middleware de développement : log les requêtes lentes et le nombre de requêtes SQL.

    Se déclenche seulement en DEBUG. Seuil configurable via variable d'environnement
    `SLOW_REQUEST_THRESHOLD_MS` (défaut 200 ms).
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.threshold_ms = int(os.environ.get('SLOW_REQUEST_THRESHOLD_MS', '200'))

    def __call__(self, request):
        from django.conf import settings
        # Ne rien faire si on n'est pas en dev
        if not settings.DEBUG:
            return self.get_response(request)

        # Réinitialiser le tracking des queries (utile en DEBUG)
        try:
            reset_queries()
        except Exception:
            pass

        start = perf_counter()
        response = self.get_response(request)
        duration_ms = (perf_counter() - start) * 1000.0
        num_queries = len(connection.queries) if hasattr(connection, 'queries') else 0

        if duration_ms > self.threshold_ms:
            logger.warning('%s %s — %.2f ms — %d queries', request.method, request.get_full_path(), duration_ms, num_queries)
            # Log SQL (dernieres 20) en debug pour investigation
            try:
                for q in connection.queries[-20:]:
                    logger.debug(q.get('sql'))
            except Exception:
                pass

        return response
