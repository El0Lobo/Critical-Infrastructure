from django.contrib import admin
from django.utils.html import format_html

from .models import Band


@admin.register(Band)
class BandAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "performer_type",
        "last_performed_on",
        "compensation_type",
        "is_published",
        "updated_at",
    )
    list_filter = ("performer_type", "compensation_type", "is_published")
    search_fields = ("name", "description", "contact_value", "contact_notes")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("preview_photo",)

    fieldsets = (
        (
            "Identity",
            {
                "fields": (
                "performer_type",
                "name",
                "slug",  # auto-filled, not shown in CMS form
                "description",
                "genre",
                "photo",
                "preview_photo",
                )
            },
        ),
        (
            "Performance",
            {
                "fields": ("last_performed_on",),
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "contact_type",
                    "contact_value",
                    "contact_notes",
                    "website",
                    "instagram",
                    "facebook",
                    "youtube",
                    "bandcamp",
                    "soundcloud",
                )
            },
        ),
        (
            "Compensation (internal only)",
            {
                "fields": ("compensation_type", "fee_amount", "entry_price", "payout_amount"),
                "description": "Stored for records only; not shown on public pages or CMS index.",
            },
        ),
        (
            "Publication",
            {
                "fields": ("is_published", "published_at"),
            },
        ),
        (
            "SEO (auto-filled, can override)",
            {
                "fields": ("seo_title", "seo_description", "og_image_override"),
            },
        ),
        (
            "Internal Notes",
            {
                "fields": ("comment_internal",),
            },
        ),
    )

    def preview_photo(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-width:200px;border-radius:6px;" />',
                obj.photo.url,
            )
        return "—"

    preview_photo.short_description = "Preview"
