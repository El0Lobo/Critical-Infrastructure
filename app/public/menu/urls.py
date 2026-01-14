from django.urls import path

from app.pages.views_public import menu as menu_page  # reuse existing view

app_name = "public_menu"

urlpatterns = [
    path("", menu_page, name="menu"),  # /menu/
]
