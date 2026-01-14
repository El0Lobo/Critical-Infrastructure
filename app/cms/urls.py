from django.urls import path

from .views import account, dashboard

urlpatterns = [
    path("dashboard/", dashboard, name="dashboard"),
    path("account/", account, name="account"),
]
