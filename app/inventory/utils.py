from django.contrib.auth import get_user_model
from django.utils.text import slugify

from app.comms.services import send_internal
from app.setup.models import SiteSettings, VisibilityRule

from .models import InventoryCategory, InventoryItem


def _inventory_target_groups():
    try:
        rule = VisibilityRule.objects.get(key="inventory.notify")
    except VisibilityRule.DoesNotExist:
        return []
    return list(rule.allowed_groups.values_list("id", flat=True))


def _notification_group_ids():
    settings = SiteSettings.get_solo()
    ids = list(settings.inventory_notification_groups.values_list("id", flat=True))
    if ids:
        return ids
    return _inventory_target_groups()


def notify_reorder(author, item, note: str = ""):
    """
    Send an internal message to users/groups responsible for inventory.
    Falls back to all superusers if no visibility rule is configured.
    """
    group_ids = _notification_group_ids()
    targets = {"groups": group_ids, "users": []}
    if not group_ids:
        User = get_user_model()
        targets["users"] = list(
            User.objects.filter(is_superuser=True).values_list("id", flat=True)
        )
    subject = "System inventory alerts"
    body = (
        f"{item.name} is flagged for reorder.\n\n"
        f"Current stock: {item.current_stock}\n"
        f"Desired stock: {item.desired_stock}\n\n"
        f"{note or ''}"
    ).strip()
    send_internal.post_internal(
        author, subject=subject, body_text=body, targets=targets, system_sender=True
    )


def ensure_inventory_for_menu_item(menu_item):
    category = ensure_category_from_menu(menu_item.category)
    link = InventoryItem.objects.filter(menu_items=menu_item).first()
    if link:
        if category and link.category_id != category.id:
            link.category = category
            link.save(update_fields=["category"])
        return link
    item = InventoryItem.objects.create(
        name=menu_item.name,
        kind=InventoryItem.KIND_INGREDIENT,
        description=menu_item.description,
        is_active=menu_item.visible_public,
        category=category,
    )
    item.menu_items.add(menu_item)
    item.sync_default_consumptions()
    return item


def ensure_inventory_for_merch_product(product):
    category = ensure_category_from_merch(product.category)
    link = InventoryItem.objects.filter(merch_products=product).first()
    if link:
        if category and link.category_id != category.id:
            link.category = category
            link.save(update_fields=["category"])
        return link
    item = InventoryItem.objects.create(
        name=product.name,
        kind=InventoryItem.KIND_PRODUCT,
        description=product.description,
        is_active=product.visible_public,
        category=category,
    )
    item.merch_products.add(product)
    return item


def ensure_category_from_menu(menu_category):
    if not menu_category:
        return None
    parent = ensure_category_from_menu(menu_category.parent) if menu_category.parent else None
    slug_source = menu_category.slug or slugify(menu_category.name) or f"{menu_category.pk}"
    slug = f"menu-{slug_source}"
    defaults = {"name": menu_category.name, "parent": parent}
    category, _ = InventoryCategory.objects.get_or_create(
        slug=slug,
        defaults=defaults,
    )
    if parent and category.parent_id != parent.id:
        category.parent = parent
        category.save(update_fields=["parent"])
    return category


def ensure_category_from_merch(merch_category):
    if not merch_category:
        return None
    parent = (
        ensure_category_from_merch(merch_category.parent) if merch_category.parent else None
    )
    slug_source = merch_category.slug or slugify(merch_category.name) or f"{merch_category.pk}"
    slug = f"merch-{slug_source}"
    defaults = {"name": merch_category.name, "parent": parent}
    category, _ = InventoryCategory.objects.get_or_create(
        slug=slug,
        defaults=defaults,
    )
    if parent and category.parent_id != parent.id:
        category.parent = parent
        category.save(update_fields=["parent"])
    return category


def user_can_see_inventory_dashboard(user) -> bool:
    settings = SiteSettings.get_solo()
    groups = settings.inventory_dashboard_groups.values_list("id", flat=True)
    group_ids = list(groups)
    if not group_ids:
        return user.is_superuser
    if user.is_superuser:
        return True
    return user.groups.filter(id__in=group_ids).exists()
