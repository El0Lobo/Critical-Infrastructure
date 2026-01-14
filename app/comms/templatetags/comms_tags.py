from django import template

register = template.Library()


@register.filter
def has_any(iterable):
    try:
        return bool(list(iterable))
    except Exception:
        return False
