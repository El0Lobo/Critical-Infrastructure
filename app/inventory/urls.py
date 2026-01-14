from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.manage, name="inventory_manage"),
    path("category/new/", views.category_create, name="inventory_category_new"),
    path("category/<slug:slug>/edit/", views.category_edit, name="inventory_category_edit"),
    path("item/new/", views.item_create, name="inventory_item_new"),
    path("item/<slug:slug>/edit/", views.item_edit, name="inventory_item_edit"),
    path("item/<slug:slug>/adjust/", views.adjust_stock, name="inventory_item_adjust"),
    path("item/<slug:slug>/reorder/", views.toggle_reorder, name="inventory_item_reorder"),
]
