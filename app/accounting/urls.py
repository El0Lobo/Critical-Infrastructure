from django.urls import path

from .views import create, edit, index

urlpatterns = [
    path("", index, name="accounting_index"),
    path("create/", create, name="accounting_create"),
    path("<slug:slug>/edit/", edit, name="accounting_edit"),
]
