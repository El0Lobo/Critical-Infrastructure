from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from app.setup.models import SiteSettings

from .forms import (
    InventoryAlertSettingsForm,
    InventoryCategoryForm,
    InventoryItemForm,
    InventoryPackageFormSet,
)
from .models import InventoryCategory, InventoryItem, InventoryLog
from .utils import notify_reorder


def _inventory_settings_access(user):
    return user.is_staff or user.is_superuser


@login_required
def manage(request):
    settings_obj = SiteSettings.get_solo()
    alerts_form = None
    if _inventory_settings_access(request.user):
        if request.method == "POST" and request.POST.get("form_name") == "inventory_alerts":
            alerts_form = InventoryAlertSettingsForm(request.POST, instance=settings_obj)
            if alerts_form.is_valid():
                alerts_form.save()
                messages.success(request, "Inventory alert preferences updated.")
                return redirect("inventory:inventory_manage")
        else:
            alerts_form = InventoryAlertSettingsForm(instance=settings_obj)
    if request.method == "POST":
        # If POST without alerts form (e.g., invalid access), redirect to avoid falling through
        return redirect("inventory:inventory_manage")

    search = request.GET.get("q", "").strip()
    kind_filter = request.GET.get("kind", "")
    status_filter = request.GET.get("status", "")
    category_filter = request.GET.get("category", "")

    base_items = (
        InventoryItem.objects.all()
        .select_related("category")
        .prefetch_related("packages")
        .order_by("name")
    )
    if search:
        base_items = base_items.filter(name__icontains=search)
    if kind_filter:
        base_items = base_items.filter(kind=kind_filter)
    if status_filter == "needs_reorder":
        base_items = base_items.filter(needs_reorder=True)
    elif status_filter == "inactive":
        base_items = base_items.filter(is_active=False)
    if category_filter:
        base_items = base_items.filter(category__slug=category_filter)

    items_by_category: dict[int | None, list[InventoryItem]] = {}
    for entry in base_items:
        items_by_category.setdefault(entry.category_id, []).append(entry)

    top_categories = (
        InventoryCategory.objects.filter(parent__isnull=True)
        .prefetch_related("children__children")
        .order_by("sort_order", "name")
    )
    uncategorized = items_by_category.get(None, [])
    categories_for_filter = InventoryCategory.objects.order_by("name")
    currency = SiteSettings.get_solo().default_currency or "€"
    return render(
        request,
        "inventory/manage.html",
        {
            "top_categories": top_categories,
            "uncategorized": uncategorized,
            "currency": currency,
            "search": search,
            "kind_filter": kind_filter,
            "status_filter": status_filter,
            "kinds": InventoryItem.KIND_CHOICES,
            "category_filter": category_filter,
            "category_choices": categories_for_filter,
            "category_items": items_by_category,
            "alerts_form": alerts_form,
        },
    )


@login_required
def category_create(request):
    initial = {}
    if "parent" in request.GET:
        try:
            initial["parent"] = InventoryCategory.objects.get(slug=request.GET.get("parent")).pk
        except InventoryCategory.DoesNotExist:
            initial["parent"] = None
    if request.method == "POST":
        form = InventoryCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"Category “{category.name}” created.")
            return redirect("inventory:inventory_manage")
    else:
        form = InventoryCategoryForm(initial=initial)
    return render(request, "inventory/category_form.html", {"form": form, "category": None})


@login_required
def category_edit(request, slug):
    category = get_object_or_404(InventoryCategory, slug=slug)
    if request.method == "POST":
        form = InventoryCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f"Category “{category.name}” updated.")
            return redirect("inventory:inventory_manage")
    else:
        form = InventoryCategoryForm(instance=category)
    return render(request, "inventory/category_form.html", {"form": form, "category": category})


@login_required
def item_create(request):
    initial = {}
    if "category" in request.GET:
        initial["category"] = request.GET.get("category")
    item = InventoryItem()
    if request.method == "POST":
        form = InventoryItemForm(request.POST, instance=item)
        package_formset = InventoryPackageFormSet(request.POST, instance=item)
        if form.is_valid() and package_formset.is_valid():
            item = form.save(commit=False)
            item.created_by = request.user
            item.updated_by = request.user
            item.save()
            form.save_m2m()
            package_formset.instance = item
            package_formset.save()
            item.sync_default_consumptions()
            messages.success(request, f"Inventory item “{item.name}” created.")
            return redirect("inventory:inventory_manage")
    else:
        form = InventoryItemForm(initial=initial, instance=item)
        package_formset = InventoryPackageFormSet(instance=item)
    return render(
        request,
        "inventory/item_form.html",
        {"form": form, "item": None, "package_formset": package_formset},
    )


@login_required
def item_edit(request, slug):
    item = get_object_or_404(InventoryItem, slug=slug)
    if request.method == "POST":
        form = InventoryItemForm(request.POST, instance=item)
        package_formset = InventoryPackageFormSet(request.POST, instance=item)
        if form.is_valid() and package_formset.is_valid():
            obj = form.save(commit=False)
            obj.updated_by = request.user
            obj.save()
            form.save_m2m()
            package_formset.save()
            obj.sync_default_consumptions()
            messages.success(request, f"Inventory item “{obj.name}” updated.")
            return redirect("inventory:inventory_manage")
    else:
        form = InventoryItemForm(instance=item)
        package_formset = InventoryPackageFormSet(instance=item)
    return render(
        request,
        "inventory/item_form.html",
        {
            "form": form,
            "item": item,
            "logs": item.logs.select_related("created_by")[:12],
            "package_formset": package_formset,
        },
    )


@login_required
@require_POST
def adjust_stock(request, slug):
    item = get_object_or_404(InventoryItem, slug=slug)
    delta_raw = request.POST.get("delta")
    note = request.POST.get("note", "")
    try:
        delta = Decimal(delta_raw)
    except Exception:
        messages.error(request, "Enter a numeric adjustment.")
        return redirect("inventory:inventory_item_edit", slug=item.slug)
    reason = InventoryLog.REASON_MANUAL
    item.adjust_stock(delta, reason, user=request.user, note=note)
    messages.success(request, f"Stock updated for {item.name}.")
    return redirect("inventory:inventory_item_edit", slug=item.slug)


@login_required
@require_POST
def toggle_reorder(request, slug):
    item = get_object_or_404(InventoryItem, slug=slug)
    action = request.POST.get("action") or "flag"
    if action == "clear":
        item.needs_reorder = False
        item.save(update_fields=["needs_reorder"])
        messages.success(request, f"Reorder flag cleared for {item.name}.")
    else:
        item.needs_reorder = True
        item.last_reorder_at = timezone.now()
        item.save(update_fields=["needs_reorder", "last_reorder_at"])
        notify_reorder(request.user, item, note=request.POST.get("note", ""))
        messages.success(request, f"Reorder request recorded for {item.name}.")
    return redirect("inventory:inventory_manage")
