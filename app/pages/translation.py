# app/pages/translation.py
from modeltranslation.translator import TranslationOptions, register

from .models import Page


@register(Page)
class PageTranslationOptions(TranslationOptions):
    """
    Translation configuration for Page model.

    This enables multi-language support for:
    - title: Page title in each language
    - slug: SEO-friendly URL slugs per language
    - summary: Brief page description
    - body: Main WYSIWYG content
    - blocks: JSON block builder data (entire structure translated per language)
    """

    fields = ("title", "slug", "summary", "body", "blocks")
    required_languages = {
        "en": ("title", "slug"),
    }
