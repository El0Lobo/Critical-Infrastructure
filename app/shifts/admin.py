from django.contrib import admin

from app.shifts.models import (
    Shift,
    ShiftAssignment,
    ShiftPreset,
    ShiftPresetSlot,
    ShiftTemplate,
)


class ShiftPresetSlotInline(admin.TabularInline):
    model = ShiftPresetSlot
    extra = 1


@admin.register(ShiftPreset)
class ShiftPresetAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_default"]
    search_fields = ["name", "slug"]
    inlines = [ShiftPresetSlotInline]


@admin.register(ShiftPresetSlot)
class ShiftPresetSlotAdmin(admin.ModelAdmin):
    list_display = ["title", "preset", "order", "start_offset_minutes", "duration_minutes"]
    search_fields = ["title", "preset__name"]
    list_filter = ["preset"]


@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "order",
        "start_reference",
        "capacity",
        "segment_count",
        "start_offset_minutes",
        "end_offset_minutes",
        "duration_minutes",
    ]
    search_fields = ["name", "slug"]
    ordering = ["order", "name"]


class ShiftAssignmentInline(admin.TabularInline):
    model = ShiftAssignment
    extra = 0
    autocomplete_fields = ["user", "assigned_by"]


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "event",
        "template",
        "template_segment",
        "template_staff_position",
        "start_at",
        "end_at",
        "status",
    ]
    list_filter = ["status", "allow_signup", "event__title", "template"]
    search_fields = ["title", "event__title", "template__name"]
    autocomplete_fields = ["event", "preset_slot", "template", "created_by", "updated_by"]
    inlines = [ShiftAssignmentInline]


@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ["shift", "user", "status", "assigned_at"]
    list_filter = ["status"]
    search_fields = ["shift__title", "user__username", "user__first_name", "user__last_name"]
