from django.urls import path

from .public_views import public_detail, public_list

urlpatterns = [
    path("events/", public_list, name="public_events"),
    path("events/sample-event/", public_detail, name="public_event_detail"),
]
