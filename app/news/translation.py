# app/news/translation.py
from modeltranslation.translator import TranslationOptions, register

from .models import NewsPost


@register(NewsPost)
class NewsPostTranslationOptions(TranslationOptions):
    """
    Translation configuration for NewsPost model.

    Enables multi-language support for public-facing post content.
    """

    fields = ("title", "slug", "summary", "body", "category")
    required_languages = {
        "en": ("title", "slug"),
    }

