from django.urls import path

from . import api_views
from .views import create, delete, edit, index, login_page_redirect, preview, toggle_status

urlpatterns = [
    path("", index, name="pages_index"),
    path("create/", create, name="pages_create"),
    path("preview/", preview, name="pages_preview"),
    path("login/edit/", login_page_redirect, name="pages_login_edit"),
    path("api/events/", api_views.events_feed, name="pages_api_events"),
    path("api/menu/", api_views.menu_snapshot, name="pages_api_menu"),
    path("api/site/", api_views.site_context, name="pages_api_site"),
    path("api/assets/", api_views.assets_library, name="pages_api_assets"),
    path("api/assets/upload/", api_views.upload_inline_asset, name="pages_api_asset_upload"),
    path("api/assets/fonts/upload/", api_views.upload_font_asset, name="pages_api_font_upload"),
    path("api/pages/", api_views.page_create, name="pages_api_create"),
    path("api/pages/<slug:slug>/", api_views.page_detail, name="pages_api_detail"),
    path("api/preview/html/", api_views.preview_html, name="pages_api_preview_html"),
    path("<slug:slug>/edit/", edit, name="pages_edit"),
    path("<slug:slug>/delete/", delete, name="pages_delete"),
    path("<slug:slug>/toggle-status/", toggle_status, name="pages_toggle_status"),
]
