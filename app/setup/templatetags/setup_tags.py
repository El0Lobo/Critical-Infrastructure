# app/setup/templatetags/setup_tags.py
from django import template
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.safestring import mark_safe

from app.setup.helpers import get_settings, is_allowed

register = template.Library()


def _ensure_roles_link():
    return reverse("setup:setup") + "#roles"


def _visibility_picker_url():
    return reverse("setup:visibility_picker")


def _visibility_edit_url(key, label):
    return reverse("setup:visibility_edit") + f"?key={key}&label={label}"


@register.simple_tag(takes_context=True)
def visibility_cog(context, key, label=""):
    """
    Legacy link-style cog (opens the full visibility page).
    """
    request = context.get("request")
    if not request or not request.user.is_superuser:
        return ""
    if not Group.objects.exists():
        link = _ensure_roles_link()
        html = f'<a class="cfg-cog muted" href="{link}" title="Define roles first">⚙️</a>'
        return mark_safe(html)
    url = _visibility_edit_url(key, label)
    html = f'<a class="cfg-cog" href="{url}" title="Visibility for {key}">⚙️</a>'
    return mark_safe(html)


@register.simple_tag(takes_context=True)
def visibility_cog_inline(context, key, label="", target=".nav-inline"):
    """
    Inline button that spawns the popover picker via HTMX.
    """
    request = context.get("request")
    if not request or not request.user.is_superuser:
        return ""
    if not Group.objects.exists():
        link = _ensure_roles_link()
        html = (
            f'<span class="cfg-cog muted" title="Define roles first" '
            f'role="button" tabindex="0" onclick="window.location.href=\'{link}\'">⚙️</span>'
        )
        return mark_safe(html)

    url = _visibility_picker_url()
    html = (
        f'<span class="cfg-cog" title="Visibility for {key}" '
        f'role="button" tabindex="0" '
        f'hx-get="{url}?key={key}&label={label}" '
        f'hx-trigger="click consume" '
        f'hx-target="closest {target}" '
        f'hx-swap="beforeend">⚙️</span>'
    )
    return mark_safe(html)


@register.filter
def allow_for(user, key):
    return is_allowed(user, key)


@register.simple_tag
def site_settings():
    return get_settings()
