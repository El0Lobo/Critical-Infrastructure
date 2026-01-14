from django.urls import path

from . import views

app_name = "menu_public"

urlpatterns = [
    path("", views.public_menu_index, name="index"),
    path("c/<slug:slug>/", views.public_category, name="category"),
]
