from django.contrib import admin

from .models import DiscountReason, Payment, POSQuickButton, Sale, SaleItem


@admin.register(POSQuickButton)
class POSQuickButtonAdmin(admin.ModelAdmin):
    list_display = ("label", "discount_type", "value", "scope", "is_active", "sort_order")
    list_filter = ("discount_type", "scope", "is_active")
    ordering = ("sort_order",)


@admin.register(DiscountReason)
class DiscountReasonAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "created_at",
        "closed_at",
        "subtotal",
        "discount_total",
        "tax_total",
        "grand_total",
    )
    list_filter = ("status", "created_at")
    inlines = [SaleItemInline, PaymentInline]
