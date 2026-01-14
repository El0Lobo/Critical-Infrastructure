from __future__ import annotations

import json
from typing import Any

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST

from app.assets.models import Asset, Collection
from app.assets.selectors import filter_assets_for_user, asset_base_queryset

from . import data_sources
from .blocks import normalise_theme
from .models import Page
from .navigation import build_nav_payload
from .serializers import serialize_page
from .utils import get_page_or_404_any_language


def _absolute_media(request, url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return request.build_absolute_uri(url)


@login_required
def events_feed(request):
    limit = int(request.GET.get("limit", 6))
    include_internal = request.GET.get("include_internal") == "1"
    events = data_sources.get_events(limit=limit, include_internal=include_internal)
    # Upgrade media URLs to absolute paths for API consumers
    for event in events:
        event["hero_image"] = _absolute_media(request, event.get("hero_image"))
        event["url"] = request.build_absolute_uri(event["url"]) if event.get("url") else None
    return JsonResponse({"events": events})


@login_required
def menu_snapshot(request):
    slugs = request.GET.getlist("slug") or None
    categories = data_sources.get_menu_structure(slugs)
    return JsonResponse({"categories": categories})


@login_required
def site_context(request):
    data: dict[str, Any] = data_sources.get_site_context()
    data["logo"] = _absolute_media(request, data.get("logo"))
    return JsonResponse(data)


@login_required
def assets_library(request):
    kinds = request.GET.getlist("kind") or None
    qs = filter_assets_for_user(asset_base_queryset(), request.user).select_related("collection")
    if kinds:
        qs = qs.filter(kind__in=kinds)

    payload: list[dict[str, Any]] = []
    for asset in qs:
        url = asset.file.url if asset.file else asset.url
        if not url:
            continue
        payload.append(
            {
                "id": asset.pk,
                "title": asset.title,
                "slug": asset.slug,
                "kind": asset.kind,
                "description": asset.description,
                "url": _absolute_media(request, url),
                "mime_type": asset.mime_type,
                "size_bytes": asset.size_bytes,
                "width": asset.width,
                "height": asset.height,
                "duration_seconds": asset.duration_seconds,
                "collection": {
                    "id": asset.collection.pk if asset.collection_id else None,
                    "title": asset.collection.title if asset.collection_id else None,
                },
                "effective_visibility": asset.effective_visibility,
                "is_external": asset.is_external,
                "external_domain": asset.external_domain,
            }
        )
    return JsonResponse({"assets": payload})


def _get_or_create_font_collection() -> Collection:
    collection, created = Collection.objects.get_or_create(
        slug="fonts",
        defaults={"title": "Fonts", "visibility_mode": "public"},
    )
    if created:
        return collection
    if collection.visibility_mode != "public":
        collection.visibility_mode = "public"
        collection.save(update_fields=["visibility_mode"])
    return collection


def _get_or_create_builder_collection() -> Collection:
    collection, created = Collection.objects.get_or_create(
        slug="page-builder",
        defaults={"title": "Page Builder uploads", "visibility_mode": "public"},
    )
    if created:
        return collection
    if collection.visibility_mode != "public":
        collection.visibility_mode = "public"
        collection.save(update_fields=["visibility_mode"])
    return collection


@login_required
@require_POST
def upload_font_asset(request):
    if not request.user.has_perm("assets.add_asset"):
        return HttpResponseForbidden("Not allowed to upload assets.")
    upload = request.FILES.get("file")
    if not upload:
        return HttpResponseBadRequest("Missing font file.")
    filename = (upload.name or "font").lower()
    if not filename.endswith((".woff2", ".woff", ".ttf", ".otf")):
        return HttpResponseBadRequest("Only WOFF2/WOFF/TTF/OTF files are supported.")
    collection = _get_or_create_font_collection()
    title = request.POST.get("title") or upload.name or "Font"
    asset = Asset(
        collection=collection,
        title=title,
        visibility="public",
        appears_on="page-builder-fonts",
    )
    asset.file = upload
    asset.save()
    data = {
        "id": asset.pk,
        "title": asset.title,
        "slug": asset.slug,
        "kind": asset.kind,
        "url": asset.file.url if asset.file else asset.url,
        "mime_type": asset.mime_type,
    }
    return JsonResponse({"asset": data}, status=201)


@login_required
@require_POST
def upload_inline_asset(request):
    if not request.user.has_perm("assets.add_asset"):
        return HttpResponseForbidden("Not allowed to upload assets.")
    upload = request.FILES.get("file")
    if not upload:
        return HttpResponseBadRequest("Missing file.")
    collection = _get_or_create_builder_collection()
    asset = Asset(
        collection=collection,
        title=request.POST.get("title") or upload.name or "Upload",
        visibility="public",
        appears_on="page-builder-inline",
    )
    asset.file = upload
    asset.save()
    data = {
        "id": asset.pk,
        "title": asset.title,
        "slug": asset.slug,
        "kind": asset.kind,
        "url": _absolute_media(request, asset.file.url if asset.file else asset.url),
        "mime_type": asset.mime_type,
    }
    return JsonResponse({"asset": data}, status=201)


def _parse_json(request) -> dict[str, Any]:
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON payload") from exc
    if not isinstance(payload, dict):
        raise ValueError("JSON payload must be an object")
    return payload


def _normalise_blocks(raw):
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    raise ValueError("blocks must be an array")


def _apply_page_payload(page: Page, data: dict[str, Any], *, user) -> None:
    simple_fields = [
        "title",
        "summary",
        "status",
        "navigation_order",
        "body",
        "render_body_only",
    ]
    for field in simple_fields:
        if field in data:
            setattr(page, field, data[field])

    bool_fields = ["is_visible", "show_navigation_bar", "render_body_only"]
    for field in bool_fields:
        if field in data:
            setattr(page, field, bool(data[field]))

    if "slug" in data:
        slug_value = data["slug"]
        page.slug = slugify(slug_value) or (
            slugify(page.title) if page.title else page.slug or "page"
        )

    if "blocks" in data:
        page.blocks = _normalise_blocks(data["blocks"])

    if "theme" in data:
        page.theme = normalise_theme(data["theme"])

    if "navigation_order" in data:
        try:
            page.navigation_order = int(data["navigation_order"])
        except (TypeError, ValueError):
            page.navigation_order = 0

    if "custom_nav_items" in data:
        nav_items = data["custom_nav_items"]
        if not isinstance(nav_items, list):
            raise ValueError("custom_nav_items must be an array")
        cleaned = []
        for slug in nav_items:
            if not isinstance(slug, str):
                continue
            slug_norm = slugify(slug) or slug.strip()
            if slug_norm and slug_norm not in cleaned:
                cleaned.append(slug_norm)
        page.custom_nav_items = cleaned

    if page.status == Page.Status.PUBLISHED and not page.published_at:
        page.published_at = timezone.now()
    elif page.status != Page.Status.PUBLISHED:
        page.published_at = None

    page.updated_by = user
    if page.pk is None:
        page.created_by = user


@login_required
@require_http_methods(["GET", "PATCH"])
def page_detail(request, slug):
    page = get_page_or_404_any_language(slug)
    if request.method == "GET":
        return JsonResponse(serialize_page(page, request))

    try:
        payload = _parse_json(request)
    except ValueError as exc:
        return HttpResponseBadRequest(str(exc))

    try:
        _apply_page_payload(page, payload, user=request.user)
    except ValueError as exc:
        return HttpResponseBadRequest(str(exc))

    try:
        page.save()
    except Exception as exc:  # pragma: no cover - database constraint errors
        return HttpResponseBadRequest(str(exc))
    return JsonResponse(serialize_page(page, request))


@login_required
@require_http_methods(["POST"])
def page_create(request):
    try:
        payload = _parse_json(request)
    except ValueError as exc:
        return HttpResponseBadRequest(str(exc))

    page = Page()
    try:
        _apply_page_payload(page, payload, user=request.user)
        page.save()
    except ValueError as exc:
        return HttpResponseBadRequest(str(exc))
    except Exception as exc:  # pragma: no cover
        return HttpResponseBadRequest(str(exc))
    return JsonResponse(serialize_page(page, request), status=201)


@login_required
@require_http_methods(["POST"])
def preview_html(request):
    try:
        payload = _parse_json(request)
    except ValueError as exc:
        return HttpResponseBadRequest(str(exc))

    blocks = payload.get("blocks") or []
    try:
        blocks = _normalise_blocks(blocks)
    except ValueError as exc:
        return HttpResponseBadRequest(str(exc))

    nav_override = payload.get("custom_nav_items")
    if not isinstance(nav_override, list):
        nav_override = []

    preview_page = Page(
        title=payload.get("title") or payload.get("page", {}).get("title") or "Preview",
        slug=slugify(payload.get("slug") or payload.get("page", {}).get("slug") or "preview"),
        body=payload.get("body") or "",
        blocks=blocks,
        theme=normalise_theme(payload.get("theme") or payload.get("page", {}).get("theme") or {}),
        status=payload.get("status") or Page.Status.DRAFT,
        is_visible=True,
        show_navigation_bar=payload.get("show_navigation_bar", True),
        render_body_only=payload.get("render_body_only", False),
        custom_nav_items=nav_override,
        custom_css=payload.get("custom_css") or "",
        custom_js=payload.get("custom_js") or "",
    )

    main_html, footer_html, nav_html, _ = preview_page.render_content_segments(
        request=request,
        extra_context={"preview": True, "nav_override": nav_override},
    )

    nav_payload = []
    if preview_page.show_navigation_bar:
        nav_payload = build_nav_payload(nav_override)
    context = {
        "page": preview_page,
        "page_rendered": main_html,
        "page_footer": footer_html,
        "navigation_html": nav_html,
        "nav_label": preview_page.title,
        "is_preview": True,
        "public_pages": nav_payload,
        "page_show_nav": bool(nav_payload),
        "page_theme_css": preview_page.get_theme_css(),
        "page_custom_css": preview_page.custom_css,
        "page_custom_js": preview_page.custom_js,
    }

    html = render_to_string("public/page_detail.html", context, request=request)
    return JsonResponse(
        {
            "html": html,
            "content_html": main_html,
            "theme_css": context.get("page_theme_css") or "",
            "custom_css": preview_page.custom_css or "",
            "custom_js": preview_page.custom_js or "",
        }
    )
