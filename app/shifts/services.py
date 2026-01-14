"""Utility helpers for shift generation and synchronisation."""

from __future__ import annotations

from django.utils import timezone

from app.core.date_utils import add_months
from app.events.models import HolidayWindow
from app.events.scheduling import build_occurrence_series, refresh_event_schedule
from app.shifts.models import Shift, ShiftTemplate


def sync_event_standard_shifts(event, *, user=None, max_occurrences: int = 64) -> None:
    """Ensure standard shift template selections are reflected in actual shifts."""

    horizon_end = add_months(timezone.now(), 6)
    holiday_windows = list(HolidayWindow.overlapping(timezone.now(), horizon_end))
    event_exceptions = list(event.recurrence_exceptions.all())
    refresh_event_schedule(
        event,
        max_occurrences=max_occurrences,
        horizon_end=horizon_end,
        holiday_windows=holiday_windows,
        exceptions=event_exceptions,
    )
    occurrences = build_occurrence_series(
        event,
        max_occurrences=max_occurrences,
        include_past=False,
        horizon_end=horizon_end,
        holiday_windows=holiday_windows,
        exceptions=event_exceptions,
    )
    if not occurrences:
        fallback = build_occurrence_series(
            event,
            max_occurrences=1,
            include_past=True,
            horizon_end=horizon_end,
            holiday_windows=holiday_windows,
            exceptions=event_exceptions,
        )
        if fallback:
            occurrences = [fallback[-1]]

    template_ids = list(event.standard_shifts.values_list("id", flat=True))

    if not event.requires_shifts or not template_ids or not occurrences:
        event.shifts.filter(template__isnull=False).delete()
        return

    templates = {tmpl.id: tmpl for tmpl in ShiftTemplate.objects.filter(pk__in=template_ids)}

    existing_by_template = {
        (
            shift.template_id,
            shift.template_segment,
            shift.template_staff_position,
            shift.start_at,
        ): shift
        for shift in event.shifts.filter(template__isnull=False)
    }

    expected_keys = set()

    for occurrence in occurrences:
        context = occurrence.to_segment_context()
        for _template_id, template in templates.items():
            segments = template.segment_schedule(context)
            for segment in segments:
                segment_start = segment["start"]
                segment_end = segment["end"]
                for staff_index in range(1, max(template.capacity, 1) + 1):
                    key = (template.id, segment["index"], staff_index, segment_start)
                    expected_keys.add(key)
                    shift = existing_by_template.get(key)
                    title = segment["title"]
                    if template.capacity > 1:
                        title = f"{segment['title']} - Slot {staff_index}"
                    if shift:
                        shift.title = title
                        shift.description = template.description
                        shift.start_at = segment_start
                        shift.end_at = segment_end
                        shift.capacity = 1
                        shift.allow_signup = template.allow_signup
                        shift.visibility_key = template.visibility_key
                        shift.template = template
                        shift.template_segment = segment["index"]
                        shift.template_staff_position = staff_index
                        if user:
                            shift.updated_by = user
                        shift.save()
                    else:
                        Shift.objects.create(
                            event=event,
                            template=template,
                            template_segment=segment["index"],
                            template_staff_position=staff_index,
                            title=title,
                            description=template.description,
                            start_at=segment_start,
                            end_at=segment_end,
                            capacity=1,
                            allow_signup=template.allow_signup,
                            visibility_key=template.visibility_key,
                            created_by=user if user else None,
                            updated_by=user if user else None,
                        )

    # Remove shifts whose templates or segments are no longer selected
    for key, shift in existing_by_template.items():
        if key not in expected_keys:
            shift.delete()
