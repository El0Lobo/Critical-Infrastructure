import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBase
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import translation
from django.http import Http404
from django.template.loader import render_to_string

from .forms import PageForm, PagePreviewForm
from .models import Page
from .serializers import serialize_page
from . import data_sources
from .utils import get_page_or_404_any_language


@login_required
def index(request):
    pages = (
        Page.objects.all()
        .select_related("created_by", "updated_by")
        .order_by("navigation_order", "title")
    )
    return render(
        request,
        "pages/index.html",
        {
            "pages": pages,
        },
    )


def _handle_form(request, *, instance: Page | None = None):
    language = translation.get_language() or settings.MODELTRANSLATION_DEFAULT_LANGUAGE
    form = PageForm(
        request.POST or None,
        request.FILES or None,
        instance=instance,
        language=language,
    )
    return form, language


def _nav_builder_items(form: PageForm):
    raw = form["custom_nav_items"].value()
    try:
        selected = json.loads(raw) if raw else []
    except (TypeError, json.JSONDecodeError):
        selected = []
    slug_value = form["slug"].value()
    slug_value = slugify(slug_value) if slug_value else ""
    title_value = form["title"].value() or "Current page"

    candidates = list(Page.objects.order_by("navigation_order", "title").values("slug", "title"))
    if slug_value and not any(c["slug"] == slug_value for c in candidates):
        candidates.append({"slug": slug_value, "title": title_value})

    ordered = []
    seen = set()
    for slug in selected:
        slug_norm = slugify(slug) or slug.strip()
        if slug_norm == "__login":
            slug_norm = "login"
        for cand in candidates:
            if cand["slug"] == slug_norm and slug_norm not in seen:
                ordered.append({"slug": slug_norm, "title": cand["title"], "checked": True})
                seen.add(slug_norm)
                break
    for cand in candidates:
        if cand["slug"] not in seen:
            ordered.append({"slug": cand["slug"], "title": cand["title"], "checked": False})
    return ordered


def _render_preview_html(page: Page, request) -> str:
    main_html, footer_html, nav_html, _ = page.render_content_segments(request=request)
    context = {
        "page": page,
        "nav_label": page.title,
        "is_preview": True,
        "page_rendered": main_html,
        "page_footer": footer_html,
        "navigation_html": nav_html,
        "public_pages": [],
        "page_show_nav": False,
        "page_theme_css": page.get_theme_css(),
        "page_custom_css": page.custom_css,
        "page_custom_js": page.custom_js,
    }
    return render_to_string("public/page_detail.html", context, request=request)


def _save_page(form: PageForm, request, *, language: str):
    page = form.save(commit=False)
    is_new = page.pk is None
    if is_new and not page.created_by:
        page.created_by = request.user
    page.updated_by = request.user
    if page.status == Page.Status.PUBLISHED and not page.published_at:
        page.published_at = timezone.now()
    page.save()
    form.save_m2m()
    form.instance = page
    messages.success(request, "Page saved.")
    return page


@login_required
def create(request):
    form_or_response, language = _handle_form(request)
    form = form_or_response
    if request.method == "POST" and form.is_valid():
        page = _save_page(form, request, language=language)
        return redirect("pages_edit", slug=page.slug)
    initial_preview = _render_preview_html(form.instance, request)
    can_upload_assets = request.user.has_perm("assets.add_asset")
    font_upload_url = reverse("pages_api_font_upload") if can_upload_assets else None
    asset_upload_url = reverse("pages_api_asset_upload") if can_upload_assets else None
    context = {
        "mode": "create",
        "form": form,
        "page": None,
        "preview_url": reverse("pages_preview"),
        "default_language": settings.MODELTRANSLATION_DEFAULT_LANGUAGE,
        "builder_boot": {
            "mode": "create",
            "page": {
                **serialize_page(form.instance, request),
                "blocks": form.instance.get_blocks_for_language(language),
            },
            "preview_html": initial_preview or "",
            "urls": {
                "save": reverse("pages_api_create"),
                "preview": reverse("pages_api_preview_html"),
                "events": reverse("pages_api_events"),
                "menu": reverse("pages_api_menu"),
                "site": reverse("pages_api_site"),
                "assets": reverse("pages_api_assets"),
                "font_upload": font_upload_url,
                "asset_upload": asset_upload_url,
                "detail": None,
            },
            "site_context": data_sources.get_site_context(),
            "nav_items": _nav_builder_items(form),
            "current_language": language,
            "default_language": settings.MODELTRANSLATION_DEFAULT_LANGUAGE,
        },
    }
    return render(request, "pages/form.html", context)


