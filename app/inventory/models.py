from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import F
from django.utils import timezone
from django.utils.text import slugify


class InventoryCategory(models.Model):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or slugify(f"cat-{timezone.now().timestamp()}")
        super().save(*args, **kwargs)


class InventoryItem(models.Model):
    KIND_INGREDIENT = "ingredient"
    KIND_SUPPLY = "supply"
    KIND_ASSET = "asset"
    KIND_PRODUCT = "product"
    KIND_CHOICES = [
        (KIND_INGREDIENT, "Ingredient"),
        (KIND_SUPPLY, "Supply"),
        (KIND_ASSET, "Asset"),
        (KIND_PRODUCT, "Product"),
    ]

    category = models.ForeignKey(
        InventoryCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name="items"
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default=KIND_SUPPLY)
    description = models.TextField(blank=True, default="")
    location = models.CharField(max_length=160, blank=True, default="")

    unit = models.ForeignKey(
        "menu.Unit", null=True, blank=True, on_delete=models.SET_NULL, related_name="inventory_items"
    )
    unit_label = models.CharField(
        max_length=32,
        blank=True,
        default="",
        help_text="Fallback label if a formal unit is not available.",
    )
    pack_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal("1.000"),
        help_text="Quantity delivered per pack (e.g., 30 for a 30L keg).",
    )
    pack_unit = models.ForeignKey(
        "menu.Unit",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inventory_pack_items",
    )

    current_stock = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0.000"))
    desired_stock = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0.000"))
    reorder_point = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0.000"))
    needs_reorder = models.BooleanField(default=False)
    auto_track_sales = models.BooleanField(
        default=False,
        help_text="When enabled, POS sales linked to this item will reduce stock automatically.",
    )

    public_visible = models.BooleanField(default=False)
    public_description = models.TextField(blank=True, default="")
    public_url = models.URLField(blank=True, default="")

    is_active = models.BooleanField(default=True)
    last_reorder_at = models.DateTimeField(null=True, blank=True)

    menu_items = models.ManyToManyField(
        "menu.Item", blank=True, related_name="inventory_links", help_text="Reference only."
    )
    merch_products = models.ManyToManyField(
        "merch.Product", blank=True, related_name="inventory_links", help_text="Reference only."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="inventory_items_created",
        on_delete=models.SET_NULL,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="inventory_items_updated",
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    @property
    def unit_display(self) -> str:
        if self.unit:
            return self.unit.display
        return self.unit_label or ""

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or slugify(f"item-{timezone.now().timestamp()}")
        super().save(*args, **kwargs)

    def sync_default_consumptions(self):
        if not self.auto_track_sales:
            return
        from app.menu.models import Item as MenuItem  # lazy import to avoid circulars

        for menu_item in self.menu_items.all():
            for variant in menu_item.variants.all():
                InventoryConsumption.objects.get_or_create(
                    inventory_item=self,
                    menu_variant=variant,
                    defaults={"quantity_per_sale": Decimal("1.000")},
                )

    def adjust_stock(self, delta: Decimal, reason: str, user=None, note: str = "", sale_item=None):
        InventoryLog.objects.create(
            inventory_item=self,
            change_amount=delta,
            reason=reason,
            note=note,
            created_by=user,
            sale_item=sale_item,
        )
        InventoryItem.objects.filter(pk=self.pk).update(current_stock=F("current_stock") + delta)
        fresh = InventoryItem.objects.get(pk=self.pk)
        if fresh.reorder_point and fresh.current_stock <= fresh.reorder_point:
            InventoryItem.objects.filter(pk=self.pk).update(needs_reorder=True)


class InventoryLog(models.Model):
    REASON_MANUAL = "manual"
    REASON_POS = "pos"
    REASON_RESTOCK = "restock"
    REASON_REORDER = "reorder_flag"
    REASON_CHOICES = [
        (REASON_MANUAL, "Manual adjustment"),
        (REASON_POS, "POS sale"),
        (REASON_RESTOCK, "Restock"),
        (REASON_REORDER, "Reorder flag"),
    ]

    inventory_item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="logs"
    )
    change_amount = models.DecimalField(max_digits=12, decimal_places=3)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    note = models.TextField(blank=True, default="")
    sale_item = models.ForeignKey(
        "pos.SaleItem", null=True, blank=True, on_delete=models.CASCADE, related_name="inventory_logs"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inventory_logs_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["inventory_item", "sale_item"],
                name="inventory_log_unique_sale",
                condition=models.Q(sale_item__isnull=False),
            )
        ]

    def __str__(self) -> str:
        return f"{self.inventory_item} {self.change_amount} ({self.reason})"


class InventoryConsumption(models.Model):
    """
    Maps menu variants to inventory usage, so POS sales can reduce stock.
    """

    inventory_item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="menu_consumptions"
    )
    menu_variant = models.ForeignKey(
        "menu.ItemVariant", on_delete=models.CASCADE, related_name="inventory_consumptions"
    )
    quantity_per_sale = models.DecimalField(max_digits=10, decimal_places=3)

    class Meta:
        unique_together = ("inventory_item", "menu_variant")
        ordering = ["menu_variant"]

    def __str__(self) -> str:
        return f"{self.menu_variant} → {self.quantity_per_sale} of {self.inventory_item}"


class InventoryPackage(models.Model):
    inventory_item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="packages"
    )
    label = models.CharField(max_length=120)
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        help_text="How many base units are contained in this package (e.g., 750 mL for a bottle, 4500 mL for a case of six).",
    )
    unit = models.ForeignKey(
        "menu.Unit",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Optional unit override for display.",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Use this package as the default suggestion when reordering.",
    )
    notes = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["label"]

    def __str__(self) -> str:
        unit = self.unit.display if self.unit else self.inventory_item.unit_display
        return f"{self.label} · {self.quantity:g} {unit}"
