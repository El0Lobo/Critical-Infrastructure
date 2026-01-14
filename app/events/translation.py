# app/events/translation.py
from modeltranslation.translator import TranslationOptions, register

from .models import Event, EventCategory, EventPerformer, HolidayWindow


@register(EventCategory)
class EventCategoryTranslationOptions(TranslationOptions):
    """
    Translation configuration for EventCategory model.

    Enables multi-language support for event categories (e.g., "Live Band", "DJ Night").
    """

    fields = ("name", "slug", "description")
    required_languages = {
        "en": ("name", "slug"),
    }


@register(Event)
class EventTranslationOptions(TranslationOptions):
    """
    Translation configuration for Event model.

    This enables multi-language support for:
    - title: Event title in each language
    - slug: SEO-friendly URL slugs per language
    - teaser: Short summary for cards and social previews
    - description_public: Full event description shown to visitors
    - description_internal: Staff notes (not translated by default, but available if needed)
    - seo_title: Custom SEO title per language
    - seo_description: Custom SEO description per language
    - venue_name: Venue name if different per language
    """

    fields = (
        "title",
        "slug",
        "teaser",
        "description_public",
        "description_internal",
        "seo_title",
        "seo_description",
        "venue_name",
    )
    required_languages = {
        "en": ("title", "slug"),
    }


@register(EventPerformer)
class EventPerformerTranslationOptions(TranslationOptions):
    """
    Translation configuration for EventPerformer model.

    Enables translation of performer display names and notes.
    """

    fields = ("display_name", "performer_type", "notes")


@register(HolidayWindow)
class HolidayWindowTranslationOptions(TranslationOptions):
    """
    Translation configuration for HolidayWindow model.

    Enables translation of holiday window names and notes.
    """

    fields = ("name", "note")
