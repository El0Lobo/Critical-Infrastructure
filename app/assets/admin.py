# app/assets/admin.py
from django.contrib import admin

from .models import Asset, Collection, Tag


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "visibility_mode", "parent", "sort_order", "updated_at")
    list_filter = ("visibility_mode", "parent", "tags", "allowed_groups")
    search_fields = ("title", "slug", "description")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("parent__id", "sort_order", "title")
    filter_horizontal = ("tags", "allowed_groups")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "collection",
        "kind",
        "effective_visibility",
        "is_external",
        "updated_at",
    )
    list_filter = ("kind", "visibility", "collection", "tags")
    search_fields = ("title", "slug", "description", "file", "url", "text_content")
    autocomplete_fields = ("collection", "tags")
    readonly_fields = ("created_at", "updated_at", "mime_type", "kind", "size_bytes")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "collection",
                    "visibility",
                    "description",
                    "tags",
                    "appears_on",
                )
            },
        ),
        ("Source", {"fields": ("file", "url", "text_content")}),
        (
            "Detected",
            {
                "fields": (
                    "mime_type",
                    "kind",
                    "size_bytes",
                    "width",
                    "height",
                    "duration_seconds",
                    "pages",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def effective_visibility(self, obj):
        return obj.effective_visibility

    effective_visibility.short_description = "Visibility"
