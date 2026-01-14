from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


# --------- money ---------
def _to_decimal(v):
    try:
        return Decimal(str(v))
    except (InvalidOperation, TypeError, ValueError):
        return None


@register.simple_tag(takes_context=True)
def money(context, value, position="after"):
    """
    Price with currency; default 'after' -> '2.50 €'.
    Respects site_settings.currency_symbol and currency_position if present.
    """
    d = _to_decimal(value)
    if d is None:
        return ""
    site = context.get("site_settings") or {}
    symbol = getattr(site, "currency_symbol", None) or site.get("currency_symbol") or "€"
    pos = (
        getattr(site, "currency_position", None) or site.get("currency_position") or position
    ).lower()
    amount = f"{d:.2f}"
    return f"{symbol}{amount}" if pos == "before" else f"{amount} {symbol}"


# --------- label helpers ---------
@register.filter
def variant_label(v):
    return str(getattr(v, "label", "") or "")


# --------- amount with CMS unit ----------
def _first_attr(obj, *names):
    for n in names:
        if not obj:
            continue
        if hasattr(obj, n):
            val = getattr(obj, n)
            if val not in (None, ""):
                return val
        # dict-like
        try:
            val = obj[n]  # type: ignore[index]
            if val not in (None, ""):
                return val
        except Exception:
            pass
    return None


def _as_decimal(value):
    d = _to_decimal(value)
    return d


def _format_qty_unit(qty, unit):
    """
    Basic formatting for quantity + unit without unwanted conversions.
    - Keeps 'g', 'kg', 'ml', 'cl', 'l', 'pcs', 'piece', 'pieces' as-is
    - If unit missing, just returns qty
    """
    if qty in (None, ""):
        return ""
    # clean unit
    u = (str(unit) if unit is not None else "").strip().lower()
    qty_str = f"{qty}".rstrip("0").rstrip(".") if isinstance(qty, float | Decimal) else f"{qty}"

    if not u:
        return qty_str

    # unify some pluralizations
    if u in ("piece", "pieces"):
        u = "pcs"
    return f"{qty_str} {u}"


def _derive_amount_from_fields(variant):
    """
    Try common field names on the Variant itself.
    Return (qty, unit) or (None, None) if not found.
    """
    # 1) explicit amount + unit on the variant
    qty = _first_attr(variant, "amount", "qty", "quantity", "Quantity", "count", "pieces")
    unit = _first_attr(variant, "unit", "uom", "uom_display")

    if qty not in (None, "") and unit not in (None, ""):
        return qty, unit

    # 2) specialized fields that imply a unit
    for field, unit_name in (
        ("g", "g"),
        ("grams", "g"),
        ("kg", "kg"),
        ("ml", "ml"),
        ("cl", "cl"),
        ("l", "l"),
        ("amount_l", "l"),
        ("volume_l", "l"),
        ("size_l", "l"),
        ("pcs", "pcs"),
    ):
        val = _first_attr(variant, field)
        if val not in (None, ""):
            return val, unit_name

    # 3) amount without explicit unit, but we might pick it up from item/category later
    if qty not in (None, ""):
        return qty, None

    return None, None


def _resolve_unit_from_item_or_category(item, category):
    """
    If the variant didn't carry a unit, try the parent item, then the category.
    """
    unit = _first_attr(item, "unit", "uom", "uom_display")
    if unit:
        return unit
    return _first_attr(category, "unit", "uom", "uom_display")


@register.simple_tag
def variant_amount(item, variant):
    """
    Returns a string like:
      - '330 ml' (drinks with ml)
      - '0.5 l'
      - '150 g'
      - '2 pcs'
    Uses Variant -> Item -> Category to resolve unit (no forced liters).
    """
    category = getattr(item, "category", None) or _first_attr(item, "category")
    qty, unit = _derive_amount_from_fields(variant)

    if not unit:
        unit = _resolve_unit_from_item_or_category(item, category)

    # final string
    return _format_qty_unit(qty, unit)
