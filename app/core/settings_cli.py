from .settings import *  # noqa

INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "django_ckeditor_5"]
