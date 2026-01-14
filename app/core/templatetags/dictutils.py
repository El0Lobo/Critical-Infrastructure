from django import template

register = template.Library()


@register.filter
def get(d, key):
    """Safe dict-get for templates: {{ obj|get:'key' }}"""
    try:
        return d.get(key, "")
    except AttributeError:
        return ""


FLAG_MAP = {
    "en": "🇬🇧",
    "es": "🇪🇸",
    "de": "🇩🇪",
    "fr": "🇫🇷",
}


@register.simple_tag
def lang_flag(code):
    """Return an emoji flag for a language code."""
    if not code:
        return "🌐"
    return FLAG_MAP.get(code.lower(), "🌐")
