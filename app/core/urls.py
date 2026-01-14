from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from app.pages.views_public import CMSLoginView, dev_force_login

from .views import health, set_language

# Non-translated URLs (admin, API, health checks, CMS admin interface)
urlpatterns = [
    # Admin & health
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("api/v1/", include("app.api.urls")),
    # Auth
    path("accounts/login/", CMSLoginView.as_view(), name="login"),
    path("accounts/dev-login/", dev_force_login, name="dev_force_login"),
    path("accounts/", include("django.contrib.auth.urls")),
    # Language switching (works for both CMS and public site) - custom view
    path("i18n/setlang/", set_language, name="set_language"),
    # Rosetta for managing translations (admin only)
    path("rosetta/", include("rosetta.urls")),
    # -------- CMS (admin interface - not language-prefixed) --------
    path("cms/", include("app.cms.urls")),
    path("cms/pages/", include("app.pages.urls")),
    path("cms/ckeditor5/", include("django_ckeditor_5.urls")),
    path("cms/news/", include("app.news.urls")),
    path("cms/events/", include("app.events.urls")),
    path("cms/shifts/", include("app.shifts.urls")),
    path("cms/door/", include("app.door.urls")),
    path("cms/merch/", include(("app.merch.urls", "merch"), namespace="merch")),
    path("cms/inventory/", include(("app.inventory.urls", "inventory"), namespace="inventory")),
    path("cms/accounting/", include("app.accounting.urls")),
    path("cms/social/", include("app.social.urls")),
    path("cms/automation/", include("app.automation.urls")),
    path("cms/maps/", include("app.maps.urls")),
    path("cms/settings/", include("app.setup.urls")),
    path("cms/users/", include("app.users.urls")),
    path("cms/menu/", include(("app.menu.urls", "menu"), namespace="menu")),
    path("cms/assets/", include("app.assets.urls")),
    path("cms/inbox/", include(("app.comms.urls", "comms"), namespace="comms")),
    path("cms/pos/", include("app.pos.urls", namespace="pos")),
    path("", include(("app.bands.urls", "bands"), namespace="bands")),
]

# Language-prefixed URLs (public-facing content)
# These will be available at /en/, /es/, /de/, /fr/, etc.
urlpatterns += i18n_patterns(
    # Main public site (pages)
    path("", include(("app.pages.urls_public", "public"), namespace="public")),
    # Public merch (e.g. /en/shop/…, /es/tienda/…)
    path("", include(("app.merch.urls_public", "merch_public"), namespace="merch_public")),
    path("", include(("app.news.public_urls", "news_public"), namespace="news_public")),
    path("", include("app.bands.public_urls", namespace="bands_pub")),
    prefix_default_language=True,  # Include /en/ prefix for English too
)

# Media during development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
