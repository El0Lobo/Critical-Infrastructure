from django.contrib import admin

from .models import BadgeDefinition, FieldPolicy, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "chosen_name", "role_title", "primary_group", "force_password_change")
    list_filter = ("primary_group", "force_password_change")
    search_fields = ("user__username", "chosen_name", "legal_name", "role_title")


@admin.register(BadgeDefinition)
class BadgeDefinitionAdmin(admin.ModelAdmin):
    list_display = ("name", "emoji", "description")
    search_fields = ("name", "emoji", "description")


@admin.register(FieldPolicy)
class FieldPolicyAdmin(admin.ModelAdmin):
    list_display = ("field_name", "visibility")
    list_filter = ("visibility",)
    search_fields = ("field_name",)
