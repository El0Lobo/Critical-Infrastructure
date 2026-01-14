from django.urls import path

from app.shifts import views

app_name = "shifts"


urlpatterns = [
    path("", views.index, name="index"),
    path("assign/<int:shift_id>/", views.assign, name="assign"),
    path("take/<int:shift_id>/", views.take, name="take"),
    path("template/create/", views.create_template, name="template_create"),
    path("template/<int:pk>/edit/", views.update_template, name="template_update"),
    path("template/<int:pk>/delete/", views.delete_template, name="template_delete"),
    path("manage/<slug:event_slug>/", views.manage_event, name="manage_event"),
]
