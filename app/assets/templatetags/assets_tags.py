# app/assets/templatetags/assets_tags.py
from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from app.assets.models import Asset, Collection

register = template.Library()


@register.simple_tag(takes_context=True)
def render_asset(context, asset_ref, **kwargs):
    asset = None
    ref = str(asset_ref)
    if ref.isdigit():
        asset = Asset.objects.filter(pk=int(ref)).select_related("collection").first()
    elif ":" in ref:
        col_slug, a_slug = ref.split(":", 1)
        asset = (
            Asset.objects.filter(collection__slug=col_slug, slug=a_slug)
            .select_related("collection")
            .first()
        )
    else:
        asset = Asset.objects.filter(slug=ref).select_related("collection").first()

    if not asset:
        return mark_safe(f"<!-- asset not found: {asset_ref} -->")

    mode = kwargs.get("mode") or "preview"
    html = render_to_string(
        "assets/partials/block_item.html",
        {"asset": asset, "mode": mode, "request": context.get("request")},
    )
    return mark_safe(html)


@register.simple_tag(takes_context=True)
def render_collection(context, collection_slug, **kwargs):
    col = Collection.objects.filter(slug=collection_slug).first()
    if not col:
        return mark_safe(f"<!-- collection not found: {collection_slug} -->")

    limit = int(kwargs.get("limit") or 0)
    layout = kwargs.get("layout") or "grid"
    mode = kwargs.get("mode") or "preview"

    assets = (
        col.assets.all().select_related("collection").prefetch_related("tags").order_by("title")
    )
    if limit:
        assets = assets[:limit]

    html = render_to_string(
        "assets/partials/block_collection.html",
        {
            "collection": col,
            "assets": assets,
            "layout": layout,
            "mode": mode,
            "request": context.get("request"),
        },
    )
    return mark_safe(html)
