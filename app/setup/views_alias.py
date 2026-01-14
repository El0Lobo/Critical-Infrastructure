# app/setup/views_alias.py  (or add into your existing views.py)
from django.http import Http404
from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse
from django.utils.text import slugify

from .models import SiteSettings


def page_alias(request, pretty: str):
    s = SiteSettings.get_solo()
    for line in (s.required_pages or "").splitlines():
        raw = (line or "").strip()
        if not raw:
            continue
        if "|" in raw:
            slug, label = (part.strip() for part in raw.split("|", 1))
        else:
            label = raw
            slug = slugify(label)

        if slugify(label) == pretty:
            # redirect to the canonical slug URL
            try:
                url = reverse("pages:detail", kwargs={"slug": slug})
            except NoReverseMatch:
                url = "/" if slug == "home" else f"/{slug}/"
            return redirect(url, permanent=True)
    raise Http404()
