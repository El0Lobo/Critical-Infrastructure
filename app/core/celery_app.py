import os

try:
    from celery import Celery
except ImportError:  # pragma: no cover - optional dependency in some environments
    Celery = None
    app = None
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.core.settings")
    app = Celery("baros")
    app.config_from_object("django.conf:settings", namespace="CELERY")
    app.autodiscover_tasks()
