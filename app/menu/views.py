# app/menu/views.py
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CategoryForm, ItemForm, ItemVariantFormSet
from .models import Category, Item
from app.setup.models import SiteSettings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now():
    """Convenience to keep templates consistent when showing 'now'."""
    return timezone.now()


# ---------------------------------------------------------------------------
# CMS: Dashboard & Lists
# ---------------------------------------------------------------------------


@login_required
def manage_menu(request):
    """
    Top-level CMS page for managing the menu tree.
    """
    roots = (
        Category.objects.filter(parent__isnull=True)
        .prefetch_related(
            "items__variants",
            "children",
            "children__items__variants",
            "children__children",
            "children__children__items__variants",
        )
        .order_by("name")
    )
    site_settings = SiteSettings.get_solo()
    currency = site_settings.default_currency or "€"
    return render(
        request,
        "menu/manage.html",
        {"root_categories": roots, "now": _now(), "currency": currency},
    )


@login_required
def items_list(request):
    """
    Flat list of all items (useful for quick edits/search).
    """
    items = (
        Item.objects.select_related("category")
        .prefetch_related("variants")
        .order_by("category__name", "name")
    )
    return render(request, "menu/items_list.html", {"items": items, "now": _now()})


# ---------------------------------------------------------------------------
# Categories (create/edit/delete)
# ---------------------------------------------------------------------------


@login_required
def category_create(request, parent_slug=None):
    """
    Create a category optionally under a specific parent.
    """
    parent = get_object_or_404(Category, slug=parent_slug) if parent_slug else None
    if parent is None:
        parent_param = request.GET.get("parent")
        if parent_param:
            parent = Category.objects.filter(slug=parent_param).first()

    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            if parent:
                obj.parent = parent
            obj.save()
            messages.success(request, f"Category “{obj.name}” created.")
            return redirect("menu:manage")
    else:
        form = CategoryForm(initial={"parent": parent})

    ctx = {"form": form, "parent": parent}
    return render(request, "menu/category_form.html", ctx)


@login_required
def category_edit(request, slug):
    """
    Edit an existing category. The form constrains the 'kind' to match.
    """
    obj = get_object_or_404(Category, slug=slug)

    if request.method == "POST":
        form = CategoryForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated.")
            return redirect("menu:manage")
    else:
        form = CategoryForm(instance=obj)

    return render(request, "menu/category_form.html", {"form": form, "obj": obj})


@login_required
def category_delete(request, slug):
    """
    Delete a category.
    """
    obj = get_object_or_404(Category, slug=slug)

    if request.method == "POST":
        obj.delete()
        messages.success(request, "Category deleted.")
        return redirect("menu:manage")

    return render(request, "menu/category_delete_confirm.html", {"obj": obj})


# ---------------------------------------------------------------------------
# Items (create/edit)
# ---------------------------------------------------------------------------


@login_required
@transaction.atomic
def item_create(request, parent_slug):
    """
    Create an item under the given parent category and manage its variants
    via an inline formset.
    """
    parent = get_object_or_404(Category, slug=parent_slug)
    item = Item(category=parent)  # unsaved, used to bind the formset instance

    if request.method == "POST":
        form = ItemForm(request.POST, instance=item)
        formset = ItemVariantFormSet(
            request.POST,
            instance=item,
        )

        if form.is_valid() and formset.is_valid():
            try:
                # Save parent first so it has a PK for formset relations.
                saved_item = form.save(commit=False)
                saved_item.category = parent
                saved_item.save()

                # Ensure formset is bound to the saved parent, then save.
                formset.instance = saved_item
                formset.save()

                messages.success(request, f"Item “{saved_item.name}” created in {parent.name}.")
                return redirect("menu:manage")

            except IntegrityError:
                messages.error(request, "Could not save item due to a database integrity error.")
                # fall through to render errors
    else:
        form = ItemForm(instance=item)
        formset = ItemVariantFormSet(
            instance=item,
        )

    ctx = {
        "form": form,
        "formset": formset,
        "parent": parent,
        # no 'item' passed here to keep the template title “New item…”
    }
    return render(request, "menu/item_form.html", ctx)


@login_required
@transaction.atomic
def item_edit(request, slug):
    """
    Edit an item and its variants. We save the parent form first, then the
    variants formset, inside a transaction to keep things consistent.
    """
    item = get_object_or_404(Item, slug=slug)
    parent = item.category

    if request.method == "POST":
        form = ItemForm(request.POST, instance=item)
        formset = ItemVariantFormSet(
            request.POST,
            instance=item,
        )

        if form.is_valid() and formset.is_valid():
            try:
                saved_item = form.save()  # already has category
                formset.instance = saved_item  # explicit, keeps things clear
                formset.save()

                messages.success(request, "Item updated.")
                return redirect("menu:manage")

            except IntegrityError:
                messages.error(request, "Could not update item due to a database integrity error.")
                # fall through to render errors
    else:
        form = ItemForm(instance=item)
        formset = ItemVariantFormSet(
            instance=item,
        )

    ctx = {
        "form": form,
        "formset": formset,
        "parent": parent,
        "item": item,  # lets template show “Edit item …”
    }
    return render(request, "menu/item_form.html", ctx)


@login_required
@permission_required("menu.delete_item", raise_exception=True)
def item_delete(request, slug):
    item = get_object_or_404(Item, slug=slug)

    if request.method == "POST":
        name = item.name
        item.delete()
        messages.success(request, f"Item “{name}” was deleted.")
        return redirect("/cms/menu/")
    return render(request, "menu/item_confirm_delete.html", {"item": item})
