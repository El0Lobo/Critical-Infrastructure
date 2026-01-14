from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, MutableMapping
else:
    Iterable = object
    MutableMapping = object

from django.db.models import Case, CharField, F, Q, QuerySet, When

from app.setup.helpers import is_allowed
from app.setup.models import VisibilityRule

from .forms import AssetFilterForm
from .models import Asset, Collection


def asset_base_queryset() -> QuerySet[Asset]:
    return (
        Asset.objects.select_related("collection")
        .prefetch_related("tags", "collection__tags", "collection__allowed_groups")
        .annotate(
            eff_vis=Case(
                When(visibility="inherit", then=F("collection__visibility_mode")),
                default=F("visibility"),
                output_field=CharField(),
            )
        )
    )


def filter_assets_with_form(params) -> tuple[AssetFilterForm, QuerySet[Asset]]:
    qs = asset_base_queryset()
    form = AssetFilterForm(params or None)

    if form.is_valid():
        q = form.cleaned_data.get("q")
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(slug__icontains=q)
                | Q(file__icontains=q)
                | Q(url__icontains=q)
                | Q(text_content__icontains=q)
                | Q(tags__name__icontains=q)
                | Q(collection__title__icontains=q)
                | Q(collection__slug__icontains=q)
                | Q(collection__tags__name__icontains=q)
            ).distinct()

        kind = form.cleaned_data.get("kind")
        if kind:
            qs = qs.filter(kind=kind)

        visibility = form.cleaned_data.get("visibility")
        if visibility in ("public", "internal", "groups"):
            qs = qs.filter(eff_vis=visibility)

        collection = form.cleaned_data.get("collection")
        if collection:
            qs = qs.filter(collection=collection)

        tags = form.cleaned_data.get("tags")
        if tags:
            qs = qs.filter(tags__in=list(tags)).distinct()

        source = form.cleaned_data.get("source")
        if source == "local":
            qs = qs.filter(file__isnull=False)
        elif source == "external":
            qs = qs.filter(file__isnull=True, url__isnull=False)

    return form, qs


def user_group_ids(user) -> set[int]:
    if not user.is_authenticated:
        return set()
    return set(user.groups.values_list("id", flat=True))


def user_can_view_asset(user, asset: Asset) -> bool:
    vis = getattr(asset, "effective_visibility", None) or getattr(asset, "eff_vis", None)
    if not vis:
        vis = asset.visibility
        if vis == "inherit" and asset.collection_id:
            vis = asset.collection.visibility_mode

    if vis == "public":
        return True
    if not user.is_authenticated:
        return False
    if vis == "internal":
        return True
    if vis == "groups":
        if not asset.collection_id:
            return False
        user_groups = user_group_ids(user)
        allowed = set(asset.collection.allowed_groups.values_list("id", flat=True))
        return bool(user_groups & allowed)
    return False


def user_allowed_for(user, key: str) -> bool:
    if not key:
        return False
    if user.is_superuser:
        return True
    return VisibilityRule.objects.filter(key=key, is_enabled=True).exists() and is_allowed(
        user, key
    )


def _rule_allows_any(user, keys: Iterable[str | None], cache: MutableMapping[str, bool]) -> bool:
    for key in keys:
        if not key:
            continue
        if key in cache:
            if cache[key]:
                return True
            continue
        allowed = user_allowed_for(user, key)
        cache[key] = allowed
        if allowed:
            return True
    return False


def filter_assets_for_user(qs: QuerySet[Asset], user) -> QuerySet[Asset]:
    groups = user_group_ids(user)
    visibility_q = Q(eff_vis="public")
    if user.is_authenticated:
        visibility_q |= Q(eff_vis="internal")
        if groups:
            visibility_q |= Q(eff_vis="groups", collection__allowed_groups__id__in=list(groups))

    allowed_ids = set(qs.filter(visibility_q).values_list("id", flat=True))
    cache: dict[str, bool] = {}
    extra_ids: list[int] = []
    for asset in qs.exclude(id__in=allowed_ids):
        asset_keys = [
            f"assets.asset.{asset.id}",
            f"assets.collection.{asset.collection_id}" if asset.collection_id else None,
            f"cms.assets.asset.{asset.id}.actions",
            f"cms.assets.collection.{asset.collection_id}.actions" if asset.collection_id else None,
            f"cms.assets.collection.{asset.collection_id}.toolbar" if asset.collection_id else None,
        ]
        if _rule_allows_any(user, asset_keys, cache):
            extra_ids.append(asset.id)
    if not extra_ids:
        return qs.filter(id__in=allowed_ids)
    return qs.filter(Q(id__in=allowed_ids) | Q(id__in=extra_ids))


def filter_collections_for_user(qs: QuerySet[Collection], user) -> QuerySet[Collection]:
    if user.is_superuser:
        return qs

    groups = user_group_ids(user)
    cache: dict[str, bool] = {}
    allowed_ids: list[int] = []

    for col in qs:
        vis = col.visibility_mode
        can_view = False
        if vis == "public":
            can_view = True
        elif not user.is_authenticated:
            can_view = False
        elif vis == "internal":
            can_view = True
        elif vis == "groups":
            allowed = set(col.allowed_groups.values_list("id", flat=True))
            can_view = bool(groups & allowed)

        if not can_view:
            keys = [
                f"assets.collection.{col.id}",
                f"cms.assets.collection.{col.id}.actions",
                f"cms.assets.collection.{col.id}.toolbar",
            ]
            if _rule_allows_any(user, keys, cache):
                can_view = True

        if can_view:
            allowed_ids.append(col.id)

    return qs.filter(id__in=allowed_ids)
