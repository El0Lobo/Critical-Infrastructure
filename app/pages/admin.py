from django.contrib import admin

from .models import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "status", "is_visible", "show_navigation_bar", "updated_at")
    list_filter = ("status", "is_visible", "show_navigation_bar")
    search_fields = ("title", "slug", "summary", "body")
    ordering = ("navigation_order", "title")
    readonly_fields = ("created_at", "updated_at", "published_at")
    prepopulated_fields = {"slug": ("title",)}
