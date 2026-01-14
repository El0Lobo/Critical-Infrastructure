# app/bands/translation.py
from modeltranslation.translator import TranslationOptions, register

from .models import Band


@register(Band)
class BandTranslationOptions(TranslationOptions):
    """
    Translation configuration for Band model.

    Enables multi-language support for:
    - name: Band/artist name (if they use different names in different languages)
    - slug: SEO-friendly URL slugs per language
    - description: Full band/artist bio and description
    - contact_notes: Contact-related notes
    - comment_internal: Internal staff notes (optional translation)
    - seo_title: Custom SEO title per language
    - seo_description: Custom SEO description per language
    """

    fields = (
        "name",
        "slug",
        "description",
        "contact_notes",
        "comment_internal",
        "seo_title",
        "seo_description",
    )
    required_languages = {
        "en": ("name", "slug"),
    }
