from django.urls import path

from . import views

app_name = "merch"

urlpatterns = [
    path("", views.manage, name="manage"),
    path("category/new/", views.category_new, name="category_new"),
    path("category/<int:pk>/edit/", views.category_edit, name="category_edit"),
    path("category/<int:pk>/delete/", views.category_delete, name="category_delete"),
    path("product/new/", views.product_create, name="product_create"),
    path("product/<slug:slug>/edit/", views.product_edit, name="product_edit"),
    path("product/<slug:slug>/delete/", views.product_delete, name="product_delete"),
]
