# app/pos/views.py
import json
from decimal import ROUND_HALF_UP, Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models as djmodels
from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST

from app.menu.models import ItemVariant  # your real models
from app.setup.models import SiteSettings

from .forms import POSQuickButtonFormSet, POSSettingsForm
from .models import Payment, POSQuickButton, Sale, SaleItem


# === Money helpers ===
def _money(v):
    return Decimal(v).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _get_pos_config() -> dict:
    settings_obj = SiteSettings.get_solo()
    tax_rate = settings_obj.pos_tax_rate or Decimal("0.00")
    if not isinstance(tax_rate, Decimal):
        tax_rate = Decimal(tax_rate)
    return {
        "tax_rate": tax_rate.quantize(Decimal("0.01")),
        "show_tax": bool(settings_obj.pos_show_tax),
        "apply_tax": bool(settings_obj.pos_apply_tax),
        "show_discounts": bool(settings_obj.pos_show_discounts),
        "apply_discounts": bool(settings_obj.pos_apply_discounts),
    }


def _config_for_client(config: dict) -> str:
    return json.dumps(
        {
            "taxRate": str(config.get("tax_rate", Decimal("0.00"))),
            "showTax": config.get("show_tax", True),
            "applyTax": config.get("apply_tax", True),
            "showDiscounts": config.get("show_discounts", True),
            "applyDiscounts": config.get("apply_discounts", True),
        }
    )


# === Cart session helpers ===
def _get_cart(req):
    """
    Cart structure in session:
    {
      "lines": [
        {"id": variant_id, "title": "...", "qty": 1, "unit_price": "4.20",
         "discount": {"type": "PERCENT|AMOUNT|FREE", "value": "10.00"} or None,
         "tax_rate": "19.00",
         "calc_subtotal": "…", "calc_discount": "…", "calc_tax": "…", "calc_total": "…"}
      ],
      "order_discount": {"type": "...", "value": "...", "reason_id": 1} or None,
      "totals": {"subtotal": "...", "discount_total": "...", "tax_total": "...", "grand_total": "..."}
    }
    """
    return req.session.get("pos_cart", {"lines": [], "order_discount": None})


def _save_cart(req, cart):
    req.session["pos_cart"] = cart
    req.session.modified = True


