from django.urls import path

from . import views

app_name = "news"

urlpatterns = [
    path("", views.feed, name="feed"),
    path("posts/create/", views.post_create, name="post_create"),
    path("posts/<int:pk>/edit/", views.post_edit, name="post_edit"),
    path("posts/<int:pk>/delete/", views.post_delete, name="post_delete"),
    path("posts/<slug:slug>/edit/", views.post_edit_legacy, name="post_edit_legacy"),
    path("posts/<slug:slug>/delete/", views.post_delete_legacy, name="post_delete_legacy"),
    path("polls/create/", views.poll_create, name="poll_create"),
    path("polls/<uuid:pk>/edit/", views.poll_edit, name="poll_edit"),
    path("polls/<uuid:pk>/delete/", views.poll_delete, name="poll_delete"),
    path("polls/<uuid:pk>/vote/", views.poll_vote, name="poll_vote"),
]
