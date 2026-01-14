from django.urls import path

from . import public_views

app_name = "news_public"

urlpatterns = [
    path("news/", public_views.news_index, name="public_news_index"),
    path("news/<slug:slug>/", public_views.news_detail, name="public_news_detail"),
]
