from django.urls import path

from .views import create, edit, index

urlpatterns = [
    path("", index, name="maps_index"),
    path("create/", create, name="maps_create"),
    path("<slug:slug>/edit/", edit, name="maps_edit"),
]
