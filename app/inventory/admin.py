from django.contrib import admin

from .models import (
    InventoryCategory,
    InventoryConsumption,
    InventoryItem,
    InventoryLog,
    InventoryPackage,
)


@admin.register(InventoryCategory)
class InventoryCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "sort_order")
    list_filter = ("parent",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


class InventoryConsumptionInline(admin.TabularInline):
    model = InventoryConsumption
    extra = 0


class InventoryPackageInline(admin.TabularInline):
    model = InventoryPackage
    extra = 1


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "current_stock", "reorder_point", "needs_reorder", "is_active")
    list_filter = ("kind", "needs_reorder", "is_active", "category")
    search_fields = ("name", "slug", "description")
    filter_horizontal = ("menu_items", "merch_products")
    inlines = [InventoryConsumptionInline, InventoryPackageInline]


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ("inventory_item", "change_amount", "reason", "created_at", "created_by")
    list_filter = ("reason", "created_at")
    search_fields = ("inventory_item__name", "note")
