# app/bands/urls.py
from django.urls import path

from . import views

app_name = "bands"
urlpatterns = [
    path("cms/bands/", views.index, name="index"),
    path("cms/bands/new/", views.edit, name="new"),
    path("cms/bands/<int:pk>/edit/", views.edit, name="edit"),
    path("cms/bands/<int:pk>/delete/", views.delete, name="delete"),
]
