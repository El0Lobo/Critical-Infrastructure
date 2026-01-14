from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.core"

    def ready(self):
        """Import auditlog configuration when app is ready."""
        import app.core.auditlog  # noqa: F401
