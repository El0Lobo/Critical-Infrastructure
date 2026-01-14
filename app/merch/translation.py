# app/merch/translation.py
from modeltranslation.translator import TranslationOptions, register

from .models import Category, Product, ProductImage, ProductVariant


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    """
    Translation configuration for Category model (merch categories).

    Enables multi-language support for:
    - name: Category name (e.g., "T-Shirts", "Posters", "Accessories")
    - slug: SEO-friendly URL slugs per language
    """

    fields = ("name", "slug")
    required_languages = {
        "en": ("name", "slug"),
    }


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    """
    Translation configuration for Product model.

    Enables multi-language support for:
    - name: Product name
    - slug: SEO-friendly URL slugs per language
    - description: Full product description
    """

    fields = ("name", "slug", "description")
    required_languages = {
        "en": ("name", "slug"),
    }


@register(ProductImage)
class ProductImageTranslationOptions(TranslationOptions):
    """
    Translation configuration for ProductImage model.

    Enables translation of alt text for product images (important for accessibility).
    """

    fields = ("alt_text",)


@register(ProductVariant)
class ProductVariantTranslationOptions(TranslationOptions):
    """
    Translation configuration for ProductVariant model.

    Enables translation of size labels and color names.
    """

    fields = ("size_label", "color")
