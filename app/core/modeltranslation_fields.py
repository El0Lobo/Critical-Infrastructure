# app/core/modeltranslation_fields.py
"""
Custom field registration for modeltranslation to support CKEditor5Field.
This file patches modeltranslation to recognize CKEditor5Field as a translatable field.
"""

from django.db import models
from django_ckeditor_5.fields import CKEditor5Field


# Monkey-patch CKEditor5Field to inherit from TextField for modeltranslation purposes
# This is the cleanest way to make modeltranslation recognize it as a supported field
def patch_modeltranslation():
    """
    Patch modeltranslation to support CKEditor5Field.

    We make CKEditor5Field a subclass of TextField in the MRO for modeltranslation's
    field type checking, while keeping all CKEditor5 functionality intact.
    """
    # Add TextField to CKEditor5Field's bases if not already there
    if models.TextField not in CKEditor5Field.__bases__:
        # Insert TextField into the inheritance hierarchy
        # This makes isinstance(field, TextField) return True for CKEditor5Field
        CKEditor5Field.__bases__ = (models.TextField,) + CKEditor5Field.__bases__


# Apply the patch when this module is imported
patch_modeltranslation()
