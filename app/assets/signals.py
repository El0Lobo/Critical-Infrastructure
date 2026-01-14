"""Signal handlers for asset-related models."""

from __future__ import annotations

from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from app.assets.models import Collection
from app.setup.permissions import assign_collection_permissions, sync_collection_permissions


@receiver(post_save, sender=Collection)
def collection_saved(sender, instance, created, **kwargs):
    """When a collection is created, assign permissions to allowed groups."""
    if created:
        assign_collection_permissions(instance)


@receiver(m2m_changed, sender=Collection.allowed_groups.through)
def collection_groups_changed(sender, instance, action, **kwargs):
    """When collection.allowed_groups changes, sync permissions to all assets."""
    if action in ("post_add", "post_remove", "post_clear"):
        sync_collection_permissions(instance)
