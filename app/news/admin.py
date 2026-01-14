from __future__ import annotations

from django.contrib import admin

from .models import NewsPoll, NewsPost, PollOption


@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "visibility", "published_at", "updated_at")
    search_fields = ("title", "summary", "body")
    list_filter = ("status", "visibility", "category")
    prepopulated_fields = {"slug": ("title",)}


class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 1


@admin.register(NewsPoll)
class NewsPollAdmin(admin.ModelAdmin):
    list_display = ("question", "allow_multiple", "anonymous", "opens_at", "closes_at")
    inlines = [PollOptionInline]
