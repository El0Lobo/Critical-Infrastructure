# app/menu/translation.py
from modeltranslation.translator import TranslationOptions, register

from .models import Category, Item, ItemVariant, Unit, UnitGroup


@register(Unit)
class UnitTranslationOptions(TranslationOptions):
    """
    Translation configuration for Unit model.

    Enables translation of unit display names (e.g., "Liters", "grams").
    Code remains the same across languages (e.g., "L", "g").
    """

    fields = ("display",)


@register(UnitGroup)
class UnitGroupTranslationOptions(TranslationOptions):
    """
    Translation configuration for UnitGroup model.

    Enables translation of unit group names.
    """

    fields = ("name",)


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    """
    Translation configuration for Category model (menu categories).

    Enables multi-language support for:
    - name: Category name (e.g., "Beer", "Cocktails", "Snacks")
    - slug: SEO-friendly URL slugs per language
    """

    fields = ("name", "slug")
    required_languages = {
        "en": ("name", "slug"),
    }


@register(Item)
class ItemTranslationOptions(TranslationOptions):
    """
    Translation configuration for Item model (menu items).

    Enables multi-language support for:
    - name: Item name
    - slug: SEO-friendly URL slugs per language
    - description: Item description
    - allergens_note: Allergen information per language
    """

    fields = ("name", "slug", "description", "allergens_note")
    required_languages = {
        "en": ("name", "slug"),
    }


@register(ItemVariant)
class ItemVariantTranslationOptions(TranslationOptions):
    """
    Translation configuration for ItemVariant model.

    Enables translation of variant labels (e.g., "Small", "Large", "Draft").
    """

    fields = ("label",)
