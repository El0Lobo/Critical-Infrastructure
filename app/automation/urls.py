from django.urls import path

from .views import create, edit, index

urlpatterns = [
    path("", index, name="automation_index"),
    path("create/", create, name="automation_create"),
    path("<slug:slug>/edit/", edit, name="automation_edit"),
]
