"""Event domain models."""

from datetime import datetime, timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class EventCategory(models.Model):
    """High level labels (e.g. live band, DJ night, flea market)."""

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140)
    description = models.TextField(blank=True)
    color = models.CharField(
        max_length=16,
        blank=True,
        help_text="Optional hex color (without #) used for UI accents.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.name


class Event(models.Model):
    """Represents a public- or internal-facing happening at the venue."""

    class EventType(models.TextChoices):
        PUBLIC = "public", "Public"
        INTERNAL = "internal", "Internal"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SCHEDULED = "scheduled", "Scheduled"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"
        CANCELLED = "cancelled", "Cancelled"

    class RecurrenceFrequency(models.TextChoices):
        NONE = "none", "Does not repeat"
        WEEKLY = "weekly", "Weekly"
        BIWEEKLY = "biweekly", "Every other week"
        MONTHLY_DATE = "monthly_date", "Monthly (specific date)"
        MONTHLY_WEEKDAY = "monthly_weekday", "Monthly (weekday, e.g. 1st Thursday)"

    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    class WeekOfMonth(models.IntegerChoices):
        FIRST = 1, "First"
        SECOND = 2, "Second"
        THIRD = 3, "Third"
        FOURTH = 4, "Fourth"
        FIFTH = 5, "Fifth"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    event_type = models.CharField(
        max_length=20, choices=EventType.choices, default=EventType.PUBLIC
    )
    hero_image = models.ImageField(upload_to="events/hero/", blank=True, null=True)
    teaser = models.CharField(
        max_length=280,
        blank=True,
        help_text="Short summary for cards, social previews, SEO descriptions.",
    )
    description_public = models.TextField(
        blank=True, help_text="Markdown or HTML rendered on the public site."
    )
    description_internal = models.TextField(
        blank=True,
        help_text="Staff-only notes (door team briefings, settlement notes, etc.)",
    )

    categories = models.ManyToManyField(
        EventCategory,
        blank=True,
        related_name="events",
        help_text="Pick all that apply (used for filtering and SEO markup).",
    )

    doors_at = models.DateTimeField(blank=True, null=True)
    starts_at = models.DateTimeField(blank=True, null=True)
    ends_at = models.DateTimeField(blank=True, null=True)
    curfew_at = models.DateTimeField(blank=True, null=True)
    recurrence_frequency = models.CharField(
        max_length=32,
        choices=RecurrenceFrequency.choices,
        default=RecurrenceFrequency.NONE,
    )
    recurrence_parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="recurrence_overrides",
        blank=True,
        null=True,
        help_text="If set, this event overrides a single occurrence of the parent recurrence.",
    )
    recurrence_parent_start = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Original start datetime for the overridden occurrence.",
    )
    recurrence_weekday = models.PositiveSmallIntegerField(
        choices=Weekday.choices,
        blank=True,
        null=True,
        help_text="Weekday used for recurring patterns.",
    )
    recurrence_week_of_month = models.PositiveSmallIntegerField(
        choices=WeekOfMonth.choices,
        blank=True,
        null=True,
        help_text="Which week (1st, 2nd, etc.) of the month for weekday-based recurrences.",
    )
    recurrence_day_of_month = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        help_text="Specific day of the month (1-31) for date-based recurrences.",
    )
    recurrence_next_start_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Optional next scheduled start when managing recurring series.",
    )
    manual_occurrences = models.JSONField(
        blank=True,
        default=list,
        help_text="Optional list of manual occurrence datetimes (ISO).",
    )

    ticket_url = models.URLField(blank=True)
    ticket_price_from = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    ticket_price_to = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    is_free = models.BooleanField(default=False)

    requires_shifts = models.BooleanField(
        default=False,
        help_text="If checked, event will appear in the shift planner.",
    )
    standard_shifts = models.ManyToManyField(
        "shifts.ShiftTemplate",
        blank=True,
        related_name="events",
        help_text="Select standard shifts (door, bar, etc.) to generate for this event.",
    )

    venue_name = models.CharField(max_length=200, blank=True)
    venue_address = models.CharField(max_length=255, blank=True)
    venue_postal_code = models.CharField(max_length=32, blank=True)
    venue_city = models.CharField(max_length=120, blank=True)
    venue_country = models.CharField(max_length=120, blank=True)
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=160, blank=True)

    visibility_key = models.CharField(
        max_length=120,
        blank=True,
        help_text="Visibility rule key (managed via the setup visibility cogs).",
    )

    featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    archived_at = models.DateTimeField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="events_created",
        blank=True,
        null=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="events_updated",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-starts_at", "title"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:220]
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        if self.status in {self.Status.CANCELLED, self.Status.ARCHIVED} and not self.archived_at:
            self.archived_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("events:detail", args=[self.slug])

    @property
    def is_recurring(self) -> bool:
        return self.recurrence_frequency != self.RecurrenceFrequency.NONE

    @property
    def is_override(self) -> bool:
        return self.recurrence_parent_id is not None

    @property
    def has_manual_occurrences(self) -> bool:
        return bool(self.manual_occurrences)

    def manual_occurrence_datetimes(self) -> list[datetime]:
        items = self.manual_occurrences or []
        if not isinstance(items, list):
            return []
        tz = timezone.get_current_timezone()
        parsed: list[datetime] = []
        for raw in items:
            if not raw:
                continue
            if isinstance(raw, datetime):
                dt = raw
            else:
                try:
                    dt = datetime.fromisoformat(str(raw))
                except (TypeError, ValueError):
                    continue
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, tz)
            else:
                dt = timezone.localtime(dt, tz)
            parsed.append(dt)
        return sorted(parsed)

    def build_occurrence_slug(self, occurrence_start: datetime) -> str:
        """Generate a slug for a single-occurrence override."""

        if timezone.is_naive(occurrence_start):
            occurrence_start = timezone.make_aware(
                occurrence_start, timezone.get_current_timezone()
            )
        suffix = timezone.localtime(occurrence_start).strftime("%Y%m%d%H%M")
        base = f"{self.slug}-{suffix}"
        slug = base[:220]
        counter = 1
        while Event.objects.filter(slug=slug).exists():
            slug = f"{base}-{counter}"[:220]
            counter += 1
        return slug

    def clone_for_occurrence(self, occurrence_start: datetime) -> "Event":
        """Create a detached event for a specific occurrence."""

        reference = self.starts_at or self.recurrence_next_start_at or occurrence_start

        def offset(value: datetime | None) -> timedelta | None:
            if value is None or reference is None:
                return None
            return value - reference

        doors_offset = offset(self.doors_at)
        ends_offset = offset(self.ends_at)
        curfew_offset = offset(self.curfew_at)

        if timezone.is_naive(occurrence_start):
            occurrence_start = timezone.make_aware(
                occurrence_start, timezone.get_current_timezone()
            )

        clone = Event.objects.get(pk=self.pk)
        clone.pk = None
        clone.slug = self.build_occurrence_slug(occurrence_start)
        clone.recurrence_frequency = Event.RecurrenceFrequency.NONE
        clone.recurrence_weekday = None
        clone.recurrence_week_of_month = None
        clone.recurrence_day_of_month = None
        clone.recurrence_next_start_at = None
        clone.recurrence_parent = self
        clone.recurrence_parent_start = occurrence_start
        clone.starts_at = occurrence_start
        clone.doors_at = occurrence_start + doors_offset if doors_offset else None
        clone.ends_at = occurrence_start + ends_offset if ends_offset else None
        clone.curfew_at = occurrence_start + curfew_offset if curfew_offset else None
        clone.save()

        clone.categories.set(self.categories.all())
        clone.standard_shifts.set(self.standard_shifts.all())

        for performer in self.performers.all():
            EventPerformer.objects.create(
                event=clone,
                band=performer.band,
                display_name=performer.display_name,
                performer_type=performer.performer_type,
                slot_starts_at=performer.slot_starts_at,
                slot_ends_at=performer.slot_ends_at,
                order=performer.order,
                notes=performer.notes,
            )

        return clone

    def get_recurrence_weekday_display(self) -> str:
        if self.recurrence_weekday is None:
            return ""
        try:
            return self.Weekday(self.recurrence_weekday).label
        except ValueError:  # pragma: no cover - defensive fallback
            return ""

    def get_recurrence_week_of_month_display(self) -> str:
        if self.recurrence_week_of_month is None:
            return ""
        try:
            return self.WeekOfMonth(self.recurrence_week_of_month).label
        except ValueError:  # pragma: no cover - defensive fallback
            return ""

    @property
    def recurrence_description(self) -> str:
        freq = self.recurrence_frequency
        if freq == self.RecurrenceFrequency.NONE:
            if self.has_manual_occurrences:
                return "Multiple dates"
            return "Does not repeat"
        weekday = self.get_recurrence_weekday_display()
        if freq == self.RecurrenceFrequency.WEEKLY:
            return f"Weekly on {weekday}" if weekday else "Weekly"
        if freq == self.RecurrenceFrequency.BIWEEKLY:
            return f"Every other week on {weekday}" if weekday else "Every other week"
        if freq == self.RecurrenceFrequency.MONTHLY_DATE:
            return (
                f"Monthly on day {self.recurrence_day_of_month}"
                if self.recurrence_day_of_month
                else "Monthly"
            )
        if freq == self.RecurrenceFrequency.MONTHLY_WEEKDAY:
            week_label = self.get_recurrence_week_of_month_display()
            if week_label and weekday:
                return f"Monthly on the {week_label.lower()} {weekday}"
            if week_label:
                return f"Monthly on the {week_label.lower()} week"
            if weekday:
                return f"Monthly on {weekday}"
            return "Monthly"
        return ""

    @property
    def doors_time(self) -> datetime | None:
        return self.doors_at or self.starts_at


