# app/pos/models.py
from django.conf import settings
from django.db import models
from django.utils import timezone


class DiscountReason(models.Model):
    name = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class POSQuickButton(models.Model):
    TYPE_PERCENT = "PERCENT"
    TYPE_AMOUNT = "AMOUNT"
    TYPE_FREE = "FREE"
    TYPE_CHOICES = [(TYPE_PERCENT, "Percent"), (TYPE_AMOUNT, "Amount"), (TYPE_FREE, "Free (100%)")]
    SCOPE_ORDER = "ORDER"
    SCOPE_ITEM = "ITEM"
    SCOPE_CHOICES = [(SCOPE_ORDER, "Order"), (SCOPE_ITEM, "Item")]

    label = models.CharField(max_length=40)
    discount_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    value = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    scope = models.CharField(max_length=8, choices=SCOPE_CHOICES, default=SCOPE_ORDER)
    reason = models.ForeignKey(DiscountReason, null=True, blank=True, on_delete=models.SET_NULL)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        if self.discount_type == self.TYPE_FREE:
            v = "FREE"
        elif self.discount_type == self.TYPE_PERCENT:
            v = f"{self.value}%"
        else:
            v = f"-{self.value}"
        return f"{self.label} ({v}, {self.scope})"


class Sale(models.Model):
    STATUS_OPEN = "OPEN"
    STATUS_PAID = "PAID"
    STATUS_VOID = "VOID"
    STATUS_CHOICES = [(STATUS_OPEN, "Open"), (STATUS_PAID, "Paid"), (STATUS_VOID, "Void")]

    created_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pos_sales_opened"
    )
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="pos_sales_closed",
    )
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=STATUS_OPEN)

    order_discount_type = models.CharField(
        max_length=10, choices=POSQuickButton.TYPE_CHOICES, blank=True
    )
    order_discount_value = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    order_discount_reason = models.ForeignKey(
        DiscountReason, null=True, blank=True, on_delete=models.SET_NULL
    )

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    note = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return f"Sale #{self.pk} — {self.status}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    menu_variant = models.ForeignKey("menu.ItemVariant", on_delete=models.PROTECT)

    title_snapshot = models.CharField(max_length=160)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    discount_type = models.CharField(max_length=10, choices=POSQuickButton.TYPE_CHOICES, blank=True)
    discount_value = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    line_subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    line_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.title_snapshot} x{self.quantity}"


class Payment(models.Model):
    KIND_CASH = "CASH"
    KIND_CARD = "CARD"
    KIND_OTHER = "OTHER"
    KIND_CHOICES = [(KIND_CASH, "Cash"), (KIND_CARD, "Card"), (KIND_OTHER, "Other")]

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="payments")
    kind = models.CharField(max_length=8, choices=KIND_CHOICES, default=KIND_CASH)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    received_at = models.DateTimeField(default=timezone.now)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.kind} {self.amount} for Sale #{self.sale_id}"
