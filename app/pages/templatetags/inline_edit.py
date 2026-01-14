from __future__ import annotations

from django import template
from django.utils.safestring import mark_safe

from app.pages.utils_inline import sanitize_inline_html

register = template.Library()


def _block_id(block) -> str:
    if isinstance(block, dict):
        return block.get("id") or ""
    return getattr(block, "id", "") or ""


@register.simple_tag
def inline_attrs(block, field):
    block_id = _block_id(block)
    if not block_id:
        return ""
    return mark_safe(
        f'data-inline-block="{block_id}" data-inline-field="{field}" role="textbox" aria-label="{field}"'
    )


@register.simple_tag
def inline_image_attrs(block, field):
    """Attach inline metadata so builder JS can expose resize handles."""

    block_id = _block_id(block)
    if not block_id:
        return ""
    return mark_safe(
        f'data-inline-block="{block_id}" data-inline-image="{field}" aria-label="{field}"'
    )


@register.filter
def inline_richtext(value):
    if not value:
        return ""
    normalized = str(value).replace("\r\n", "\n").replace("\n", "<br>")
    return mark_safe(sanitize_inline_html(normalized))
