# app/users/urls.py
from django.urls import path

from . import views
from .views import ImpersonateStartView, ImpersonateStopView

app_name = "users"

urlpatterns = [
    path("", views.index, name="index"),
    path("create/", views.create_user, name="create"),
    path("profile/<int:user_id>/", views.profile_detail, name="profile"),
    path("profile/<int:user_id>/edit/", views.profile_edit, name="profile_edit"),
    path("cms/users/<int:user_id>/delete/", views.user_delete, name="delete"),
    # Badge CRUD
    path("badges/", views.badges_list, name="badges_list"),
    path("badges/new/", views.badges_create, name="badges_create"),
    path("badges/<int:pk>/edit/", views.badges_edit, name="badges_edit"),
    path("badges/<int:pk>/delete/", views.badges_delete, name="badges_delete"),
    path("impersonate/<int:user_id>/", ImpersonateStartView.as_view(), name="impersonate"),
    path("impersonate/stop/", ImpersonateStopView.as_view(), name="impersonate_stop"),
    path("groups/hierarchy/", views.group_hierarchy, name="group_hierarchy"),
    path("membership/settings/", views.membership_settings, name="membership_settings"),
    path("roles/settings/", views.roles_settings, name="roles_settings"),
]
