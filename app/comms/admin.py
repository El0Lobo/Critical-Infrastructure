from django.contrib import admin

from . import models


@admin.register(models.MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "type",
        "account",
        "subject",
        "created_at",
        "last_activity_at",
        "is_closed",
    )
    list_filter = ("type", "is_closed", "account")
    search_fields = ("subject",)


@admin.register(models.Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "thread",
        "direction",
        "sender_user",
        "sent_at",
        "received_at",
        "created_at",
    )
    list_filter = ("direction",)
    search_fields = ("body_text", "body_html_sanitized")


@admin.register(models.Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("id", "account", "name", "slug", "is_system")
    list_filter = ("is_system", "account")
    search_fields = ("name", "slug")


@admin.register(models.Draft)
class DraftAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "account", "subject", "status", "updated_at")
    list_filter = ("status", "account")
    search_fields = ("subject", "body_text", "body_html")


@admin.register(models.Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "message",
        "filename",
        "mime_type",
        "size_bytes",
        "scan_status",
        "is_inline",
    )
    list_filter = ("scan_status", "is_inline", "mime_type")
    search_fields = ("filename",)


@admin.register(models.ReadReceipt)
class ReadReceiptAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "user", "read_at")
    list_filter = ("read_at",)
    search_fields = ("message__thread__subject", "user__username")


@admin.register(models.UserThreadState)
class UserThreadStateAdmin(admin.ModelAdmin):
    list_display = ("id", "thread", "user", "archived", "starred", "last_read_at")
    list_filter = ("archived", "starred")
    search_fields = ("thread__subject", "user__username")