class EventPerformer(models.Model):
    """Performer slot (imported from Band or ad-hoc)."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="performers")
    band = models.ForeignKey(
        "bands.Band",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="event_slots",
    )
    display_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Shown publicly; defaults to the linked band's name.",
    )
    performer_type = models.CharField(
        max_length=16,
        blank=True,
        help_text="Optional override (DJ set, acoustic, support, etc.).",
    )
    slot_starts_at = models.DateTimeField(blank=True, null=True)
    slot_ends_at = models.DateTimeField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["order", "slot_starts_at", "display_name"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.display_name} @ {self.event.title}"

    def save(self, *args, **kwargs):
        self.sync_display_name()
        super().save(*args, **kwargs)

    def sync_display_name(self):
        if self.band and not self.display_name:
            self.display_name = self.band.name


class EventRecurrenceException(models.Model):
    """Represents a single occurrence of a recurring event being skipped or overridden."""

    class ExceptionType(models.TextChoices):
        SKIP = "skip", "Skip occurrence"
        OVERRIDE = "override", "Override occurrence"
        HOLIDAY = "holiday", "Holiday blackout"

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="recurrence_exceptions",
    )
    occurrence_start = models.DateTimeField()
    exception_type = models.CharField(
        max_length=16,
        choices=ExceptionType.choices,
        default=ExceptionType.SKIP,
    )
    override_event = models.OneToOneField(
        Event,
        on_delete=models.CASCADE,
        related_name="recurrence_exception",
        blank=True,
        null=True,
    )
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-occurrence_start"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "occurrence_start"],
                name="unique_event_occurrence_exception",
            )
        ]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.event.title} @ {self.occurrence_start} ({self.get_exception_type_display()})"


class HolidayWindow(models.Model):
    """Date span where recurring events should automatically be skipped."""

    name = models.CharField(max_length=140)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    applies_to_internal = models.BooleanField(
        default=True,
        help_text="If unchecked, internal events will still be scheduled.",
    )
    applies_to_public = models.BooleanField(
        default=True,
        help_text="If unchecked, public events will still be scheduled.",
    )
    note = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="holiday_windows_created",
        blank=True,
        null=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="holiday_windows_updated",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-starts_at"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.name} ({self.starts_at:%Y-%m-%d} → {self.ends_at:%Y-%m-%d})"

    @classmethod
    def overlapping(cls, start: datetime | None, end: datetime | None):
        """Return active windows intersecting the provided timeframe."""

        tz = timezone.get_current_timezone()

        def _normalize(value: datetime | None) -> datetime | None:
            if not value:
                return None
            if timezone.is_naive(value):
                return timezone.make_aware(value, tz)
            return value

        start = _normalize(start)
        end = _normalize(end)

        qs = cls.objects.all()
        if start:
            qs = qs.filter(ends_at__gte=start)
        if end:
            qs = qs.filter(starts_at__lte=end)
        return qs
