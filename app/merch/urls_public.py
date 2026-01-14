from django.urls import path

from . import views

app_name = "merch_public"

urlpatterns = [
    path("store/", views.store_index, name="shop_index"),
    path("store/c/<slug:slug>/", views.store_category, name="shop_category"),
    path("store/p/<slug:slug>/", views.store_detail, name="shop_detail"),
]
