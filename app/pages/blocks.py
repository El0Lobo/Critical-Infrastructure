from __future__ import annotations

import hashlib
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.text import slugify

from app.setup.models import SiteSettings

if TYPE_CHECKING:
    from collections.abc import Iterable

from . import data_sources
from .structured_data import (
    build_event_structured_data,
    build_map_structured_data,
    build_menu_structured_data,
)

Block = dict[str, Any]
Context = dict[str, Any]

HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

STYLE_FONT_STACKS = {
    "sans": '"Inter", "Helvetica Neue", Arial, sans-serif',
    "serif": 'Georgia, "Times New Roman", serif',
    "mono": 'ui-monospace, "SFMono-Regular", Menlo, Consolas, "Liberation Mono", monospace',
    "display": '"Oswald", "Archivo Black", "Arial Narrow", sans-serif',
    "press_start": '"Press Start 2P", cursive, "Courier New", monospace',
    "archivo_black": '"Archivo Black", "Arial Black", sans-serif',
    "glass_antiqua": '"Glass Antiqua", "Comic Sans MS", cursive',
    "im_fell": '"IM Fell DW Pica", Georgia, serif',
    "orbitron": '"Orbitron", "Segoe UI", sans-serif',
    "pathway_extreme": '"Pathway Extreme", "Raleway", sans-serif',
    "raleway": '"Raleway", "Helvetica Neue", sans-serif',
    "special_elite": '"Special Elite", "Courier New", monospace',
    "staatliches": '"Staatliches", "Archivo Black", sans-serif',
}

STYLE_FONT_SIZES = {
    "xs": "0.85rem",
    "sm": "0.95rem",
    "base": "1rem",
    "lg": "1.15rem",
    "xl": "1.35rem",
    "xxl": "1.6rem",
}

STYLE_DEFAULTS = {
    "font_family": "",
    "font_size": "",
    "text_color": "",
    "background_color": "",
    "font_asset": None,
}

FONT_MIME_FORMATS = {
    "font/woff2": "woff2",
    "font/woff": "woff",
    "font/ttf": "truetype",
    "font/otf": "opentype",
    "application/font-woff": "woff",
}


def _resolve_media(request, url: str | None) -> str | None:
    if not url:
        return None
    if request and url.startswith("/"):
        return request.build_absolute_uri(url)
    return url


def _format_file_size(value: Any) -> str:
    try:
        size = int(value)
    except (TypeError, ValueError):
        return ""
    if size <= 0:
        return ""
    if size < 1024:
        return f"{size} B"
    units = ["KB", "MB", "GB", "TB"]
    result = float(size)
    unit = "KB"
    for label in units:
        result /= 1024
        unit = label
        if result < 1024:
            break
    return f"{result:.1f} {unit}" if result < 10 else f"{int(result)} {unit}"


def _format_duration(value: Any) -> str:
    try:
        seconds = int(float(value))
    except (TypeError, ValueError):
        return ""
    if seconds <= 0:
        return ""
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:d}:{secs:02d}"


def _block_element_id(block: Block | None, prefix: str) -> str:
    raw = ""
    if isinstance(block, dict):
        raw = str(block.get("id") or block.get("pk") or "")
    if not raw:
        raw = "block"
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", raw).strip("-") or "block"
    return f"{prefix}-{safe}"


