# Register custom modeltranslation field types before app initialization
from . import modeltranslation_fields  # noqa

from .celery_app import app as celery_app  # noqa
