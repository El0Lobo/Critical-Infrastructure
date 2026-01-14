"""Shift planning domain models."""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class ShiftTemplate(models.Model):
    """Reusable standalone shift definition (e.g. Door, Bar Shift 2)."""

    class Reference(models.TextChoices):
        EVENT_START = "event_start", "Event start"
        DOORS_OPEN = "doors", "Doors open"

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    start_reference = models.CharField(
        max_length=20,
        choices=Reference.choices,
        default=Reference.DOORS_OPEN,
        help_text="Base time used to calculate the shift start.",
    )
    start_offset_minutes = models.IntegerField(
        default=0,
        help_text="Minutes relative to the chosen reference (negative = before).",
    )
    end_offset_minutes = models.IntegerField(
        default=0,
        help_text="Minutes to subtract from the closing time (positive = earlier).",
    )
    duration_minutes = models.PositiveIntegerField(
        default=0,
        help_text="Optional fixed duration per segment (0 = auto evenly split).",
    )
    segment_count = models.PositiveIntegerField(
        default=1,
        help_text="How many sequential segments to split the coverage into.",
    )
    capacity = models.PositiveIntegerField(
        default=1,
        verbose_name="People per segment",
        help_text="Number of people required in each segment.",
    )
    allow_signup = models.BooleanField(default=True)
    visibility_key = models.CharField(max_length=120, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify

            self.slug = slugify(self.name)[:140]
        super().save(*args, **kwargs)

    def segment_schedule(self, event):
        closing = event.curfew_at or event.ends_at

        # For auto-duration templates, always anchor to doors (or start) so coverage spans door open to curfew.
        if self.duration_minutes == 0:
            base = event.doors_at or event.starts_at
        else:
            base = event.starts_at
            if self.start_reference == self.Reference.DOORS_OPEN and event.doors_at:
                base = event.doors_at

        if base is None:
            base = event.starts_at or event.doors_at or timezone.now()

        start = base + timedelta(minutes=self.start_offset_minutes)

        # Determine coverage end
        coverage_end = closing or None
        if coverage_end:
            comparison_base = base
            while coverage_end <= comparison_base:
                coverage_end += timedelta(days=1)
            coverage_end = coverage_end - timedelta(minutes=self.end_offset_minutes)
        if not coverage_end or coverage_end <= start:
            total_minutes = self.duration_minutes * max(self.segment_count, 1) or 180 * max(
                self.segment_count, 1
            )
            coverage_end = start + timedelta(minutes=total_minutes)

        span = coverage_end - start
        segments = []
        count = max(self.segment_count, 1)

        if self.duration_minutes:
            seg_duration = timedelta(minutes=self.duration_minutes)
        else:
            seg_duration = span / count if count else timedelta(minutes=0)
        if seg_duration <= timedelta(0):
            seg_duration = timedelta(minutes=30)

        current_start = start
        for idx in range(1, count + 1):
            seg_end = coverage_end if idx == count else current_start + seg_duration
            if seg_end > coverage_end:
                seg_end = coverage_end
            segments.append(
                {
                    "index": idx,
                    "title": f"{self.name} {idx}" if count > 1 else self.name,
                    "start": current_start,
                    "end": seg_end,
                }
            )
            current_start = seg_end

        return segments

    def instantiate_shift(self, event, *, user=None):
        """Create one or more Shift instances for the given event."""

        created = []
        for segment in self.segment_schedule(event):
            for staff_index in range(1, max(self.capacity, 1) + 1):
                title = segment["title"]
                if self.capacity > 1:
                    title = f"{segment['title']} · Slot {staff_index}"
                created.append(
                    Shift.objects.create(
                        event=event,
                        template=self,
                        template_segment=segment["index"],
                        template_staff_position=staff_index,
                        title=title,
                        description=self.description,
                        start_at=segment["start"],
                        end_at=segment["end"],
                        capacity=1,
                        allow_signup=self.allow_signup,
                        visibility_key=self.visibility_key,
                        created_by=user,
                        updated_by=user,
                    )
                )
        return created


class ShiftPreset(models.Model):
    """Reusable template that expands into a set of shifts for an event."""

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(
        default=False,
        help_text="If flagged, suggest this preset during event creation.",
    )
    visibility_key = models.CharField(
        max_length=120,
        blank=True,
        help_text="Visibility rule key controlling who can use this preset.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.name

    def apply_to_event(self, event, *, user=None):
        """Instantiate this preset's slots as shifts for the provided event."""

        from app.shifts.models import Shift  # local import to avoid circular

        created = []
        base = event.starts_at
        for slot in self.slots.all().order_by("order", "id"):
            start = base + timedelta(minutes=slot.start_offset_minutes)
            end = start + timedelta(minutes=slot.duration_minutes)
            shift = Shift.objects.create(
                event=event,
                preset_slot=slot,
                title=slot.title,
                start_at=start,
                end_at=end,
                capacity=slot.capacity,
                allow_signup=slot.allow_signup,
                description=slot.notes,
                created_by=user,
                updated_by=user,
            )
            created.append(shift)
        return created


class ShiftPresetSlot(models.Model):
    """Single shift definition belonging to a preset."""

    preset = models.ForeignKey(ShiftPreset, on_delete=models.CASCADE, related_name="slots")
    title = models.CharField(max_length=120)
    order = models.PositiveIntegerField(default=0)
    start_offset_minutes = models.IntegerField(
        default=0,
        help_text="Minutes relative to event start (negative = before).",
    )
    duration_minutes = models.PositiveIntegerField(default=120, help_text="Length in minutes.")
    capacity = models.PositiveIntegerField(default=1)
    allow_signup = models.BooleanField(
        default=True,
        help_text="If false, shift can only be assigned manually.",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.title} ({self.duration_minutes} min)"


class Shift(models.Model):
    """Event-specific shift instance."""

    STATUS_CHOICES = [
        ("open", "Open"),
        ("closed", "Closed"),
        ("archived", "Archived"),
    ]

    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="shifts",
    )
    preset_slot = models.ForeignKey(
        ShiftPresetSlot,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="generated_shifts",
    )
    template = models.ForeignKey(
        ShiftTemplate,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="generated_shifts",
    )
    template_segment = models.PositiveSmallIntegerField(default=1)
    template_staff_position = models.PositiveSmallIntegerField(default=1)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=1)
    allow_signup = models.BooleanField(default=True)
    visibility_key = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="open")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="shifts_created",
        blank=True,
        null=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="shifts_updated",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_at", "title"]
        unique_together = (
            ("event", "template", "template_segment", "template_staff_position", "start_at"),
        )

    def __str__(self) -> str:  # pragma: no cover - trivial
        if self.start_at:
            return f"{self.title} ({self.start_at:%Y-%m-%d %H:%M})"
        return self.title

    @property
    def slots_taken(self) -> int:
        return self.assignments.filter(
            status__in=[ShiftAssignment.Status.ASSIGNED, ShiftAssignment.Status.COMPLETED]
        ).count()

    @property
    def is_full(self) -> bool:
        return self.slots_taken >= self.capacity

    def is_taken_by(self, user) -> bool:
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return self.assignments.filter(
            user=user,
            status__in=[ShiftAssignment.Status.ASSIGNED, ShiftAssignment.Status.COMPLETED],
        ).exists()


class ShiftAssignment(models.Model):
    """Assignment or signup of a user to a shift."""

    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        ASSIGNED = "assigned", "Assigned"
        COMPLETED = "completed", "Completed"
        DROPPED = "dropped", "Released"

    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name="assignments")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shift_assignments",
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.REQUESTED)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="shift_assignments_made",
        blank=True,
        null=True,
    )
    assigned_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("shift", "user")
        ordering = ["-assigned_at"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.user} → {self.shift} ({self.status})"

    @property
    def display_name(self) -> str:
        profile = getattr(self.user, "profile", None)
        if profile:
            chosen = (getattr(profile, "chosen_name", "") or "").strip()
            if chosen:
                return chosen
            legal = (getattr(profile, "legal_name", "") or "").strip()
            if legal:
                return legal
        full_name = (getattr(self.user, "get_full_name", lambda: "")() or "").strip()
        if full_name:
            return full_name
        username = getattr(self.user, "get_username", lambda: str(self.user_id))()
        return username or str(self.user_id)