def _reprice_cart(cart: dict, config: dict | None = None) -> dict:
    config = config or _get_pos_config()
    apply_discounts = config.get("apply_discounts", True)
    apply_tax = config.get("apply_tax", True)
    tax_rate_default = config.get("tax_rate", Decimal("0.00")) or Decimal("0.00")
    if not isinstance(tax_rate_default, Decimal):
        tax_rate_default = Decimal(tax_rate_default)
    tax_rate_default = tax_rate_default.quantize(Decimal("0.01"))

    subtotal = Decimal("0.00")
    discount_total = Decimal("0.00")
    tax_total = Decimal("0.00")
    grand_total = Decimal("0.00")

    lines = cart.get("lines", [])
    if not apply_discounts:
        cart["order_discount"] = None
        for line in lines:
            line["discount"] = None

    for line in lines:
        qty = int(line.get("qty", 0))
        unit = _money(line.get("unit_price", "0.00"))
        line_sub = _money(unit * qty)

        # per-line discount
        line_disc = Decimal("0.00")
        discount_entries: list[dict] = []
        if apply_discounts:
            if line.get("discounts"):
                discount_entries = line.get("discounts", [])
            elif line.get("discount"):
                discount_entries = [line["discount"]]
                line.pop("discount", None)
            line["discounts"] = discount_entries
        else:
            discount_entries = []

        free_units = 0
        discounted_units = 0
        for entry in discount_entries:
            dtype = entry.get("type")
            dval = _money(entry.get("value", "0"))
            per_unit = bool(entry.get("per_item"))
            count = int(entry.get("count", 1) or 1)
            button_qty = min(count, qty) if per_unit else 1
            base = unit if per_unit else line_sub
            amount = Decimal("0.00")
            if dtype == "FREE":
                amount = base
            elif dtype == "PERCENT":
                amount = (base * dval / Decimal("100")).quantize(Decimal("0.01"))
            elif dtype == "AMOUNT":
                amount = min(dval, base)
            if per_unit:
                amount *= button_qty
                if dtype == "FREE":
                    free_units += button_qty
                else:
                    discounted_units += button_qty
            elif dtype == "FREE":
                free_units = qty
            if amount > line_sub - line_disc:
                amount = line_sub - line_disc
            line_disc += amount

        line_after_disc = _money(line_sub - line_disc)

        tax_rate = _money(line.get("tax_rate", tax_rate_default))
        if not apply_tax:
            tax_rate = Decimal("0.00")
        line_tax = (line_after_disc * tax_rate / Decimal("100")).quantize(Decimal("0.01"))
        line_total = _money(line_after_disc + line_tax)

        line["calc_subtotal"] = str(_money(line_sub))
        line["calc_discount"] = str(_money(line_disc))
        line["calc_tax"] = str(_money(line_tax))
        line["calc_total"] = str(_money(line_total))
        line["free_units"] = min(free_units, qty)
        line["discount_units"] = max(discounted_units, 0)

        subtotal += line_sub
        discount_total += line_disc
        tax_total += line_tax
        grand_total += line_total

    # order-level discount
    order_disc_amount = Decimal("0.00")
    od = cart.get("order_discount") if apply_discounts else None
    if od:
        base = _money(subtotal - discount_total)
        dtype = od.get("type")
        dval = _money(od.get("value", "0"))
        if dtype == "FREE":
            order_disc_amount = base
        elif dtype == "PERCENT":
            order_disc_amount = (base * dval / Decimal("100")).quantize(Decimal("0.01"))
        elif dtype == "AMOUNT":
            order_disc_amount = min(dval, base)

        # naive proportional tax reduction to reflect order discount
        if base > 0 and apply_tax:
            fraction = (base - order_disc_amount) / base
            tax_total = (tax_total * fraction).quantize(Decimal("0.01"))
            grand_total = _money((base - order_disc_amount) + tax_total)
        else:
            tax_total = Decimal("0.00")
            grand_total = Decimal("0.00")

        discount_total += order_disc_amount

    cart["totals"] = {
        "subtotal": str(_money(subtotal)),
        "discount_total": str(_money(discount_total)),
        "tax_total": str(_money(tax_total)),
        "grand_total": str(_money(grand_total)),
    }
    return cart


def _variant_display_parts(variant: ItemVariant) -> tuple[str, str]:
    title = variant.item.name
    label = (variant.label or "").strip()
    qty = _variant_size_quantity(variant)
    if label and qty:
        detail = f"{label} — {qty}"
    elif label:
        detail = label
    else:
        detail = qty
    return title, detail


def _variant_size_label(v: ItemVariant) -> str:
    """
    Size/variant label for buttons inside an item tile.
    Prefer explicit label; else derive from quantity + unit (e.g., '0.3 L').
    """
    base = _variant_size_quantity(v)
    if v.label:
        return f"{v.label} ({base})"
    return base


# === Views ===
@method_decorator([login_required], name="dispatch")
class IndexView(View):
    template_name = "pos/index.html"

    def _build_context(self, request, *, pos_form=None, quickbuttons=None):
        config = _get_pos_config()
        cart = _reprice_cart(_get_cart(request), config=config)
        if pos_form is None:
            pos_form = POSSettingsForm(instance=SiteSettings.get_solo())
        if quickbuttons is None:
            quickbuttons = POSQuickButtonFormSet(
                queryset=POSQuickButton.objects.all().order_by("sort_order", "id"),
                prefix="quickbuttons",
            )
        return {
            "cart": cart,
            "pos_config": config,
            "pos_config_json": _config_for_client(config),
            "pos_form": pos_form,
            "quickbuttons": quickbuttons,
        }

    def get(self, request):
        return render(request, self.template_name, self._build_context(request))

    def post(self, request):
        settings_obj = SiteSettings.get_solo()
        pos_form = POSSettingsForm(request.POST, instance=settings_obj)
        quickbuttons = POSQuickButtonFormSet(
            request.POST,
            queryset=POSQuickButton.objects.all().order_by("sort_order", "id"),
            prefix="quickbuttons",
        )
        if pos_form.is_valid() and quickbuttons.is_valid():
            pos_form.save()
            quickbuttons.save()
            messages.success(request, "POS settings saved.")
            return redirect("pos:index")
        messages.error(request, "Could not save POS settings. Please review the fields.")
        return render(
            request,
            self.template_name,
            self._build_context(request, pos_form=pos_form, quickbuttons=quickbuttons),
        )


