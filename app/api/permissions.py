"""DRF permission classes for the API app."""

from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission

from app.assets.selectors import user_allowed_for


class CanAddAsset(BasePermission):
    """Permission class for creating new assets."""

    def has_permission(self, request, view):
        """Check if user can add assets."""
        if request.method == "POST":
            return user_allowed_for(request.user, "cms.assets.add_asset")
        return True


class CanModifyAsset(BasePermission):
    """Permission class for updating and deleting assets."""

    def has_object_permission(self, request, view, obj):
        """Check if user can modify this specific asset."""
        if request.method in SAFE_METHODS:
            # Read permissions are checked at queryset level via filter_assets_for_user
            return True
        # Write/delete permissions
        return user_allowed_for(request.user, f"cms.assets.asset.{obj.id}.actions")


class CanAddCollection(BasePermission):
    """Permission class for creating new collections."""

    def has_permission(self, request, view):
        """Check if user can add collections."""
        if request.method == "POST":
            return user_allowed_for(request.user, "cms.assets.add_collection")
        return True


class CanModifyCollection(BasePermission):
    """Permission class for updating and deleting collections."""

    def has_object_permission(self, request, view, obj):
        """Check if user can modify this specific collection."""
        if request.method in SAFE_METHODS:
            # Read permissions are checked at queryset level via filter_collections_for_user
            return True
        # Write/delete permissions
        return user_allowed_for(request.user, f"cms.assets.collection.{obj.id}.actions")
