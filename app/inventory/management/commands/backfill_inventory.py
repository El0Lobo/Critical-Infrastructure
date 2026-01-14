from django.core.management.base import BaseCommand

from app.menu.models import Item as MenuItem
from app.merch.models import Product as MerchProduct

from ...utils import ensure_inventory_for_menu_item, ensure_inventory_for_merch_product


class Command(BaseCommand):
    help = "Create inventory entries for existing menu items and merch products."

    def handle(self, *args, **options):
        created_menu = 0
        created_merch = 0
        for menu_item in MenuItem.objects.select_related("category"):
            item = menu_item.inventory_links.first()
            if not item:
                ensure_inventory_for_menu_item(menu_item)
                created_menu += 1
            elif not item.category:
                new_cat = ensure_inventory_for_menu_item(menu_item).category
                if new_cat and item.category_id != new_cat.id:
                    item.category = new_cat
                    item.save(update_fields=["category"])

        for product in MerchProduct.objects.select_related("category"):
            item = product.inventory_links.first()
            if not item:
                ensure_inventory_for_merch_product(product)
                created_merch += 1
            elif not item.category:
                new_cat = ensure_inventory_for_merch_product(product).category
                if new_cat and item.category_id != new_cat.id:
                    item.category = new_cat
                    item.save(update_fields=["category"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Backfill complete: {created_menu} menu items, {created_merch} merch products."
            )
        )