def _clean_hex_color(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    candidate = value.strip()
    if not HEX_COLOR_RE.match(candidate):
        return ""
    if len(candidate) == 4:
        candidate = "#" + "".join(char * 2 for char in candidate[1:])
    return candidate.lower()


def _guess_font_format(url: str, hint: str | None = None) -> str:
    if hint:
        label = hint.lower()
        if label in FONT_MIME_FORMATS.values():
            return label
        mapped = FONT_MIME_FORMATS.get(label)
        if mapped:
            return mapped
    root = url.split("?", 1)[0]
    ext = os.path.splitext(root)[1].lower()
    return {
        ".woff2": "woff2",
        ".woff": "woff",
        ".otf": "opentype",
        ".ttf": "truetype",
    }.get(ext, "truetype")


def _normalise_font_asset(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    url = str(value.get("url") or "").strip()
    if not url or not url.startswith(("/", "http://", "https://")):
        return None
    asset_id = value.get("id")
    try:
        asset_id = int(asset_id)
    except (TypeError, ValueError):
        asset_id = None
    title = str(value.get("title") or "").strip()
    mime = str(value.get("mime_type") or "").strip() or None
    format_hint = str(value.get("format") or "").strip() or None
    return {
        "id": asset_id,
        "title": title,
        "url": url,
        "format": _guess_font_format(url, format_hint or mime),
    }


def _normalise_style_dict(value: Any) -> dict[str, Any]:
    clean = STYLE_DEFAULTS.copy()
    if not isinstance(value, dict):
        return clean
    font_family = value.get("font_family")
    if isinstance(font_family, str) and font_family in STYLE_FONT_STACKS:
        clean["font_family"] = font_family
    font_size = value.get("font_size")
    if isinstance(font_size, str) and font_size in STYLE_FONT_SIZES:
        clean["font_size"] = font_size
    clean["text_color"] = _clean_hex_color(value.get("text_color"))
    clean["background_color"] = _clean_hex_color(value.get("background_color"))
    clean["font_asset"] = _normalise_font_asset(value.get("font_asset"))
    return clean


def _register_font_face(
    asset: dict[str, Any] | None,
    font_cache: dict[str, tuple[str, str]],
) -> str:
    if not asset:
        return ""
    url = asset.get("url")
    if not url:
        return ""
    fmt = asset.get("format") or "truetype"
    family_hint = asset.get("family")
    cache_key = f"{family_hint or url}|{fmt}"
    if cache_key not in font_cache:
        digest = hashlib.sha1(cache_key.encode("utf-8")).hexdigest()[:10]
        family = family_hint or f"CMSFont-{digest}"
        safe_url = url.replace("'", "\\'")
        css = (
            f"@font-face{{font-family:'{family}';src:url('{safe_url}') format('{fmt}');"
            "font-display:swap;}}"
        )
        font_cache[cache_key] = (family, css)
    return font_cache[cache_key][0]


def _build_inline_style(
    style: dict[str, Any],
    font_cache: dict[str, tuple[str, str]],
) -> str:
    inline_parts: list[str] = []
    font_asset = style.get("font_asset")
    font_family_value = ""
    font_face_name = _register_font_face(font_asset, font_cache)
    if font_face_name:
        font_family_value = f"'{font_face_name}'"
    else:
        font_stack = STYLE_FONT_STACKS.get(style.get("font_family") or "")
        if font_stack:
            font_family_value = font_stack
        else:
            style["font_family"] = ""
    if font_family_value:
        inline_parts.append(f"font-family:{font_family_value}")
    size_value = STYLE_FONT_SIZES.get(style.get("font_size") or "")
    if size_value:
        inline_parts.append(f"font-size:{size_value}")
    else:
        style["font_size"] = ""
    if style.get("text_color"):
        inline_parts.append(f"color:{style['text_color']}")
    if style.get("background_color"):
        inline_parts.append(f"background-color:{style['background_color']}")
    return "; ".join(inline_parts)


def _apply_style_overrides(props: dict[str, Any]) -> None:
    font_cache: dict[str, tuple[str, str]] = {}
    base_style = _normalise_style_dict(props.get("style"))
    props["style"] = base_style
    props["style_inline"] = _build_inline_style(base_style, font_cache)

    inline_targets: dict[str, str] = {}
    style_targets = props.get("style_targets")
    if isinstance(style_targets, dict):
        cleaned_targets = {}
        for key, value in style_targets.items():
            style_dict = _normalise_style_dict(value)
            cleaned_targets[key] = style_dict
            inline_targets[key] = _build_inline_style(style_dict, font_cache)
        props["style_targets"] = cleaned_targets
    props["style_inline_targets"] = inline_targets
    inline_fonts = props.get("inline_fonts")
    if isinstance(inline_fonts, list):
        for item in inline_fonts:
            _register_font_face(item, font_cache)
    props["style_font_faces"] = [mark_safe(css) for _, css in font_cache.values()]


def normalise_theme(value: Any) -> dict[str, dict[str, Any]]:
    """
    Normalise a user-supplied theme payload into style dictionaries.
    """

    payload = value if isinstance(value, dict) else {}
    return {
        "body": _normalise_style_dict(payload.get("body")),
        "sections": _normalise_style_dict(payload.get("sections")),
    }


def build_theme_css(value: Any) -> tuple[str, dict[str, dict[str, Any]]]:
    """
    Build inline CSS (including @font-face declarations) for a theme payload.
    """

    theme = normalise_theme(value)
    font_cache: dict[str, tuple[str, str]] = {}
    css_rules: list[str] = []

    body_inline = _build_inline_style(theme["body"], font_cache)
    if body_inline:
        css_rules.append(f"body {{{body_inline}}}")
        css_rules.append(f".site-shell {{{body_inline}}}")
    section_inline = _build_inline_style(theme["sections"], font_cache)
    if section_inline:
        css_rules.append(f".page-block {{{section_inline}}}")
        css_rules.append(f".page-block__container {{{section_inline}}}")

    font_faces = [css for _, css in font_cache.values()]
    css = "\n".join(font_faces + css_rules).strip()
    return css, theme


def render_blocks(
    blocks: Iterable[Block],
    *,
    request=None,
    extra_context: Context | None = None,
) -> str:
    rendered: list[str] = []
    for block in blocks or []:
        html = render_block(block, request=request, extra_context=extra_context)
        if html:
            rendered.append(html)
    return mark_safe("".join(rendered))  # noqa: S308


def render_block(
    block: Block,
    *,
    request=None,
    extra_context: Context | None = None,
) -> str:
    block_type = block.get("type")
    renderer = BLOCK_RENDERERS.get(block_type)
    if not renderer:
        return ""
    props = deepcopy(block.get("props", {}))
    _apply_style_overrides(props)
    context = {
        "block": block,
        "props": props,
        **(extra_context or {}),
    }
    return renderer(context=context, request=request)


def _prepare_asset_entries(items: Any) -> tuple[list[dict[str, Any]], list[int]]:
    entries: list[dict[str, Any]] = []
    ids: list[int] = []
    for raw in items or []:
        if not isinstance(raw, dict):
            continue
        asset_meta = raw.get("asset")
        if not isinstance(asset_meta, dict):
            asset_meta = {}
        asset_id = asset_meta.get("id") or raw.get("asset_id")
        try:
            asset_id_int = int(asset_id)
        except (TypeError, ValueError):
            asset_id_int = None
        if asset_id_int:
            ids.append(asset_id_int)
        entries.append(
            {
                "asset_id": asset_id_int,
                "asset_meta": asset_meta,
                "data": raw,
            }
        )
    return entries, ids


def _render_template(template_name: str, context: Context, request=None) -> str:
    return render_to_string(template_name, context, request=request)


def _hero_renderer(*, context: Context, request=None) -> str:
    props = context["props"]
    props["background_image_resolved"] = _resolve_media(request, props.get("background_image"))
    props.setdefault("alignment", "center")
    props.setdefault("overlay", 0.4)
    props.setdefault("actions", [])
    return _render_template("pages/blocks/hero.html", context, request=request)


def _rich_text_renderer(*, context: Context, request=None) -> str:
    return _render_template("pages/blocks/rich_text.html", context, request=request)


def _events_renderer(*, context: Context, request=None) -> str:
    props = context["props"]
    events = data_sources.get_events(
        limit=int(props.get("limit", 6) or 6),
        include_internal=bool(props.get("include_internal")),
    )
    for event in events:
        event["hero_image"] = _resolve_media(request, event.get("hero_image"))
        if request and event.get("url") and event["url"].startswith("/"):
            event["url"] = request.build_absolute_uri(event["url"])
    structured_data_list = context.get("structured_data")
    if isinstance(structured_data_list, list) and events:
        site_context = data_sources.get_site_context()
        structured_data_list.extend(
            build_event_structured_data(events, site_context=site_context)
        )
    context = {**context, "events": events}
    return _render_template("pages/blocks/events.html", context, request=request)


def _events_compact_renderer(*, context: Context, request=None) -> str:
    props = context["props"]
    events = data_sources.get_events(
        limit=int(props.get("limit", 3) or 3),
        include_internal=bool(props.get("include_internal")),
    )
    for event in events:
        event["hero_image"] = _resolve_media(request, event.get("hero_image"))
        if request and event.get("url") and event["url"].startswith("/"):
            event["url"] = request.build_absolute_uri(event["url"])
    context = {**context, "events": events}
    return _render_template("pages/blocks/events_compact.html", context, request=request)


def _events_archive_renderer(*, context: Context, request=None) -> str:
    props = context["props"]
    category_slugs = props.get("category_slugs")
    events = data_sources.get_event_archive(
        limit=int(props.get("limit", 12) or 12),
        include_internal=bool(props.get("include_internal")),
        include_past=bool(props.get("include_past")),
        category_slugs=category_slugs if isinstance(category_slugs, list) else None,
    )
    for event in events:
        event["hero_image"] = _resolve_media(request, event.get("hero_image"))
        if request and event.get("url") and event["url"].startswith("/"):
            event["url"] = request.build_absolute_uri(event["url"])
    categories = data_sources.get_event_categories()
    context = {**context, "events": events, "event_categories": categories}
    return _render_template("pages/blocks/events_archive.html", context, request=request)


def _recurring_events_renderer(*, context: Context, request=None) -> str:
    props = context["props"]
    series = data_sources.get_recurring_series(
        limit=int(props.get("limit", 6) or 6),
        include_internal=bool(props.get("include_internal")),
        include_past=bool(props.get("include_past")),
        occurrence_limit=int(props.get("occurrence_limit", 6) or 6),
    )
    for event in series:
        event["hero_image"] = _resolve_media(request, event.get("hero_image"))
        if request and event.get("url") and event["url"].startswith("/"):
            event["url"] = request.build_absolute_uri(event["url"])
    context = {**context, "series": series}
    return _render_template("pages/blocks/recurring_events.html", context, request=request)


def _news_latest_renderer(*, context: Context, request=None) -> str:
    props = context["props"]
    posts = data_sources.get_recent_news(
        limit=int(props.get("limit") or 3),
        category=(props.get("category") or "").strip() or None,
    )
    for post in posts:
        if request and post.get("url", "").startswith("/"):
            post["url"] = request.build_absolute_uri(post["url"])
    default_link = reverse("news_public:public_news_index")
    link_href = props.get("link_href") or default_link
    if request and link_href.startswith("/"):
        link_href = request.build_absolute_uri(link_href)
    context = {**context, "posts": posts, "cta_url": link_href}
    return _render_template("pages/blocks/news_latest.html", context, request=request)


def _news_archive_renderer(*, context: Context, request=None) -> str:
    props = context["props"]
    posts = data_sources.get_recent_news(
        limit=int(props.get("limit") or 6),
        category=(props.get("category") or "").strip() or None,
    )
    for post in posts:
        if request and post.get("url", "").startswith("/"):
            post["url"] = request.build_absolute_uri(post["url"])
    categories = data_sources.get_news_categories()
    news_url = reverse("news_public:public_news_index")
    if request and news_url.startswith("/"):
        news_url = request.build_absolute_uri(news_url)
    context = {**context, "posts": posts, "categories": categories, "news_url": news_url}
    return _render_template("pages/blocks/news_archive.html", context, request=request)


def _menu_renderer(*, context: Context, request=None) -> str:
    props = context["props"]
    categories = data_sources.get_menu_structure(props.get("category_slugs"))
    structured_data_list = context.get("structured_data")
    if isinstance(structured_data_list, list):
        site_context = data_sources.get_site_context()
        menu_ld = build_menu_structured_data(
            categories,
            site_context=site_context,
            title=(props.get("title") or "").strip() or None,
        )
        if menu_ld:
            structured_data_list.append(menu_ld)
    context = {**context, "categories": categories}
    return _render_template("pages/blocks/menu.html", context, request=request)


def _opening_hours_renderer(*, context: Context, request=None) -> str:
    site = data_sources.get_site_context()
    context = {**context, "site": site, "hours": site["opening_hours"]}
    return _render_template("pages/blocks/opening_hours.html", context, request=request)


def _contact_renderer(*, context: Context, request=None) -> str:
    site = data_sources.get_site_context()
    site["logo"] = _resolve_media(request, site.get("logo"))
    props = context.get("props", {})
    site_contact = site.get("contact", {}) or {}
    site_address = site.get("address", {}) or {}
    site_social = site.get("social", {}) or {}

    default_contact_fields = [field for field, _ in CONTACT_BLOCK_FIELDS]
    selected_contact_fields = props.get("contact_fields")
    if isinstance(selected_contact_fields, list):
        selected_contact_fields = [
            field for field in selected_contact_fields if field in default_contact_fields
        ]
    else:
        selected_contact_fields = default_contact_fields

    social_defaults = [field for field, _ in CONTACT_BLOCK_SOCIALS]
    selected_social_fields = props.get("social_fields")
    if isinstance(selected_social_fields, list):
        selected_social_fields = [
            field for field in selected_social_fields if field in social_defaults
        ]
    else:
        selected_social_fields = social_defaults if props.get("show_social", True) else []

    def _clean_url(value: str | None) -> str:
        if not value:
            return ""
        value = re.sub(r"^https?://", "", value)
        return value.rstrip("/")

    if site_contact.get("website"):
        site_contact["website_display"] = _clean_url(site_contact.get("website"))

    social_links: list[dict[str, str]] = []
    for key, label in CONTACT_BLOCK_SOCIALS:
        if key not in selected_social_fields:
            continue
        url = site_social.get(key)
        if not url:
            continue
        social_links.append(
            {
                "label": label,
                "href": url,
                "display": _clean_url(url),
                "icon": SOCIAL_ICON_FILES.get(key),
            }
        )

    address_has_any = any(
        [
            site_address.get("street"),
            site_address.get("number"),
            site_address.get("postal_code"),
            site_address.get("city"),
            site_address.get("country"),
        ]
    )

    show_address = "address" in selected_contact_fields and address_has_any
    show_phone = "phone" in selected_contact_fields and bool(site_contact.get("phone"))
    show_email = "email" in selected_contact_fields and bool(site_contact.get("email"))
    show_website = "website" in selected_contact_fields and bool(site_contact.get("website"))

    context = {
        **context,
        "site": site,
        "contact_fields": selected_contact_fields,
        "social_links": social_links,
        "show_address": show_address,
        "show_phone": show_phone,
        "show_email": show_email,
        "show_website": show_website,
        "contact_icons": CONTACT_ICON_FILES,
    }
    return _render_template("pages/blocks/contact.html", context, request=request)


SOCIAL_FIELD_LABELS = [
    ("social_instagram", "Instagram"),
    ("social_facebook", "Facebook"),
    ("social_twitter", "Twitter"),
    ("social_tiktok", "TikTok"),
    ("social_youtube", "YouTube"),
    ("social_spotify", "Spotify"),
    ("social_soundcloud", "SoundCloud"),
    ("social_bandcamp", "Bandcamp"),
    ("social_linkedin", "LinkedIn"),
    ("social_mastodon", "Mastodon"),
    ("website_url", "Website"),
]

CONTACT_BLOCK_FIELDS = [
    ("address", "Address"),
    ("phone", "Phone"),
    ("email", "Email"),
    ("website", "Website"),
]

CONTACT_BLOCK_SOCIALS = [
    ("facebook", "Facebook"),
    ("instagram", "Instagram"),
    ("twitter", "Twitter"),
    ("tiktok", "TikTok"),
    ("youtube", "YouTube"),
    ("spotify", "Spotify"),
    ("soundcloud", "SoundCloud"),
    ("bandcamp", "Bandcamp"),
    ("linkedin", "LinkedIn"),
    ("mastodon", "Mastodon"),
]

CONTACT_ICON_FILES = {
    "address": "icons/home.svg",
    "phone": "icons/phone.svg",
    "email": "icons/email.svg",
    "website": "icons/globe.svg",
}

SOCIAL_ICON_FILES = {
    "facebook": "icons/facebook.svg",
    "instagram": "icons/instagram.svg",
    "twitter": "icons/twitter.svg",
    "tiktok": "icons/tiktok.svg",
    "youtube": "icons/youtube.svg",
    "spotify": "icons/spotify.svg",
    "soundcloud": "icons/soundcloud.svg",
    "bandcamp": "icons/bandcamp.svg",
    "linkedin": "icons/linkedin.svg",
    "mastodon": "icons/mastodon.svg",
    "website": "icons/globe.svg",
}


def _format_address(settings: SiteSettings) -> str:
    lines: list[str] = []
    street = " ".join(filter(None, [settings.address_street, settings.address_number])).strip()
    if street:
        lines.append(street)
    city_line = " ".join(
        filter(
            None,
            [
                settings.address_postal_code,
                settings.address_city,
                settings.address_state,
            ],
        )
    ).strip()
    if city_line:
        lines.append(city_line)
    if settings.address_country:
        lines.append(settings.address_country)
    return "\n".join(lines)


def _social_icon_for(*values: str | None) -> str | None:
    for raw in values:
        if not raw:
            continue
        slug = re.sub(r"[^a-z0-9]+", "", raw.lower())
        if slug.startswith("social"):
            slug = slug.removeprefix("social")
        if slug.endswith("url"):
            slug = slug[: -len("url")]
        if slug in SOCIAL_ICON_FILES:
            return SOCIAL_ICON_FILES[slug]
    return None


def _footer_renderer(*, context: Context, request=None) -> str:
    props = {**context["props"]}
    settings = SiteSettings.get_solo()
    site_context = data_sources.get_site_context()

    if not props.get("brand_name"):
        props["brand_name"] = settings.org_name
    if not props.get("brand_tagline") and settings.mode:
        props["brand_tagline"] = settings.get_mode_display()

    logo = props.get("brand_logo")
    if not logo and settings.logo:
        try:
            logo = settings.logo.url
        except Exception:
            logo = None
    props["brand_logo_resolved"] = _resolve_media(request, logo)

    if not props.get("address_html"):
        props["address_html"] = _format_address(settings)

    def _normalise_links(items):
        normalised = []
        for item in items or []:
            if not item:
                continue
            href = item.get("href")
            if href and request and href.startswith("/"):
                href = request.build_absolute_uri(href)
            normalised.append(
                {
                    "label": item.get("label"),
                    "display": item.get("display"),
                    "href": href,
                    "new_tab": bool(item.get("new_tab")),
                    "icon": item.get("icon"),
                }
            )
        return [item for item in normalised if item.get("label") or item.get("href")]

    if not props.get("social_links"):
        socials: list[dict] = []
        for field, label in SOCIAL_FIELD_LABELS:
            url = getattr(settings, field, "")
            if not url:
                continue
            socials.append(
                {
                    "label": label,
                    "href": url,
                    "new_tab": True,
                    "icon": _social_icon_for(field, label),
                }
            )
        props["social_links"] = socials
    else:
        provided: list[dict[str, Any]] = []
        for item in props.get("social_links") or []:
            if not item:
                continue
            icon = item.get("icon") or _social_icon_for(item.get("label"))
            provided.append({**item, "icon": icon})
        props["social_links"] = provided

    props.setdefault("show_language_switcher", True)
    props.setdefault("links_heading", "Explore")
    props.setdefault("legal_heading", "Legal")
    props.setdefault("social_heading", "Connect")

    context = {
        **context,
        "props": props,
        "links": _normalise_links(props.get("links")),
        "legal": _normalise_links(props.get("legal")),
        "social_links": _normalise_links(props.get("social_links")),
        "site": site_context,
        "enabled_languages": settings.get_enabled_languages(),
    }
    return _render_template("pages/blocks/footer.html", context, request=request)


def _gallery_renderer(*, context: Context, request=None) -> str:
    props = context["props"]
    items = props.get("items", [])
    for item in items:
        item["image_resolved"] = _resolve_media(request, item.get("image"))
    context = {**context, "items": items}
    return _render_template("pages/blocks/gallery.html", context, request=request)


def _media_carousel_renderer(*, context: Context, request=None) -> str:
    props = context["props"]
    entries, asset_ids = _prepare_asset_entries(props.get("items"))
    asset_map = data_sources.get_public_assets_by_ids(asset_ids)
    resolved: list[dict[str, Any]] = []
    for entry in entries:
        asset_id = entry["asset_id"]
        if asset_id and asset_id not in asset_map:
            continue
        asset_data = asset_map.get(asset_id) if asset_id else entry["asset_meta"]
        if not asset_data:
            continue
        url = _resolve_media(request, asset_data.get("url"))
        if not url:
            continue
        payload = entry["data"]
        resolved.append(
            {
                "id": asset_id or f"slide-{len(resolved)}",
                "url": url,
                "kind": asset_data.get("kind") or "other",
                "title": asset_data.get("title") or payload.get("caption") or "Media",
                "caption": (payload.get("caption") or "").strip(),
                "description": (payload.get("description") or "").strip(),
                "cta_label": (payload.get("cta_label") or "").strip(),
                "cta_url": (payload.get("cta_url") or "").strip(),
                "width": asset_data.get("width"),
                "height": asset_data.get("height"),
            }
        )
    try:
        interval = int(props.get("autoplay_interval") or 6)
        interval = max(3, min(interval, 60))
    except (TypeError, ValueError):
        interval = 6
    carousel_id = _block_element_id(context.get("block"), "carousel")
    context = {
        **context,
        "items": resolved,
        "carousel_id": carousel_id,
        "autoplay": bool(props.get("autoplay")),
        "autoplay_interval": interval,
        "show_thumbnails": bool(props.get("show_thumbnails", True)),
    }
    return _render_template("pages/blocks/media_carousel.html", context, request=request)


def _media_player_renderer(*, context: Context, request=None) -> str:
    props = context["props"]
    entries, asset_ids = _prepare_asset_entries(props.get("items"))
    asset_map = data_sources.get_public_assets_by_ids(asset_ids)
    resolved: list[dict[str, Any]] = []
    for entry in entries:
        asset_id = entry["asset_id"]
        if asset_id and asset_id not in asset_map:
            continue
        asset_data = asset_map.get(asset_id) if asset_id else entry["asset_meta"]
        if not asset_data:
            continue
        url = _resolve_media(request, asset_data.get("url"))
        if not url:
            continue
        payload = entry["data"]
        kind = asset_data.get("kind") or "other"
        resolved.append(
            {
                "id": asset_id or f"media-{len(resolved)}",
                "url": url,
                "kind": kind,
                "kind_label": kind.capitalize(),
                "display_title": (payload.get("title") or asset_data.get("title") or "Media").strip(),
                "description": (payload.get("description") or asset_data.get("description") or "").strip(),
                "size_label": _format_file_size(asset_data.get("size_bytes")),
                "duration_label": _format_duration(asset_data.get("duration_seconds")),
            }
        )
    layout = props.get("layout") if props.get("layout") in {"grid", "list"} else "list"
    context = {
        **context,
        "items": resolved,
        "layout": layout,
        "show_downloads": bool(props.get("show_downloads")),
    }
    return _render_template("pages/blocks/media_player.html", context, request=request)


def _download_list_renderer(*, context: Context, request=None) -> str:
    props = context["props"]
    entries, asset_ids = _prepare_asset_entries(props.get("items"))
    asset_map = data_sources.get_public_assets_by_ids(asset_ids)
    resolved: list[dict[str, Any]] = []
    for entry in entries:
        asset_id = entry["asset_id"]
        if asset_id and asset_id not in asset_map:
            continue
        asset_data = asset_map.get(asset_id) if asset_id else entry["asset_meta"]
        if not asset_data:
            continue
        url = _resolve_media(request, asset_data.get("url"))
        if not url:
            continue
        payload = entry["data"]
        label = (payload.get("label") or asset_data.get("title") or "Download").strip()
        resolved.append(
            {
                "id": asset_id or f"download-{len(resolved)}",
                "url": url,
                "kind": asset_data.get("kind") or "other",
                "label": label or "Download",
                "description": (payload.get("description") or asset_data.get("description") or "").strip(),
                "size_label": _format_file_size(asset_data.get("size_bytes")),
                "duration_label": _format_duration(asset_data.get("duration_seconds")),
                "button_label": (payload.get("button_label") or "Download").strip() or "Download",
                "mime_type": asset_data.get("mime_type"),
                "width": asset_data.get("width"),
                "height": asset_data.get("height"),
            }
        )
    context = {
        **context,
        "items": resolved,
        "show_icons": bool(props.get("show_icons", True)),
    }
    return _render_template("pages/blocks/download_list.html", context, request=request)


def _inventory_renderer(*, context: Context, request=None) -> str:
    props = context["props"]
    categories = props.get("category_slugs")
    if isinstance(categories, str):
        categories = [slug.strip() for slug in categories.split(",") if slug.strip()]
    items = data_sources.get_public_inventory(categories)
    context = {**context, "items": items, "props": props}
    return _render_template("pages/blocks/inventory.html", context, request=request)


def _map_renderer(*, context: Context, request=None) -> str:
    props = context["props"]
    auto_location = props.get("auto_location", True)
    latitude = props.get("latitude")
    longitude = props.get("longitude")
    lat_value: float | None
    lon_value: float | None
    try:
        lat_value = float(latitude) if latitude not in (None, "") else None
    except (TypeError, ValueError):
        lat_value = None
    try:
        lon_value = float(longitude) if longitude not in (None, "") else None
    except (TypeError, ValueError):
        lon_value = None
    try:
        zoom = int(props.get("zoom") or 15)
    except (TypeError, ValueError):
        zoom = 15
    block = context.get("block") or {}
    map_id = f"page-map-{block.get('id', 'map')}"
    site = data_sources.get_site_context()
    address_override = (props.get("address_override") or "").strip()
    if address_override:
        search_address = address_override
    else:
        addr = site.get("address") or {}
        parts = []
        line1 = " ".join(filter(None, [addr.get("street"), addr.get("number")])).strip()
        if line1:
            parts.append(line1)
        line2 = " ".join(filter(None, [addr.get("postal_code"), addr.get("city")])).strip()
        if line2:
            parts.append(line2)
        if addr.get("country"):
            parts.append(addr.get("country"))
        search_address = ", ".join(parts)

    def _clean_items(values):
        cleaned: list[dict[str, str]] = []
        for item in values or []:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or "").strip()
            details = str(item.get("details") or "").strip()
            if not label and not details:
                continue
            cleaned.append({"label": label, "details": details})
        return cleaned

    structured_data_list = context.get("structured_data")
    if isinstance(structured_data_list, list):
        map_url = None
        page_url = context.get("page_url")
        if page_url:
            map_url = f"{page_url}#{map_id}"
        place_payload = build_map_structured_data(
            site_context=site,
            address_override=address_override or None,
            latitude=lat_value,
            longitude=lon_value,
            map_url=map_url,
        )
        if place_payload:
            structured_data_list.append(place_payload)
    context = {
        **context,
        "map_id": map_id,
        "latitude": lat_value,
        "longitude": lon_value,
        "zoom": zoom,
        "transport_items": _clean_items(props.get("transport_items")),
        "parking_items": _clean_items(props.get("parking_items")),
        "auto_location": bool(auto_location),
        "address_search": search_address,
    }
    return _render_template("pages/blocks/map.html", context, request=request)


def _list_theme_media(subdir: str) -> list[dict[str, str]]:
    media_root = getattr(settings, "MEDIA_ROOT", "")
    media_url = getattr(settings, "MEDIA_URL", "")
    if not media_root or not media_url:
        return []
    directory = Path(media_root) / subdir
    if not directory.exists():
        return []
    options: list[dict[str, str]] = []
    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        slug = slugify(path.stem) or path.stem
        url = f"{media_url.rstrip('/')}/{subdir.strip('/')}/{path.name}"
        label = path.stem.replace("_", " ").title()
        options.append({"value": f"{subdir}-{slug}", "label": label, "url": url})
    return options


def _navigation_renderer(*, context: Context, request=None) -> str:
    props = context["props"]
    from .navigation import build_nav_payload, get_navigation_entries, serialize_nav_entries

    if props.get("enabled") is False:
        return ""
    site = data_sources.get_site_context()
    logo_source = props.get("logo_image") or site.get("logo")
    logo = _resolve_media(request, logo_source)
    override_links = props.get("links")
    context_override = context.get("nav_override") or []
    if isinstance(override_links, list) and any(override_links):
        nav_entries = build_nav_payload(override_links)
    elif context_override:
        nav_entries = build_nav_payload(context_override)
    else:
        nav_entries = serialize_nav_entries(get_navigation_entries())
    enabled_languages = SiteSettings.get_solo().get_enabled_languages()
    context = {
        **context,
        "props": props,
        "site": site,
        "logo": logo,
        "nav_items": nav_entries,
        "enabled_languages": enabled_languages,
        "theme_backgrounds": _list_theme_media("bg-images"),
        "theme_textures": _list_theme_media("textures"),
    }
    return _render_template("pages/blocks/navigation.html", context, request=request)


BLOCK_RENDERERS = {
    "hero": _hero_renderer,
    "rich_text": _rich_text_renderer,
    "events": _events_renderer,
    "events_compact": _events_compact_renderer,
    "events_archive": _events_archive_renderer,
    "recurring_events": _recurring_events_renderer,
    "news_latest": _news_latest_renderer,
    "news_archive": _news_archive_renderer,
    "menu": _menu_renderer,
    "opening_hours": _opening_hours_renderer,
    "contact": _contact_renderer,
    "footer": _footer_renderer,
    "gallery": _gallery_renderer,
    "media_carousel": _media_carousel_renderer,
    "media_player": _media_player_renderer,
    "download_list": _download_list_renderer,
    "inventory": _inventory_renderer,
    "navigation": _navigation_renderer,
    "map": _map_renderer,
}
