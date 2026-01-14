from __future__ import annotations

from django.utils.text import slugify

from app.pages.navigation import get_navigation_entries, serialize_nav_entries
from app.assets.models import Asset

from .models import SiteSettings
from .icon_pack import ICON_FILE_SPECS


def _build_site_icon_links():
    slug_map = {spec["slug"]: spec for spec in ICON_FILE_SPECS.values()}
    links = []
    qs = Asset.objects.filter(collection__slug="site-icons")
    for asset in qs:
        url = asset.file.url if asset.file else asset.url
        if not url:
            continue
        spec = slug_map.get(asset.slug, {})
        link = {"href": url, "rel": spec.get("link", {}).get("rel", "icon")}
        if spec.get("link", {}).get("type"):
            link["type"] = spec["link"]["type"]
        if spec.get("link", {}).get("sizes"):
            link["sizes"] = spec["link"]["sizes"]
        links.append(link)
    links.sort(key=lambda l: (l.get("rel", ""), l.get("sizes", "")))
    return links


def site_settings_context(request):
    settings_obj = SiteSettings.get_solo()

    nav_entries = get_navigation_entries() if settings_obj.public_pages_enabled else []
    pages = serialize_nav_entries(nav_entries)
    page_show_nav = bool(pages)

    # Determine active nav item
    req_slug = None
    if getattr(request, "resolver_match", None):
        req_slug = request.resolver_match.kwargs.get("slug")
    if req_slug is None and request.path == "/":
        req_slug = "home"

    current_nav_title = None
    if req_slug:
        lookup = slugify(req_slug) or req_slug
        for entry in nav_entries:
            if entry.slug == lookup or entry.pretty_slug == lookup:
                current_nav_title = entry.title
                break

    # Address helpers
    street = (settings_obj.address_street or "").strip()
    number = (settings_obj.address_number or "").strip()
    postal = (settings_obj.address_postal_code or "").strip()
    city = (settings_obj.address_city or "").strip()
    state = (settings_obj.address_state or "").strip()
    country = (settings_obj.address_country or "").strip()

    line1 = " ".join(x for x in [street, number] if x) if street else ""
    line2 = " ".join(x for x in [postal, city, state] if x)
    line3 = country
    has_any = any([line1, line2, line3])
    compact = ", ".join(x for x in [line1, line2, line3] if x)

    return {
        "site_settings": settings_obj,
        "public_pages": pages,
        "page_show_nav": page_show_nav,
        "current_nav_title": current_nav_title,
        "site_address_has_any": has_any,
        "site_address_line1": line1,
        "site_address_line2": line2,
        "site_address_line3": line3,
        "site_address_compact": compact,
        "site_icon_links": _build_site_icon_links(),
    }
