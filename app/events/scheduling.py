"""Utility functions for computing event occurrences and schedules."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

from django.utils import timezone

from app.events.models import Event, EventRecurrenceException, HolidayWindow


@dataclass(frozen=True)
class EventOccurrenceData:
    """Computed occurrence for an event (without persisting to DB)."""

    event: Event
    start: datetime
    doors: datetime | None
    end: datetime | None
    curfew: datetime | None
    is_override: bool = False
    source_exception: EventRecurrenceException | None = None

    def to_segment_context(self):
        """Return a lightweight object mimicking an Event for template scheduling."""

        return SimpleNamespace(
            starts_at=self.start,
            doors_at=self.doors,
            ends_at=self.end,
            curfew_at=self.curfew,
        )


def _ensure_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if timezone.is_naive(value):
        return timezone.make_aware(value, timezone.get_current_timezone())
    return value


def _apply_offset(start: datetime, offset: timedelta | None) -> datetime | None:
    if offset is None:
        return None
    return start + offset


def _increment_month(year: int, month: int) -> tuple[int, int]:
    month += 1
    if month > 12:
        month = 1
        year += 1
    return year, month


def _nth_weekday_of_month(year: int, month: int, weekday: int, nth: int) -> int:
    cal = calendar.Calendar()
    days = [
        day
        for day in cal.itermonthdates(year, month)
        if day.month == month and day.weekday() == weekday
    ]
    if not days:
        return 1
    index = nth - 1
    if index >= len(days):
        # Fallback to the last existing weekday in the month when nth is too large (e.g. 5th Thursday).
        return days[-1].day
    return days[index].day


def _next_occurrence_start(event: Event, current: datetime) -> datetime | None:
    freq = event.recurrence_frequency
    tz = timezone.get_current_timezone()
    if freq == Event.RecurrenceFrequency.NONE:
        return None

    if freq == Event.RecurrenceFrequency.WEEKLY:
        next_start = current + timedelta(weeks=1)
        if event.recurrence_weekday is not None:
            delta = (event.recurrence_weekday - next_start.weekday()) % 7
            next_start += timedelta(days=delta)
        return next_start

    if freq == Event.RecurrenceFrequency.BIWEEKLY:
        next_start = current + timedelta(weeks=2)
        if event.recurrence_weekday is not None:
            delta = (event.recurrence_weekday - next_start.weekday()) % 7
            next_start += timedelta(days=delta)
        return next_start

    current_local = timezone.localtime(current, tz)

    if freq == Event.RecurrenceFrequency.MONTHLY_DATE:
        day = event.recurrence_day_of_month or current_local.day
        year, month = _increment_month(current_local.year, current_local.month)
        max_day = calendar.monthrange(year, month)[1]
        day = min(day, max_day)
        new_local = current_local.replace(year=year, month=month, day=day)
        return timezone.make_aware(new_local.replace(tzinfo=None), tz)

    if freq == Event.RecurrenceFrequency.MONTHLY_WEEKDAY:
        weekday = (
            event.recurrence_weekday
            if event.recurrence_weekday is not None
            else current_local.weekday()
        )
        week_number = event.recurrence_week_of_month or 1
        year, month = _increment_month(current_local.year, current_local.month)
        day = _nth_weekday_of_month(year, month, weekday, week_number)
        new_local = current_local.replace(year=year, month=month, day=day)
        return timezone.make_aware(new_local.replace(tzinfo=None), tz)

    return None


def _initial_start(event: Event) -> datetime | None:
    if event.recurrence_frequency == Event.RecurrenceFrequency.NONE:
        return _ensure_aware(event.starts_at)
    return _ensure_aware(event.recurrence_next_start_at or event.starts_at)


def _compute_offsets(
    event: Event,
) -> tuple[timedelta | None, timedelta | None, timedelta | None]:
    reference = _ensure_aware(event.starts_at or event.recurrence_next_start_at)

    def offset(value: datetime | None) -> timedelta | None:
        value = _ensure_aware(value)
        if value is None or reference is None:
            return None
        return value - reference

    return offset(event.doors_at), offset(event.ends_at), offset(event.curfew_at)


def build_occurrence_series(
    event: Event,
    *,
    max_occurrences: int = 6,
    include_past: bool = False,
    horizon_end: datetime | None = None,
    exceptions: Sequence[EventRecurrenceException] | None = None,
    holiday_windows: Sequence[HolidayWindow] | None = None,
) -> list[EventOccurrenceData]:
    """Return upcoming occurrences for an event based on its recurrence settings."""

    start = _initial_start(event)
    if start is None:
        return []

    now = timezone.now()
    doors_offset, ends_offset, curfew_offset = _compute_offsets(event)
    occurrences: list[EventOccurrenceData] = []
    horizon = _ensure_aware(horizon_end)
    exception_map = {}
    if exceptions:
        for item in exceptions:
            key = _ensure_aware(item.occurrence_start)
            if key:
                exception_map[key] = item
    holiday_list = list(holiday_windows or [])

    def blocked_by_holiday(start_dt: datetime) -> bool:
        if not holiday_list or not event.is_recurring:
            return False
        for window in holiday_list:
            applies = (event.event_type == Event.EventType.PUBLIC and window.applies_to_public) or (
                event.event_type == Event.EventType.INTERNAL and window.applies_to_internal
            )
            if not applies:
                continue
            window_start = _ensure_aware(window.starts_at)
            window_end = _ensure_aware(window.ends_at)
            if not window_start or not window_end:
                continue
            if window_start <= start_dt <= window_end:
                return True
        return False

    if event.recurrence_frequency == Event.RecurrenceFrequency.NONE:
        occurrence = EventOccurrenceData(
            event=event,
            start=start,
            doors=_apply_offset(start, doors_offset),
            end=_apply_offset(start, ends_offset),
            curfew=_apply_offset(start, curfew_offset),
        )
        if (not horizon or occurrence.start <= horizon) and (
            include_past or occurrence.start >= now
        ):
            occurrences.append(occurrence)
        return occurrences

    attempts = 0
    current = start
    while attempts < max_occurrences * 6:
        attempts += 1
        if horizon and current > horizon:
            break

        exception = exception_map.get(current)
        if exception and exception.override_event:
            override = exception.override_event
            override_start = _ensure_aware(override.starts_at) or current
            occurrence = EventOccurrenceData(
                event=override,
                start=override_start,
                doors=_ensure_aware(override.doors_at),
                end=_ensure_aware(override.ends_at),
                curfew=_ensure_aware(override.curfew_at),
                is_override=True,
                source_exception=exception,
            )
            if horizon and occurrence.start > horizon:
                break
            if include_past or occurrence.start >= now:
                occurrences.append(occurrence)
                if len(occurrences) >= max_occurrences:
                    break
        elif exception:
            # Skip this occurrence entirely (skip/holiday).
            pass
        else:
            if blocked_by_holiday(current):
                next_start = _next_occurrence_start(event, current)
                if not next_start or next_start == current:
                    break
                current = next_start
                continue
            occurrence = EventOccurrenceData(
                event=event,
                start=current,
                doors=_apply_offset(current, doors_offset),
                end=_apply_offset(current, ends_offset),
                curfew=_apply_offset(current, curfew_offset),
            )
            if include_past or occurrence.start >= now:
                occurrences.append(occurrence)
                if len(occurrences) >= max_occurrences:
                    break

        next_start = _next_occurrence_start(event, current)
        if not next_start or next_start == current:
            break
        current = next_start

    return occurrences


def refresh_event_schedule(
    event: Event,
    *,
    max_occurrences: int = 6,
    horizon_end: datetime | None = None,
    holiday_windows: Sequence[HolidayWindow] | None = None,
    exceptions: Sequence[EventRecurrenceException] | None = None,
) -> list[EventOccurrenceData]:
    """Recalculate and persist the next scheduled start if needed, returning occurrences."""

    occurrences = build_occurrence_series(
        event,
        max_occurrences=max_occurrences,
        include_past=True,
        horizon_end=horizon_end,
        holiday_windows=holiday_windows,
        exceptions=exceptions,
    )
    next_start = None
    now = timezone.now()
    for occurrence in occurrences:
        if occurrence.start >= now:
            next_start = occurrence.start
            break

    if event.is_recurring:
        if event.recurrence_next_start_at != next_start:
            Event.objects.filter(pk=event.pk).update(recurrence_next_start_at=next_start)
            event.recurrence_next_start_at = next_start
    else:
        # For single events, clear any stale recurrence pointer.
        if event.recurrence_next_start_at:
            Event.objects.filter(pk=event.pk).update(recurrence_next_start_at=None)
            event.recurrence_next_start_at = None

    return occurrences
