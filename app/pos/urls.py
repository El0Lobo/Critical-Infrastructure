from django.urls import path

from . import views

app_name = "pos"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    # API endpoints (AJAX):
    path("api/items/search/", views.api_search_items, name="api_search_items"),
    path("api/cart/add/", views.api_cart_add, name="api_cart_add"),
    path("api/cart/remove/", views.api_cart_remove, name="api_cart_remove"),
    path("api/items/browse/", views.api_browse_items, name="api_browse_items"),
    path("api/cart/update/", views.api_cart_update, name="api_cart_update"),
    path("api/cart/clear/", views.api_cart_clear, name="api_cart_clear"),
    path("api/cart/apply-discount/", views.api_cart_apply_discount, name="api_cart_apply_discount"),
    path("api/cart/totals/", views.api_cart_totals, name="api_cart_totals"),
    path("api/checkout/", views.api_checkout, name="api_checkout"),
    path("api/quick-buttons/", views.api_quick_buttons, name="api_quick_buttons"),
]
