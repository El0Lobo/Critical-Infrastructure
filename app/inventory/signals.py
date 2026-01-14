from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver

from app.menu.models import Item as MenuItem
from app.merch.models import Product as MerchProduct
from app.pos.models import Sale

from .models import InventoryConsumption, InventoryLog
from .utils import ensure_inventory_for_menu_item, ensure_inventory_for_merch_product


@receiver(post_save, sender=Sale)
def apply_inventory_on_sale(sender, instance, **kwargs):
    if instance.status != Sale.STATUS_PAID:
        return
    items = instance.items.select_related("menu_variant").all()
    for sale_item in items:
        variant = sale_item.menu_variant
        variant_id = getattr(variant, "id", None)
        if not variant_id:
            continue
        for link in InventoryConsumption.objects.select_related("inventory_item").filter(
            menu_variant=variant, inventory_item__auto_track_sales=True
        ):
            item = link.inventory_item
            if InventoryLog.objects.filter(inventory_item=item, sale_item=sale_item).exists():
                continue
            delta = Decimal(link.quantity_per_sale) * sale_item.quantity * Decimal("-1")
            item.adjust_stock(
                delta,
                reason=InventoryLog.REASON_POS,
                user=None,
                note=f"Sale #{instance.pk}",
                sale_item=sale_item,
            )


@receiver(post_save, sender=MenuItem)
def create_inventory_on_menu(sender, instance, created, **kwargs):
    if kwargs.get("raw"):
        return
    if created:
        ensure_inventory_for_menu_item(instance)


@receiver(post_save, sender=MerchProduct)
def create_inventory_on_merch(sender, instance, created, **kwargs):
    if kwargs.get("raw"):
        return
    if created:
        ensure_inventory_for_merch_product(instance)
