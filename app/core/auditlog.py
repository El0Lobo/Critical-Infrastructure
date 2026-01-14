"""Auditlog registration for tracking model changes."""

from auditlog.registry import auditlog
from django.contrib.auth import get_user_model

from app.assets.models import Asset, Collection
from app.assets.models import Tag as AssetTag
from app.events.models import Event, EventCategory, HolidayWindow
from app.setup.models import SiteSettings, VisibilityRule

User = get_user_model()

# Register models to be audited
auditlog.register(User, exclude_fields=["password", "last_login"])
auditlog.register(Asset)
auditlog.register(Collection)
auditlog.register(AssetTag)
auditlog.register(Event)
auditlog.register(EventCategory)
auditlog.register(HolidayWindow)
auditlog.register(VisibilityRule)
auditlog.register(SiteSettings)
