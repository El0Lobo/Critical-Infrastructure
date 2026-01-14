# app/pages/urls_public.py
from django.urls import path

from . import views_public as views

app_name = "public"

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.CMSLoginView.as_view(), name="login"),
    path("<slug:slug>/", views.page_detail, name="page-detail"),
]