@login_required
def api_search_items(request):
    """
    Returns grouped items for search:
    {
      "items": [
        {
          "id": <item_id>, "name": "Latte",
          "variants": [
            {"id": <variant_id>, "size": "Small", "price": "2.80"},
            ...
          ]
        },
        ...
      ]
    }
    """
    q = request.GET.get("q", "").strip()

    qs = ItemVariant.objects.select_related("item", "unit", "item__category").filter(
        item__visible_public=True
    )

    if q:
        qs = qs.filter(djmodels.Q(item__name__icontains=q) | djmodels.Q(label__icontains=q))

    items = {}
    for v in qs.order_by("item__name", "label")[:60]:
        # filter out sold-out parent items (your Item method)
        if v.item.is_sold_out():
            continue
        it = items.setdefault(v.item.id, {"id": v.item.id, "name": v.item.name, "variants": []})
        it["variants"].append(
            {
                "id": v.id,
                "size": _variant_size_label(v),
                "price": str(_money(v.price)),
            }
        )

    out = list(items.values())
    # sort variants and items for stable ordering
    for it in out:
        it["variants"].sort(key=lambda x: x["size"].lower())
    out.sort(key=lambda x: x["name"].lower())
    return JsonResponse({"items": out})


@login_required
def api_browse_items(request):
    """
    Returns categories grouped by item with variants per item:
    {
      "categories": [
        {
          "id": <cat_id>, "name": "Coffee",
          "items": [
            {
              "id": <item_id>, "name": "Latte",
              "variants": [
                {"id": <variant_id>, "size": "Small", "price": "2.80"},
                ...
              ]
            },
            ...
          ]
        },
        ...
      ]
    }
    """
    qs = (
        ItemVariant.objects.select_related("item", "unit", "item__category")
        .filter(item__visible_public=True)
        .order_by("item__category__name", "item__name", "label")
    )

    # cat_id -> {id, name, items: {item_id: {id, name, variants: []}}}
    cats = {}
    for v in qs:
        if v.item.is_sold_out():
            continue
        cat = v.item.category
        if not cat:
            continue

        c = cats.setdefault(cat.id, {"id": cat.id, "name": cat.name, "items": {}})
        it = c["items"].setdefault(
            v.item.id, {"id": v.item.id, "name": v.item.name, "variants": []}
        )
        it["variants"].append(
            {
                "id": v.id,
                "size": _variant_size_label(v),
                "price": str(_money(v.price)),
            }
        )

    # finalize: list-ify and sort
    categories = []
    for c in cats.values():
        items_list = list(c["items"].values())
        for it in items_list:
            it["variants"].sort(key=lambda x: x["size"].lower())
        items_list.sort(key=lambda x: x["name"].lower())
        categories.append({"id": c["id"], "name": c["name"], "items": items_list})

    categories.sort(key=lambda c: c["name"].lower())
    return JsonResponse({"categories": categories})


