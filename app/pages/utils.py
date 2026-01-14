from __future__ import annotations

from django.conf import settings
from django.http import Http404
from django.utils import translation

from .models import Page


def get_page_or_404_any_language(slug: str) -> Page:
    """Fetch a Page by slug regardless of the currently active language."""

    tried = set()
    lang_order = []

    current = translation.get_language()
    if current:
        lang_order.append(current)
        tried.add(current)

    default_lang = getattr(settings, "LANGUAGE_CODE", None)
    if default_lang and default_lang not in tried:
        lang_order.append(default_lang)
        tried.add(default_lang)

    for code, _ in settings.LANGUAGES:
        if code not in tried:
            lang_order.append(code)
            tried.add(code)

    for code in lang_order:
        with translation.override(code):
            try:
                return Page.objects.get(slug=slug)
            except Page.DoesNotExist:
                continue
    raise Http404("No Page matches the given query.")
