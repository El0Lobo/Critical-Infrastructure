from django.urls import path

from . import views

app_name = "menu"

urlpatterns = [
    path("", views.manage_menu, name="manage"),  # resolves to /cms/menu/
    path("items/", views.items_list, name="items_list"),
    path("categories/new/", views.category_create, name="category_create"),
    path(
        "categories/<slug:parent_slug>/new/", views.category_create, name="category_create_child"
    ),
    path("categories/<slug:slug>/edit/", views.category_edit, name="category_edit"),
    path("categories/<slug:slug>/delete/", views.category_delete, name="category_delete"),
    path("items/new/<slug:parent_slug>/", views.item_create, name="item_create_here"),
    path("items/<slug:slug>/edit/", views.item_edit, name="item_edit"),
    path("item/<slug:slug>/delete/", views.item_delete, name="item_delete"),
]
