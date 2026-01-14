from django.urls import path

from app.events import views

app_name = "events"


urlpatterns = [
    path("", views.index, name="index"),
    path("categories/create/", views.category_create, name="category_create"),
    path("categories/", views.categories, name="categories"),
    path("categories/<int:pk>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
    path("holidays/", views.holidays, name="holidays"),
    path("holidays/<int:pk>/edit/", views.holiday_edit, name="holiday_edit"),
    path("holidays/<int:pk>/delete/", views.holiday_delete, name="holiday_delete"),
    path("create/", views.create, name="create"),
    path("<slug:slug>/edit/", views.edit, name="edit"),
    path("<slug:slug>/occurrence/edit/", views.edit_occurrence, name="occurrence_edit"),
    path("<slug:slug>/occurrence/delete/", views.delete_occurrence, name="occurrence_delete"),
    path("<slug:slug>/delete/", views.delete, name="delete"),
    path("<slug:slug>/", views.detail, name="detail"),
]
