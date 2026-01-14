from django.urls import path

from . import public_views

app_name = "bands_public"

urlpatterns = [
    path("bands/", public_views.public_list, name="public_list"),
    path("bands/<slug:slug>/", public_views.public_detail, name="public_detail"),
]
