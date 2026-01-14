from __future__ import annotations

import json
from types import SimpleNamespace

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import LoginView
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.views.decorators.http import require_POST

from app.setup.models import SiteSettings

from . import data_sources
from .models import Page
from .navigation import build_nav_payload
from .structured_data import build_base_structured_data


def _public_enabled_or_404() -> SiteSettings:
    settings_obj = SiteSettings.get_solo()
    if not settings_obj.public_pages_enabled:
        raise Http404("Public site is disabled.")
    return settings_obj


def _published_queryset():
    return Page.objects.filter(status=Page.Status.PUBLISHED, is_visible=True)


def _nav_payload_for(page: Page):
    """
    Get navigation entries for the given page.
    If custom_nav_items is set, use those slugs.
    Otherwise, show all visible published pages.
    """
    if not page.show_navigation_bar:
        return []

    # If custom nav items are specified, use them
    override = [slug for slug in (page.custom_nav_items or []) if slug]
    if override:
        return build_nav_payload(override)

    # Otherwise, return all visible pages as navigation
    from .navigation import get_navigation_entries, serialize_nav_entries

    entries = get_navigation_entries(include_hidden=False)
    return serialize_nav_entries(entries)


def _render_page(request, page: Page) -> HttpResponse:
    rendered, footer, nav_html, block_structured_data = page.render_content_segments(request=request)
    nav_entries = _nav_payload_for(page)
    site_context = data_sources.get_site_context()
    structured_payloads = block_structured_data + build_base_structured_data(
        page=page, request=request, site_context=site_context
    )
    structured_data = [
        json.dumps(item, ensure_ascii=False, separators=(",", ":"))
        for item in structured_payloads
        if item
    ]
    context = {
        "page": page,
        "page_rendered": rendered,
        "page_footer": footer,
        "nav_label": page.title,
        "public_pages": nav_entries,
        "page_show_nav": bool(nav_entries),
        "navigation_html": nav_html,
        "page_theme_css": page.get_theme_css(),
        "page_custom_css": page.custom_css,
        "page_custom_js": page.custom_js,
        "structured_data": structured_data,
    }
    return render(request, "public/page_detail.html", context)


def _first_available_page():
    """
    Get the home page, using navigation_order to identify it language-agnostically.
    The home page is marked with navigation_order=0.
    """
    qs = _published_queryset()
    # Look for the page with navigation_order=0 (home page)
    home = qs.filter(navigation_order=0).first()
    if home:
        return home
    # Fall back to first page by order
    return qs.order_by("navigation_order", "title").first()


def home(request):
    """
    Render the home page. Always renders directly without redirect to support
    multilingual URLs (en/home, de/startseite, fr/accueil, etc.).
    """
    _public_enabled_or_404()
    page = _first_available_page()
    if not page:
        return render(
            request,
            "public/empty_site.html",
            {
                "page_show_nav": False,
                "page_footer": "",
                "page": SimpleNamespace(custom_css="", custom_js=""),
                "page_custom_css": "",
                "page_custom_js": "",
            },
            status=404,
        )
    # Render the home page directly (no redirect)
    return _render_page(request, page)


def page_detail(request, slug):
    _public_enabled_or_404()
    page = get_object_or_404(_published_queryset(), slug=slug)
    return _render_page(request, page)


class CMSLoginView(LoginView):
    template_name = "registration/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Find login page by checking all language-specific slug fields
        # This supports login, iniciar-sesion, anmelden, connexion across languages
        from django.db.models import Q

        page = Page.objects.filter(
            Q(slug_en="login")
            | Q(slug_es="iniciar-sesion")
            | Q(slug_de="anmelden")
            | Q(slug_fr="connexion"),
            status=Page.Status.PUBLISHED,
            is_visible=True,
        ).first()
        if page:
            context["page"] = page
            main_html, footer_html, nav_html, _ = page.render_content_segments(request=self.request)
            context["page_rendered"] = main_html
            context["page_footer"] = footer_html
            if page.show_navigation_bar:
                nav_payload = build_nav_payload(page.custom_nav_items or [])
            else:
                nav_payload = []
            context["public_pages"] = nav_payload
            context["page_show_nav"] = bool(nav_payload)
            context["nav_label"] = page.title
            context["navigation_html"] = nav_html
            context["page_theme_css"] = page.get_theme_css()
            context["page_custom_css"] = page.custom_css
            context["page_custom_js"] = page.custom_js
        else:
            context.setdefault("page", SimpleNamespace(custom_css="", custom_js=""))
            context.setdefault("public_pages", [])
            context.setdefault("page_show_nav", False)
            context.setdefault("nav_label", "Login")
            context["page_rendered"] = ""
            context["page_footer"] = ""
            context.setdefault("page_theme_css", "")
            context.setdefault("page_custom_css", "")
            context.setdefault("page_custom_js", "")
        try:
            context["password_reset_url"] = reverse("password_reset")
        except NoReverseMatch:
            context["password_reset_url"] = None

        site_settings = SiteSettings.get_solo()
        context["show_dev_login"] = (
            settings.ENV in ("development", "test") and site_settings.dev_login_enabled
        )

        return context


@require_POST
def dev_force_login(request):
    """
    Force login as admin user in development mode.
    Only available when DJANGO_ENV=development or test.
    """
    # Security check: only allow in development/test environments
    settings_obj = SiteSettings.get_solo()
    if settings.ENV not in ("development", "test") or not settings_obj.dev_login_enabled:
        messages.error(request, "Dev login is only available in development mode.")
        return redirect("login")

    User = get_user_model()
    admin_user = User.objects.filter(username="admin", is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser("admin", "admin@example.com", "admin123")
    elif admin_user.username == "admin":
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.set_password("admin123")
        admin_user.save(update_fields=["is_superuser", "is_staff", "password"])
        profile = getattr(admin_user, "profile", None)
        if profile and not profile.email:
            profile.email = "admin@example.com"
            profile.save(update_fields=["email"])

    if admin_user:
        # Force login
        login(request, admin_user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, f"Logged in as {admin_user.username} (dev mode)")
        # Redirect to CMS dashboard
        return redirect("/cms/dashboard/")
    else:
        messages.error(request, "No admin user found. Run: python manage.py create_dev_admin")
        return redirect("login")
