from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CategoryForm, ProductForm, ProductImageFormSet, ProductVariantFormSet
from .models import Category, Product
from app.setup.models import SiteSettings

# ---------------- CMS ----------------


@login_required
def manage(request):
    top_categories = (
        Category.objects.filter(parent__isnull=True)
        .prefetch_related(
            Prefetch("children", queryset=Category.objects.all().order_by("order", "name")),
            Prefetch(
                "products",
                queryset=Product.objects.all()
                .prefetch_related("images", "variants")
                .order_by("-featured", "name"),
            ),
        )
        .order_by("order", "name")
    )
    settings = SiteSettings.get_solo()
    currency = settings.default_currency or "€"
    return render(
        request,
        "merch/manage.html",
        {"top_categories": top_categories, "currency": currency},
    )


@login_required
def category_new(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"Category “{cat.name}” created.")
            return redirect("merch:manage")
    else:
        form = CategoryForm()
    return render(request, "merch/category_form.html", {"form": form, "category": None})


@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"Category “{cat.name}” updated.")
            return redirect("merch:manage")
    else:
        form = CategoryForm(instance=category)
    return render(request, "merch/category_form.html", {"form": form, "category": category})


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        name = category.name
        category.delete()
        messages.success(request, f"Category “{name}” deleted.")
        return redirect("merch:manage")
    return render(request, "merch/confirm_delete.html", {"category": category})


@login_required
def product_create(request):
    product = Product()
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        img_formset = ProductImageFormSet(
            request.POST, request.FILES, instance=product, prefix="images"
        )
        var_formset = ProductVariantFormSet(request.POST, instance=product, prefix="variants")
        if form.is_valid() and img_formset.is_valid() and var_formset.is_valid():
            form.save()
            img_formset.save()
            var_formset.save()
            messages.success(request, "Product created.")
            return redirect("merch:manage")
    else:
        form = ProductForm(instance=product)
        img_formset = ProductImageFormSet(instance=product, prefix="images")
        var_formset = ProductVariantFormSet(instance=product, prefix="variants")
    return render(
        request,
        "merch/product_form.html",
        {
            "product": product,
            "form": form,
            "img_formset": img_formset,
            "var_formset": var_formset,
        },
    )


@login_required
def product_edit(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        img_formset = ProductImageFormSet(
            request.POST, request.FILES, instance=product, prefix="images"
        )
        var_formset = ProductVariantFormSet(request.POST, instance=product, prefix="variants")
        if form.is_valid() and img_formset.is_valid() and var_formset.is_valid():
            form.save()
            img_formset.save()
            var_formset.save()
            messages.success(request, "Product updated.")
            return redirect("merch:manage")
    else:
        form = ProductForm(instance=product)
        img_formset = ProductImageFormSet(instance=product, prefix="images")
        var_formset = ProductVariantFormSet(instance=product, prefix="variants")
    return render(
        request,
        "merch/product_form.html",
        {
            "product": product,
            "form": form,
            "img_formset": img_formset,
            "var_formset": var_formset,
        },
    )


@login_required
def product_delete(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.method == "POST":
        name = product.name
        product.delete()
        messages.success(request, f"Product “{name}” deleted.")
        return redirect("merch:manage")
    return render(request, "merch/confirm_delete.html", {"product": product})


# ---------------- Public Store ----------------


def store_index(request):
    categories = Category.objects.filter(parent__isnull=True).order_by("order", "name")
    products = (
        Product.objects.filter(visible_public=True)
        .prefetch_related("images", "variants")
        .order_by("-featured", "name")
    )
    return render(
        request, "public/merch/index.html", {"categories": categories, "products": products}
    )


def store_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    child_ids = list(category.children.values_list("id", flat=True))
    products = (
        Product.objects.filter(visible_public=True, category_id__in=[category.id, *child_ids])
        .prefetch_related("images", "variants")
        .order_by("-featured", "name")
    )
    categories = Category.objects.filter(parent__isnull=True).order_by("order", "name")
    return render(
        request,
        "public/merch/index.html",
        {
            "categories": categories,
            "products": products,
            "active_category": category,
        },
    )


def store_detail(request, slug):
    product = get_object_or_404(
        Product.objects.prefetch_related("images", "variants", "category"),
        slug=slug,
        visible_public=True,
    )
    return render(request, "public/merch/detail.html", {"product": product})
