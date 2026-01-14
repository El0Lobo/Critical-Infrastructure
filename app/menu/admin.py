# app/menu/admin.py
from django.contrib import admin

from .models import Category, Item, ItemVariant, Unit


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("code", "display", "kind")
    list_filter = ("kind",)
    search_fields = ("code", "display")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "kind",
        "parent",
        "slug",
    )
    list_filter = ("kind",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class ItemVariantInline(admin.TabularInline):
    model = ItemVariant
    extra = 1


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "visible_public",
        "featured",
        "sold_out_until",
        "new_until",
        "slug",
    )
    list_filter = ("visible_public", "featured", "category__kind")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ItemVariantInline]
