from urllib.parse import urlparse

from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.translation import activate
from django.views.decorators.cache import never_cache


def health(request):
    return JsonResponse({"ok": True})


@never_cache
def set_language(request):
    """
    Custom set_language view that redirects to home page in new language.

    This avoids the problem of trying to find translated URLs with different slugs.
    E.g., /en/about/ becomes /de/ (home) instead of trying /de/about/ (doesn't exist).
    """
    next_url = request.POST.get("next", request.GET.get("next"))
    if not next_url:
        next_url = request.META.get("HTTP_REFERER")

    lang_code = request.POST.get("language", request.GET.get("language"))

    if lang_code and lang_code in dict(settings.LANGUAGES):
        activate(lang_code)

        # Determine whether the target URL is a public page by inspecting its path.
        parsed = urlparse(next_url or "")
        path = parsed.path or ""
        first_segment = path.strip("/").split("/", 1)[0] if path else ""
        public_languages = {code for code, _ in settings.LANGUAGES}
        if first_segment in public_languages:
            response = HttpResponseRedirect(f"/{lang_code}/")
        else:
            response = HttpResponseRedirect(next_url or "/")

        # Set language cookie
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            lang_code,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path=settings.LANGUAGE_COOKIE_PATH,
            domain=settings.LANGUAGE_COOKIE_DOMAIN,
            secure=settings.LANGUAGE_COOKIE_SECURE,
            httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
            samesite=settings.LANGUAGE_COOKIE_SAMESITE,
        )
        return response

    # Fallback
    return HttpResponseRedirect(next_url or "/")
