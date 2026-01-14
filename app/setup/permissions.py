"""Permission management using django-guardian for object-level permissions."""

from __future__ import annotations

from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import assign_perm, get_objects_for_user, remove_perm

from app.assets.models import Asset, Collection


def assign_asset_permissions(asset: Asset, groups: list[Group] | None = None) -> None:
    """Assign object-level permissions for an asset to specific groups.

    Args:
        asset: The asset to assign permissions for
        groups: List of groups to grant permissions to. If None, uses asset.collection.allowed_groups
    """
    if groups is None and asset.collection:
        groups = list(asset.collection.allowed_groups.all())

    if not groups:
        return

    ContentType.objects.get_for_model(Asset)

    for group in groups:
        # Grant view, change, delete permissions
        assign_perm("view_asset", group, asset)
        assign_perm("change_asset", group, asset)
        assign_perm("delete_asset", group, asset)


def assign_collection_permissions(
    collection: Collection, groups: list[Group] | None = None
) -> None:
    """Assign object-level permissions for a collection to specific groups.

    Args:
        collection: The collection to assign permissions for
        groups: List of groups to grant permissions to. If None, uses collection.allowed_groups
    """
    if groups is None:
        groups = list(collection.allowed_groups.all())

    if not groups:
        return

    for group in groups:
        assign_perm("view_collection", group, collection)
        assign_perm("change_collection", group, collection)
        assign_perm("delete_collection", group, collection)

        # Also assign permissions to all assets in this collection
        for asset in collection.assets.all():
            assign_perm("view_asset", group, asset)
            assign_perm("change_asset", group, asset)
            assign_perm("delete_asset", group, asset)


def remove_asset_permissions(asset: Asset, groups: list[Group] | None = None) -> None:
    """Remove object-level permissions for an asset from specific groups.

    Args:
        asset: The asset to remove permissions from
        groups: List of groups to remove permissions from. If None, removes from all groups.
    """
    if groups is None:
        groups = list(Group.objects.all())

    for group in groups:
        remove_perm("view_asset", group, asset)
        remove_perm("change_asset", group, asset)
        remove_perm("delete_asset", group, asset)


def get_user_assets(user, collection=None):
    """Get all assets a user has permission to view.

    Args:
        user: The user to check permissions for
        collection: Optional collection to filter by

    Returns:
        QuerySet of assets the user can view
    """
    if user.is_superuser:
        qs = Asset.objects.all()
    else:
        qs = get_objects_for_user(
            user,
            "assets.view_asset",
            klass=Asset,
            use_groups=True,
            with_superuser=False,
        )

    if collection:
        qs = qs.filter(collection=collection)

    return qs


def get_user_collections(user):
    """Get all collections a user has permission to view.

    Args:
        user: The user to check permissions for

    Returns:
        QuerySet of collections the user can view
    """
    if user.is_superuser:
        return Collection.objects.all()

    return get_objects_for_user(
        user,
        "assets.view_collection",
        klass=Collection,
        use_groups=True,
        with_superuser=False,
    )


def sync_collection_permissions(collection: Collection) -> None:
    """Sync permissions from collection to all its assets.

    This should be called when collection.allowed_groups changes.

    Args:
        collection: The collection to sync permissions for
    """
    # Remove all existing permissions
    for asset in collection.assets.all():
        remove_asset_permissions(asset)

    # Assign new permissions based on current allowed_groups
    groups = list(collection.allowed_groups.all())
    for asset in collection.assets.all():
        assign_asset_permissions(asset, groups=groups)
