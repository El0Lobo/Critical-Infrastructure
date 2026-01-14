# app/assets/urls.py
from django.urls import path

from . import views

app_name = "assets"

urlpatterns = [
    path("", views.assets_index, name="index"),
    path("toggle/<int:pk>/", views.asset_toggle_visibility, name="toggle_visibility"),
    path("rename/<int:pk>/", views.asset_rename, name="rename"),
    path(
        "collections/toggle/<int:pk>/",
        views.collection_toggle_visibility,
        name="collection_toggle_visibility",
    ),
    path("collections/rename/<int:pk>/", views.collection_rename, name="collection_rename"),
    path("collections/update/<int:pk>/", views.collection_update, name="collection_update"),
    path("collection/<int:pk>/delete/", views.collection_delete, name="collection_delete"),
    path("asset/<int:pk>/data/", views.asset_data, name="asset_data"),
    path("asset/<int:pk>/update/", views.asset_update, name="asset_update"),
    path("asset/<int:pk>/delete/", views.asset_delete, name="asset_delete"),
    path("file/<int:pk>/", views.asset_file, name="asset_file"),
]
