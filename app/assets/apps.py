# app/assets/apps.py
from django.apps import AppConfig


class AssetsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.assets"
    verbose_name = "Digital Assets"

    def ready(self):
        """Import signal handlers when app is ready."""
        import app.assets.signals  # noqa: F401
