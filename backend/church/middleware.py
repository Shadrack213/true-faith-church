"""
Answers GET /api/health/ before Django's HTTPS redirect and host checks.

Hosting platforms (e.g. Render) check that the app is alive by calling this URL
from inside their network, over plain HTTP and sometimes with an internal host
name. Those calls would otherwise get a redirect (HTTPS) or a 400 (unknown host).
The response only says whether the database is reachable; it reveals nothing else.
"""
from .views import database_ok
from django.http import JsonResponse

HEALTH_PATH = "/api/health/"


class HealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == HEALTH_PATH and request.method in ("GET", "HEAD"):
            if database_ok():
                return JsonResponse({"status": "ok", "database": "ok"})
            return JsonResponse({"status": "error", "database": "unavailable"}, status=503)
        return self.get_response(request)
