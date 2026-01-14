"""Synchronize primary logo to the Assets library."""

from __future__ import annotations

import os

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile

from app.assets.models import Asset, Collection

BRANDING_COLLECTION_SLUG = "site-branding"

LOGO_SPECS = {
    "logo": {"slug": "logo-primary", "title": "Primary logo", "kind": "image"},
}


def _ensure_collection() -> Collection:
    collection, _ = Collection.objects.get_or_create(
        slug=BRANDING_COLLECTION_SLUG,
        defaults={
            "title": "Site Branding",
            "visibility_mode": "public",
            "description": "Logos uploaded via Setup.",
        },
    )
    updated = False
    if collection.title != "Site Branding":
        collection.title = "Site Branding"
        updated = True
    if collection.visibility_mode != "public":
        collection.visibility_mode = "public"
        updated = True
    if updated:
        collection.save(update_fields=["title", "visibility_mode"])
    return collection


def _content_and_name(uploaded: UploadedFile | None, stored_field):
    if uploaded:
        try:
            uploaded.seek(0)
        except Exception:
            pass
        return uploaded.read(), uploaded.name
    if stored_field:
        try:
            stored_field.open("rb")
            data = stored_field.read()
            return data, stored_field.name
        finally:
            try:
                stored_field.close()
            except Exception:  # pragma: no cover
                pass
    return None, None


def _write_asset(collection: Collection, attr: str, file_field, uploaded: UploadedFile | None = None) -> None:
    spec = LOGO_SPECS[attr]
    slug = spec["slug"]
    qs = collection.assets.filter(slug=slug)

    content, filename = _content_and_name(uploaded, file_field)
    if not content:
        qs.delete()
        return

    asset, _ = Asset.objects.get_or_create(
        collection=collection,
        slug=slug,
        defaults={
            "title": spec["title"],
            "visibility": "public",
            "kind": spec.get("kind") or "other",
            "description": "Uploaded via Setup",
        },
    )
    # Update metadata
    if asset.title != spec["title"]:
        asset.title = spec["title"]
    asset.visibility = "public"
    asset.kind = spec.get("kind") or "other"
    asset.description = "Uploaded via Setup"
    asset.save(update_fields=["title", "visibility", "kind", "description"])

    clean_name = os.path.basename(filename or "") or f"{slug}"
    asset.file.save(clean_name, ContentFile(content), save=True)


def sync_branding_assets(settings_obj, uploads: dict | None = None) -> None:
    collection = _ensure_collection()
    uploads = uploads or {}
    for attr in LOGO_SPECS:
        _write_asset(
            collection,
            attr,
            getattr(settings_obj, attr, None),
            uploads.get(attr),
        )