@login_required
@require_POST
def api_cart_add(request):
    var_id = request.POST.get("id")
    qty = int(request.POST.get("qty", "1"))
    if not var_id or qty < 1:
        return HttpResponseBadRequest("Invalid parameters")
    config = _get_pos_config()

    try:
        v = ItemVariant.objects.select_related("item", "unit").get(pk=var_id)
    except ItemVariant.DoesNotExist:
        return HttpResponseBadRequest("Variant not found")

    title_main, detail = _variant_display_parts(v)
    title_full = f"{title_main} — {detail}" if detail else title_main
    unit_price = _money(v.price)

    cart = _get_cart(request)
    # bump if present, else append
    for line in cart["lines"]:
        if str(line["id"]) == str(v.id):
            line["qty"] = int(line["qty"]) + qty
            break
    else:
        cart["lines"].append(
            {
                "id": v.id,
                "title": title_full,
                "title_main": title_main,
                "variant_label": detail,
                "qty": qty,
                "unit_price": str(unit_price),
                "discounts": [],
                "tax_rate": str(config.get("tax_rate", Decimal("0.00"))),
            }
        )

    _reprice_cart(cart, config=config)
    _save_cart(request, cart)
    return JsonResponse(cart)


@login_required
@require_POST
def api_cart_remove(request):
    item_id = request.POST.get("id")
    if not item_id:
        return HttpResponseBadRequest("Missing id")
    config = _get_pos_config()
    cart = _get_cart(request)
    cart["lines"] = [
        line_item for line_item in cart["lines"] if str(line_item["id"]) != str(item_id)
    ]
    _reprice_cart(cart, config=config)
    _save_cart(request, cart)
    return JsonResponse(cart)


@login_required
@require_POST
def api_cart_update(request):
    item_id = request.POST.get("id")
    qty = int(request.POST.get("qty", "1"))
    if not item_id or qty < 0:
        return HttpResponseBadRequest("Invalid parameters")
    config = _get_pos_config()
    cart = _get_cart(request)
    for line_item in list(cart["lines"]):
        if str(line_item["id"]) == str(item_id):
            if qty == 0:
                cart["lines"].remove(line_item)
            else:
                line_item["qty"] = qty
            break
    _reprice_cart(cart, config=config)
    _save_cart(request, cart)
    return JsonResponse(cart)


@login_required
@require_POST
def api_cart_clear(request):
    config = _get_pos_config()
    cart = {"lines": [], "order_discount": None}
    _reprice_cart(cart, config=config)
    _save_cart(request, cart)
    return JsonResponse(cart)


@login_required
def api_quick_buttons(request):
    btns = POSQuickButton.objects.filter(is_active=True).order_by("sort_order")
    data = [
        {
            "id": b.id,
            "label": b.label,
            "type": b.discount_type,
            "value": str(_money(b.value)),
            "scope": b.scope,
            "reason_id": b.reason_id,
        }
        for b in btns
    ]
    return JsonResponse({"buttons": data})


@login_required
@require_POST
def api_cart_apply_discount(request):
    config = _get_pos_config()
    if not config.get("apply_discounts", True):
        return HttpResponseBadRequest("Discounts are disabled.")

    scope = request.POST.get("scope")  # ORDER or ITEM
    dtype = request.POST.get("type")  # PERCENT/AMOUNT/FREE
    value = request.POST.get("value", "0")
    reason_id = request.POST.get("reason_id")
    item_id = request.POST.get("item_id")
    increment = request.POST.get("increment") == "true"
    label = request.POST.get("label") or ""
    button_id = request.POST.get("button_id")

    if scope not in ("ORDER", "ITEM") or dtype not in ("PERCENT", "AMOUNT", "FREE"):
        return HttpResponseBadRequest("Invalid discount")

    cart = _get_cart(request)
    if scope == "ORDER":
        cart["order_discount"] = {
            "type": dtype,
            "value": value,
            "reason_id": int(reason_id) if reason_id else None,
            "label": label,
        }
    else:
        if not item_id:
            return HttpResponseBadRequest("Missing item_id for item discount")
        for line_item in cart["lines"]:
            if str(line_item["id"]) == str(item_id):
                discounts = line_item.setdefault("discounts", [])
                if line_item.get("discount") and not discounts:
                    discounts.append(
                        {
                            "type": line_item["discount"].get("type"),
                            "value": line_item["discount"].get("value"),
                            "per_item": line_item["discount"].get("per_item"),
                            "count": int(line_item["discount"].get("count", 1) or 1),
                            "button_id": line_item["discount"].get("button_id"),
                            "label": line_item["discount"].get("label", ""),
                        }
                    )
                    line_item.pop("discount", None)
                target = None
                if increment and button_id:
                    for entry in discounts:
                        if entry.get("button_id") == button_id:
                            target = entry
                            break
                if target:
                    target["count"] = int(target.get("count", 0) or 0) + 1
                else:
                    discounts.append(
                        {
                            "type": dtype,
                            "value": value,
                            "per_item": True,
                            "count": 1,
                            "button_id": button_id,
                            "label": label,
                        }
                    )
                break

    _reprice_cart(cart, config=config)
    _save_cart(request, cart)
    return JsonResponse(cart)


