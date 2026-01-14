# app/core/middleware.py
from django.utils.deprecation import MiddlewareMixin


class NoStoreForCMSMiddleware(MiddlewareMixin):
    """
    Prevent browser caching of authenticated/admin pages so back button
    can't show stale content after logout.
    """

    def process_response(self, request, response):
        path = request.path
        if path.startswith("/cms") or path.startswith("/accounts"):
            # Strong headers to defeat both HTTP cache and bfcache
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
        return response
