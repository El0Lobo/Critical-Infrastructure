from django.urls import path

from . import views_compose, views_inbox, views_mail, views_threads

urlpatterns = [
    path("", views_inbox.inbox, name="inbox"),
    path("t/<int:thread_id>/", views_threads.detail, name="thread_detail"),
    path("t/<int:thread_id>/modal/", views_threads.modal, name="thread_modal"),
    path("t/<int:thread_id>/archive/", views_threads.archive, name="thread_archive"),
    path("t/<int:thread_id>/unarchive/", views_threads.unarchive, name="thread_unarchive"),
    path("t/<int:thread_id>/labels/", views_threads.labels, name="thread_labels"),
    path("t/<int:thread_id>/reply/internal/", views_threads.reply_internal, name="reply_internal"),
    path("compose/", views_compose.compose_internal, name="compose_internal"),
    path(
        "compose/internal/modal/",
        views_compose.compose_internal_modal,
        name="compose_internal_modal",
    ),
    path("compose/email/", views_mail.compose_email_modal, name="compose_email_modal"),
    path("t/<int:thread_id>/reply/email/", views_mail.reply_email_modal, name="reply_email_modal"),
]
