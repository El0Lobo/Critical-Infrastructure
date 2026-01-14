from django.contrib import admin

from app.events.models import (
    Event,
    EventCategory,
    EventPerformer,
    EventRecurrenceException,
    HolidayWindow,
)


class EventPerformerInline(admin.TabularInline):
    model = EventPerformer
    extra = 0
    autocomplete_fields = ["band"]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "event_type", "starts_at", "status", "requires_shifts", "featured"]
    list_filter = [
        "event_type",
        "status",
        "recurrence_frequency",
        "requires_shifts",
        "featured",
        "categories",
    ]
    search_fields = ["title", "teaser"]
    inlines = [EventPerformerInline]
    filter_horizontal = ["categories"]
    autocomplete_fields = ["created_by", "updated_by"]
    prepopulated_fields = {"slug": ("title",)}


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active"]
    search_fields = ["name", "slug"]


@admin.register(HolidayWindow)
class HolidayWindowAdmin(admin.ModelAdmin):
    list_display = ["name", "starts_at", "ends_at", "applies_to_public", "applies_to_internal"]
    list_filter = ["applies_to_public", "applies_to_internal"]
    search_fields = ["name", "note"]


@admin.register(EventRecurrenceException)
class EventRecurrenceExceptionAdmin(admin.ModelAdmin):
    list_display = ["event", "occurrence_start", "exception_type", "override_event"]
    search_fields = ["event__title"]
    list_filter = ["exception_type"]