@login_required
def api_cart_totals(request):
    config = _get_pos_config()
    cart = _reprice_cart(_get_cart(request), config=config)
    return JsonResponse(cart)


@login_required
@require_POST
@transaction.atomic
def api_checkout(request):
    """
    MVP: one payment per sale.
    POST body expects:
      - kind: CASH|CARD|OTHER
      - amount: "12.34"
      - note: optional
    """
    config = _get_pos_config()
    cart = _reprice_cart(_get_cart(request), config=config)
    if not cart["lines"]:
        return HttpResponseBadRequest("Cart is empty")

    p_kind = request.POST.get("kind", "CASH")
    p_amount = request.POST.get("amount")
    if not p_amount:
        return HttpResponseBadRequest("Missing payment amount")

    sale = Sale.objects.create(
        opened_by=request.user,
        status=Sale.STATUS_PAID,
        order_discount_type=(
            cart["order_discount"]["type"] if cart.get("order_discount") else None
        ),
        order_discount_value=(
            _money(cart["order_discount"]["value"])
            if cart.get("order_discount")
            else Decimal("0.00")
        ),
        order_discount_reason_id=(
            cart["order_discount"]["reason_id"] if cart.get("order_discount") else None
        ),
        subtotal=_money(cart["totals"]["subtotal"]),
        discount_total=_money(cart["totals"]["discount_total"]),
        tax_total=_money(cart["totals"]["tax_total"]),
        grand_total=_money(cart["totals"]["grand_total"]),
        note=request.POST.get("note", ""),
        closed_by=request.user,
        closed_at=timezone.now(),
    )

    for line_item in cart["lines"]:
        SaleItem.objects.create(
            sale=sale,
            menu_variant_id=int(line_item["id"]),  # FK to ItemVariant
            title_snapshot=line_item["title"],
            quantity=int(line_item["qty"]),
            unit_price=_money(line_item["unit_price"]),
            discount_type=(line_item["discount"]["type"] if line_item.get("discount") else None),
            discount_value=(
                _money(line_item["discount"]["value"])
                if line_item.get("discount")
                else Decimal("0.00")
            ),
            tax_rate=_money(line_item.get("tax_rate", TAX_RATE_DEFAULT)),
            tax_amount=_money(line_item["calc_tax"]),
            line_subtotal=_money(line_item["calc_subtotal"]),
            line_discount=_money(line_item["calc_discount"]),
            line_total=_money(line_item["calc_total"]),
        )

    Payment.objects.create(
        sale=sale, kind=p_kind, amount=_money(p_amount), received_by=request.user
    )

    # clear cart
    _save_cart(request, {"lines": [], "order_discount": None})
    return JsonResponse({"ok": True, "sale_id": sale.id})


def _variant_size_quantity(v):
    # Return numeric quantity + unit as a clean string, e.g. "0.3 L"
    try:
        qty = f"{v.quantity.normalize():g}"
    except Exception:
        qty = str(v.quantity)
    unit_code = getattr(v.unit, "code", "")
    if unit_code:
        return f"{qty} {unit_code}".strip()
    return qty