@login_required
def edit(request, slug):
    page = get_page_or_404_any_language(slug)
    form_or_response, language = _handle_form(request, instance=page)
    form = form_or_response
    if request.method == "POST" and form.is_valid():
        saved = _save_page(form, request, language=language)
        return redirect("pages_edit", slug=saved.slug)
    initial_preview = _render_preview_html(page, request)
    can_upload_assets = request.user.has_perm("assets.add_asset")
    font_upload_url = reverse("pages_api_font_upload") if can_upload_assets else None
    asset_upload_url = reverse("pages_api_asset_upload") if can_upload_assets else None
    context = {
        "mode": "edit",
        "form": form,
        "page": page,
        "preview_url": reverse("pages_preview"),
        "page_rendered": initial_preview,
        "default_language": settings.MODELTRANSLATION_DEFAULT_LANGUAGE,
        "builder_boot": {
            "mode": "edit",
            "page": {
                **serialize_page(page, request),
                "blocks": page.get_blocks_for_language(language),
            },
            "preview_html": initial_preview or "",
            "urls": {
                "save": reverse("pages_api_detail", args=[page.slug]),
                "preview": reverse("pages_api_preview_html"),
                "events": reverse("pages_api_events"),
                "menu": reverse("pages_api_menu"),
                "site": reverse("pages_api_site"),
                "assets": reverse("pages_api_assets"),
                "font_upload": font_upload_url,
                "asset_upload": asset_upload_url,
                "detail": reverse("pages_api_detail", args=[page.slug]),
            },
            "site_context": data_sources.get_site_context(),
            "nav_items": _nav_builder_items(form),
            "current_language": language,
            "default_language": settings.MODELTRANSLATION_DEFAULT_LANGUAGE,
        },
    }
    return render(request, "pages/form.html", context)


@login_required
@require_POST
def delete(request, slug):
    page = get_page_or_404_any_language(slug)
    page.delete()
    messages.success(request, "Page deleted.")
    return redirect("pages_index")


@login_required
@require_POST
def toggle_status(request, slug):
    page = get_page_or_404_any_language(slug)
    if page.status == Page.Status.PUBLISHED:
        page.status = Page.Status.DRAFT
        message = "Moved page to draft."
    else:
        page.status = Page.Status.PUBLISHED
        message = "Published page."
    page.updated_by = request.user
    page.save()
    messages.success(request, message)
    return redirect("pages_index")


@login_required
def login_page_redirect(request):
    page, _ = Page.objects.get_or_create(
        slug="login",
        defaults={
            "title": "Login",
            "status": Page.Status.PUBLISHED,
            "is_visible": True,
            "show_navigation_bar": False,
            "custom_nav_items": [],
            "body": (
                "<section class='card login-intro' style='max-width:520px;margin:2rem auto;'>"
                "<h2>Sign in</h2>"
                "<p>This page renders the login form automatically. Edit this page to add copy or media above the form.</p>"
                "</section>"
            ),
        },
    )
    # Reuse the edit view directly to avoid redirect loops on /login/edit/
    return edit(request, slug=page.slug)


@login_required
@require_POST
def preview(request):
    """
    Render a live preview of an in-flight page edit in a new tab/window.
    """

    language = translation.get_language() or settings.MODELTRANSLATION_DEFAULT_LANGUAGE
    form = PagePreviewForm(request.POST, request.FILES, language=language)
    if not form.is_valid():
        return render(
            request,
            "pages/preview_error.html",
            {"form": form},
            status=400,
        )

    page = form.save(commit=False)
    page.pk = None
    page.created_at = page.created_at or timezone.now()
    page.updated_at = timezone.now()
    if page.status == Page.Status.PUBLISHED and not page.published_at:
        page.published_at = timezone.now()
    try:
        if page.hero_image:
            _ = page.hero_image.url
    except Exception:
        page.hero_image = None
    rendered_main, rendered_footer, nav_html, _ = page.render_content_segments(request=request)

    return render(
        request,
        "public/page_detail.html",
        {
            "page": page,
            "nav_label": page.title,
            "is_preview": True,
            "page_rendered": rendered_main,
            "page_footer": rendered_footer,
            "navigation_html": nav_html,
            "page_theme_css": page.get_theme_css(),
        },
    )
