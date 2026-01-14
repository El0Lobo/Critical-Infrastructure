from django.urls import path

from . import views

app_name = "menu"

urlpatterns = [
    path("categories/", views.cms_categories_list, name="categories_list"),
    path("categories/new/", views.cms_category_create, name="category_create"),
    path("categories/<slug:slug>/edit/", views.cms_category_edit, name="category_edit"),
    path("items/", views.cms_items_list, name="items_list"),
    path("items/new/", views.cms_item_create, name="item_create"),
    path("items/<slug:slug>/edit/", views.cms_item_edit, name="item_edit"),
    path("tags/", views.cms_tags_list, name="tags_list"),
    path("settings/", views.cms_settings, name="settings"),
    path("items/bulk/publish/", views.cms_items_bulk_publish, name="items_bulk_publish"),
    path("items/bulk/soldout/", views.cms_items_bulk_soldout, name="items_bulk_soldout"),
    path("items/bulk/newbadge/", views.cms_items_bulk_newbadge, name="items_bulk_newbadge"),
]
