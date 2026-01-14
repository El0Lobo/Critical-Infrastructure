"""Forms for event management."""

from __future__ import annotations

from datetime import datetime, timedelta

from django import forms
from django.db import models
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

from app.bands.models import Band
from app.core.date_utils import add_months
from app.events.models import Event, EventCategory, EventPerformer, HolidayWindow
from app.setup.models import SiteSettings
from app.shifts.models import ShiftTemplate


class EventForm(forms.ModelForm):
    """Main event form used for create/edit modals."""
    manual_occurrences_text = forms.CharField(
        required=False,
        label=_("Manual dates"),
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "2026-01-14 19:00\n2026-02-11 19:00",
            }
        ),
        help_text=_(
            "Optional list of dates for announcements without a recurring pattern. "
            "Enter one date per line using YYYY-MM-DD HH:MM."
        ),
    )

    class Meta:
        model = Event
        fields = [
            "title",
            "event_type",
            "slug",
            "status",
            "hero_image",
            "teaser",
            "description_public",
            "description_internal",
            "categories",
            "doors_at",
            "starts_at",
            "ends_at",
            "curfew_at",
            "recurrence_frequency",
            "recurrence_weekday",
            "recurrence_week_of_month",
            "recurrence_day_of_month",
            "recurrence_next_start_at",
            "ticket_url",
            "ticket_price_from",
            "ticket_price_to",
            "is_free",
            "requires_shifts",
            "standard_shifts",
            "venue_name",
            "venue_address",
            "venue_postal_code",
            "venue_city",
            "venue_country",
            "seo_title",
            "seo_description",
            "visibility_key",
            "featured",
        ]
        widgets = {
            "description_public": forms.Textarea(attrs={"rows": 6}),
            "description_internal": forms.Textarea(attrs={"rows": 4}),
            "doors_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "curfew_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "categories": forms.CheckboxSelectMultiple(),
            "recurrence_day_of_month": forms.NumberInput(attrs={"min": 1, "max": 31}),
            "recurrence_next_start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "standard_shifts": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        tz = timezone.get_current_timezone()

        self.is_occurrence_override = bool(
            getattr(self.instance, "recurrence_parent_id", None)
            or getattr(self.instance, "recurrence_parent", None)
        )

        for key in [
            "doors_at",
            "starts_at",
            "ends_at",
            "curfew_at",
            "recurrence_frequency",
            "recurrence_weekday",
            "recurrence_week_of_month",
            "recurrence_day_of_month",
            "recurrence_next_start_at",
        ]:
            if key in self.fields:
                self.fields[key].required = False

        def to_naive(value):
            if not value:
                return value
            if timezone.is_naive(value):
                return value.replace(second=0, microsecond=0)
            return timezone.localtime(value).replace(second=0, microsecond=0, tzinfo=None)

        if self.is_occurrence_override:
            for field_name in [
                "recurrence_frequency",
                "recurrence_weekday",
                "recurrence_week_of_month",
                "recurrence_day_of_month",
                "recurrence_next_start_at",
                "manual_occurrences_text",
            ]:
                if field_name in self.fields:
                    self.fields[field_name].disabled = True
            self.fields[field_name].help_text = _("Managed by the recurring series.")
            if "recurrence_frequency" in self.fields:
                self.initial.setdefault("recurrence_frequency", Event.RecurrenceFrequency.NONE)

        if "standard_shifts" in self.fields:
            queryset = ShiftTemplate.objects.order_by("order", "name")
            self.fields["standard_shifts"].queryset = queryset
        else:
            queryset = ShiftTemplate.objects.none()
        # Provide friendly defaults the first time an event is created.
        if not self.instance.pk:
            now = timezone.localtime()

            try:
                cfg = SiteSettings.get_solo()
            except Exception:  # pragma: no cover - in migrations / early boot
                cfg = None

            default_starts = now.replace(minute=0, second=0, microsecond=0) + timedelta(days=7)
            default_doors = default_starts - timedelta(hours=1)
            default_ends = default_starts + timedelta(hours=3)
            default_curfew = default_ends

            if cfg:
                self.initial.setdefault("venue_name", cfg.org_name)
                address_parts = [cfg.address_street, cfg.address_number]
                address_joined = " ".join(part for part in address_parts if part)
                self.initial.setdefault("venue_address", address_joined.strip())
                self.initial.setdefault("venue_postal_code", cfg.address_postal_code)
                self.initial.setdefault("venue_city", cfg.address_city)
                self.initial.setdefault("venue_country", cfg.address_country or "")

                openings = cfg.hours.filter(
                    closed=False, open_time__isnull=False, close_time__isnull=False
                ).order_by("weekday")
                if openings:

                    def order_key(hour):
                        return ((hour.weekday - now.weekday()) % 7, hour.open_time)

                    first_slot = sorted(openings, key=order_key)[0]
                    days_until = (first_slot.weekday - now.weekday()) % 7
                    target_date = now.date() + timedelta(days=days_until)
                    doors_dt = timezone.make_aware(
                        datetime.combine(target_date, first_slot.open_time), tz
                    )
                    close_dt = timezone.make_aware(
                        datetime.combine(target_date, first_slot.close_time), tz
                    )
                    start_dt = doors_dt + timedelta(minutes=60)
                    if start_dt > close_dt:
                        start_dt = doors_dt

                    default_doors = doors_dt
                    default_starts = start_dt
                    default_ends = close_dt
                    default_curfew = close_dt

            self.initial.setdefault("doors_at", to_naive(default_doors))
            self.initial.setdefault("starts_at", to_naive(default_starts))
            self.initial.setdefault("ends_at", to_naive(default_ends))
            self.initial.setdefault("curfew_at", to_naive(default_curfew))

        # Provide nicer help-text for empty slug
        self.fields["slug"].help_text = _("Leave blank to auto-generate from the title.")
        if "categories" in self.fields:
            self.fields["categories"].queryset = EventCategory.objects.order_by("name")
            self.fields["categories"].widget.attrs.update({"data-allow-search": "true"})
        if "standard_shifts" in self.fields:
            widget = self.fields["standard_shifts"].widget or forms.CheckboxSelectMultiple()
            if not isinstance(widget, forms.CheckboxSelectMultiple):
                widget = forms.CheckboxSelectMultiple()
            widget.choices = self.fields["standard_shifts"].choices
            self.fields["standard_shifts"].widget = widget
            self.fields["standard_shifts"].required = False
            if not self.instance.pk:
                selected_ids = []
                last_event = None
                if user:
                    last_event = (
                        Event.objects.filter(created_by=user).order_by("-created_at").first()
                    )
                if not last_event:
                    last_event = Event.objects.order_by("-created_at").first()
                if last_event:
                    selected_ids = list(last_event.standard_shifts.values_list("id", flat=True))
                    if selected_ids:
                        self.initial.setdefault("standard_shifts", selected_ids)
                        if last_event.requires_shifts:
                            self.initial.setdefault("requires_shifts", True)
                            self.fields["requires_shifts"].initial = True

        for key in ["doors_at", "starts_at", "ends_at", "curfew_at", "recurrence_next_start_at"]:
            value = self.initial.get(key)
            if hasattr(value, "tzinfo") and value is not None:
                self.initial[key] = value.replace(tzinfo=None)

        if "manual_occurrences_text" in self.fields:
            manual_entries = []
            if self.instance.pk and self.instance.manual_occurrences:
                for dt in self.instance.manual_occurrence_datetimes():
                    manual_entries.append(timezone.localtime(dt, tz).strftime("%Y-%m-%d %H:%M"))
            self.initial.setdefault("manual_occurrences_text", "\n".join(manual_entries))

        self.fieldsets = [
            (
                "Basics",
                [
                    "title",
                    "status",
                    "event_type",
                    "slug",
                    "categories",
                    "featured",
                    "hero_image",
                    "teaser",
                ],
                {"open": True},
            ),
            (
                "Schedule",
                ["doors_at", "starts_at", "ends_at", "curfew_at"],
                {"open": True},
            ),
            (
                "Recurrence",
                [
                    "recurrence_frequency",
                    "recurrence_weekday",
                    "recurrence_week_of_month",
                    "recurrence_day_of_month",
                    "recurrence_next_start_at",
                    "manual_occurrences_text",
                ],
                {},
            ),
            (
                "Location",
                [
                    "venue_name",
                    "venue_address",
                    "venue_postal_code",
                    "venue_city",
                    "venue_country",
                ],
                {},
            ),
            (
                "Ticketing",
                [
                    "is_free",
                    "ticket_price_from",
                    "ticket_price_to",
                    "ticket_url",
                ],
                {},
            ),
            (
                "Content",
                [
                    "description_public",
                    "description_internal",
                    "seo_title",
                    "seo_description",
                ],
                {},
            ),
            (
                "Visibility",
                ["visibility_key"],
                {},
            ),
            (
                "Shifts",
                ["requires_shifts", "standard_shifts"],
                {},
            ),
        ]

        self.render_fieldsets = []
        for title, field_names, opts in self.fieldsets:
            bound_fields = [self[field] for field in field_names]
            self.render_fieldsets.append((title, bound_fields, opts))

        if "standard_shifts" in self.fields:
            self.standard_shift_count = self.fields["standard_shifts"].queryset.count()
        else:
            self.standard_shift_count = 0

    def clean_slug(self):
        slug = self.cleaned_data.get("slug")
        if slug:
            qs = Event.objects.exclude(pk=self.instance.pk)
            if qs.filter(slug=slug).exists():
                raise forms.ValidationError("Slug already in use.")
        return slug

    def _validate_recurrence_fields(
        self,
        cleaned,
        is_override,
        freq,
        weekday,
        week_of_month,
        day_of_month,
        starts_at,
        next_start,
    ):
        """Validate recurrence pattern fields based on frequency."""
        if is_override:
            cleaned["recurrence_weekday"] = None
            cleaned["recurrence_week_of_month"] = None
            cleaned["recurrence_day_of_month"] = None
            return

        if day_of_month is not None and not 1 <= day_of_month <= 31:
            self.add_error("recurrence_day_of_month", "Choose a day between 1 and 31.")

        # Validate weekday for patterns that require it
        if freq in {
            Event.RecurrenceFrequency.WEEKLY,
            Event.RecurrenceFrequency.BIWEEKLY,
            Event.RecurrenceFrequency.MONTHLY_WEEKDAY,
        }:
            if weekday is None:
                self.add_error(
                    "recurrence_weekday", "Select a weekday for this recurrence pattern."
                )
        else:
            cleaned["recurrence_weekday"] = None

        # Validate day of month for monthly date pattern
        if freq == Event.RecurrenceFrequency.MONTHLY_DATE:
            if day_of_month is None:
                self.add_error(
                    "recurrence_day_of_month", "Select the day of the month for this recurrence."
                )
        else:
            cleaned["recurrence_day_of_month"] = (
                day_of_month if freq == Event.RecurrenceFrequency.MONTHLY_DATE else None
            )

        # Validate week of month for monthly weekday pattern
        if freq == Event.RecurrenceFrequency.MONTHLY_WEEKDAY:
            if week_of_month is None:
                self.add_error(
                    "recurrence_week_of_month", "Select which week of the month applies."
                )
        else:
            cleaned["recurrence_week_of_month"] = None

        # Validate start time for recurring events
        if freq != Event.RecurrenceFrequency.NONE and not (starts_at or next_start):
            self.add_error(
                "recurrence_next_start_at",
                "Provide either a start date/time or the next scheduled start for recurring events.",
            )

        # Clear recurrence fields for non-recurring events
        if freq == Event.RecurrenceFrequency.NONE:
            cleaned["recurrence_weekday"] = None
            cleaned["recurrence_week_of_month"] = None
            cleaned["recurrence_day_of_month"] = None
            cleaned["recurrence_next_start_at"] = next_start

    def _align_weekly_biweekly_start(self, cleaned, weekday, tz, now_local):
        """Align start time to selected weekday for weekly/biweekly recurrences."""
        start_val = cleaned.get("starts_at")
        if not start_val or weekday is None:
            return

        start_aware = start_val
        if timezone.is_naive(start_aware):
            start_aware = timezone.make_aware(start_aware, tz)
        else:
            start_aware = timezone.localtime(start_aware, tz)

        # Only adjust when the chosen weekday does not match or is in the past
        if start_aware.weekday() != weekday or start_aware <= now_local:
            time_part = start_aware.time()
            candidate = timezone.make_aware(datetime.combine(now_local.date(), time_part), tz)

            # Advance to the requested weekday, ensuring it's not in the past
            while candidate.weekday() != weekday or candidate <= now_local:
                candidate += timedelta(days=1)

            cleaned["starts_at"] = candidate.astimezone(tz).replace(tzinfo=None)
            cleaned["recurrence_next_start_at"] = cleaned["starts_at"]

        # Snap schedule to site opening hours if available
        self._apply_site_hours_to_schedule(cleaned, weekday, tz, now_local)

    def _apply_site_hours_to_schedule(self, cleaned, weekday, tz, now_local):
        """Apply site opening hours constraints to event schedule."""
        try:
            cfg = SiteSettings.get_solo()
            slot = cfg.hours.filter(
                weekday=weekday, closed=False, open_time__isnull=False, close_time__isnull=False
            ).first()
        except Exception:
            slot = None

        if slot:
            self._snap_to_site_hours(cleaned, weekday, tz, now_local, slot)
        else:
            self._normalize_event_times(cleaned, tz)

    def _snap_to_site_hours(self, cleaned, weekday, tz, now_local, slot):
        """Snap event times to site opening hours."""

        def _aware(value):
            if not value:
                return None
            if timezone.is_naive(value):
                return timezone.make_aware(value, tz)
            return timezone.localtime(value, tz)

        def _delta(a, b, default):
            if a and b:
                aware_a, aware_b = _aware(a), _aware(b)
                if aware_a and aware_b:
                    diff = aware_a - aware_b
                    if diff.total_seconds() >= 0:
                        return diff
            return default

        # Calculate existing time deltas
        start_delta = _delta(cleaned.get("starts_at"), cleaned.get("doors_at"), timedelta(hours=1))
        end_delta = _delta(cleaned.get("ends_at"), cleaned.get("starts_at"), timedelta(hours=3))
        curfew_delta = _delta(cleaned.get("curfew_at"), cleaned.get("ends_at"), timedelta(0))

        def _next_occurrence(time_value):
            base_time = datetime.combine(now_local.date(), time_value)
            candidate = timezone.make_aware(base_time, tz)
            while candidate.weekday() != weekday or candidate <= now_local:
                candidate += timedelta(days=1)
            return candidate

        doors_local = _next_occurrence(slot.open_time)
        close_local = _next_occurrence(slot.close_time)
        if slot.close_time <= slot.open_time:
            close_local += timedelta(days=1)

        starts_local = min(doors_local + start_delta, doors_local)
        ends_local = min(starts_local + end_delta, close_local)
        curfew_local = max(ends_local + curfew_delta, ends_local)

        cleaned["doors_at"] = doors_local.replace(tzinfo=None)
        cleaned["starts_at"] = starts_local.replace(tzinfo=None)
        cleaned["ends_at"] = ends_local.replace(tzinfo=None)
        cleaned["curfew_at"] = curfew_local.replace(tzinfo=None)
        cleaned["recurrence_next_start_at"] = starts_local.replace(tzinfo=None)

    def _normalize_event_times(self, cleaned, tz):
        """Normalize event times when no site hours are available."""

        def _naive(value):
            if not value:
                return None
            if timezone.is_naive(value):
                return value
            return timezone.localtime(value, tz).replace(tzinfo=None)

        normalized_start = _naive(cleaned.get("starts_at"))
        normalized_doors = _naive(cleaned.get("doors_at"))
        normalized_end = _naive(cleaned.get("ends_at"))
        normalized_curfew = _naive(cleaned.get("curfew_at"))

        if normalized_doors and normalized_start and normalized_doors > normalized_start:
            normalized_doors = normalized_start

        cleaned["starts_at"] = normalized_start
        cleaned["doors_at"] = normalized_doors
        cleaned["ends_at"] = normalized_end
        cleaned["curfew_at"] = normalized_curfew
        cleaned["recurrence_next_start_at"] = normalized_start

    def _calculate_monthly_date_start(self, cleaned, aware_start, day_of_month, tz, now_local):
        """Calculate start time for monthly date recurrence pattern."""
        import calendar

        try:
            candidate = timezone.make_aware(
                datetime(
                    year=now_local.year,
                    month=now_local.month,
                    day=day_of_month,
                    hour=aware_start.hour,
                    minute=aware_start.minute,
                    second=aware_start.second,
                ),
                tz,
            )
        except ValueError:
            # Day doesn't exist in this month (e.g., Feb 30), use last day
            last_day = calendar.monthrange(now_local.year, now_local.month)[1]
            candidate = timezone.make_aware(
                datetime(
                    year=now_local.year,
                    month=now_local.month,
                    day=last_day,
                    hour=aware_start.hour,
                    minute=aware_start.minute,
                    second=aware_start.second,
                ),
                tz,
            )

        if candidate <= now_local:
            candidate = add_months(candidate, 1)

        cleaned["starts_at"] = candidate.replace(tzinfo=None)
        cleaned["recurrence_next_start_at"] = cleaned["starts_at"]

    def _calculate_monthly_weekday_start(
        self, cleaned, aware_start, weekday, week_of_month, tz, now_local
    ):
        """Calculate start time for monthly weekday recurrence pattern."""
        first_of_month = now_local.replace(
            day=1,
            hour=aware_start.hour,
            minute=aware_start.minute,
            second=aware_start.second,
        )

        candidate = first_of_month
        while candidate.weekday() != weekday:
            candidate += timedelta(days=1)
        candidate += timedelta(weeks=week_of_month - 1)

        if candidate <= now_local:
            next_month = add_months(candidate, 1).replace(day=1)
            candidate = next_month
            while candidate.weekday() != weekday:
                candidate += timedelta(days=1)
            candidate += timedelta(weeks=week_of_month - 1)

        cleaned["starts_at"] = candidate.replace(tzinfo=None)
        cleaned["recurrence_next_start_at"] = cleaned["starts_at"]

    def _parse_manual_occurrences(self, raw_value, tz):
        if not raw_value:
            return []
        entries = []
        chunks = []
        if isinstance(raw_value, str):
            for chunk in raw_value.replace(",", "\n").splitlines():
                chunk = chunk.strip()
                if chunk:
                    chunks.append(chunk)
        elif isinstance(raw_value, list):
            chunks = [str(item).strip() for item in raw_value if str(item).strip()]
        else:
            chunks = [str(raw_value).strip()] if str(raw_value).strip() else []

        for chunk in chunks:
            normalized = chunk.replace(" ", "T")
            try:
                parsed = datetime.fromisoformat(normalized)
            except ValueError:
                self.add_error(
                    "manual_occurrences_text",
                    _("Use YYYY-MM-DD HH:MM format, one per line."),
                )
                continue
            if timezone.is_naive(parsed):
                parsed = timezone.make_aware(parsed, tz)
            else:
                parsed = timezone.localtime(parsed, tz)
            entries.append(parsed)
        entries = sorted(entries)
        return [dt.replace(tzinfo=None).isoformat(timespec="minutes") for dt in entries]

    def clean(self):
        """Validate and normalize event form data."""
        cleaned = super().clean()

        # Extract all form values
        is_override = getattr(self, "is_occurrence_override", False)
        event_type = cleaned.get("event_type") or Event.EventType.PUBLIC
        starts_at = cleaned.get("starts_at")
        freq = cleaned.get("recurrence_frequency") or Event.RecurrenceFrequency.NONE
        weekday = cleaned.get("recurrence_weekday")
        week_of_month = cleaned.get("recurrence_week_of_month")
        day_of_month = cleaned.get("recurrence_day_of_month")
        next_start = cleaned.get("recurrence_next_start_at")
        manual_raw = cleaned.get("manual_occurrences_text")

        # Handle override mode
        if is_override:
            freq = Event.RecurrenceFrequency.NONE
            cleaned["recurrence_frequency"] = freq
            next_start = starts_at or next_start
            cleaned["recurrence_next_start_at"] = next_start

        # Setup timezone and aware datetime
        tz = timezone.get_current_timezone()
        reference_start = starts_at or next_start
        aware_start = None
        if reference_start:
            if timezone.is_naive(reference_start):
                aware_start = timezone.make_aware(reference_start, tz)
            else:
                aware_start = timezone.localtime(reference_start, tz)
        now_local = timezone.now().astimezone(tz)

        manual_occurrences = self._parse_manual_occurrences(manual_raw, tz)
        cleaned["manual_occurrences"] = manual_occurrences

        if manual_occurrences and freq != Event.RecurrenceFrequency.NONE:
            self.add_error(
                "manual_occurrences_text",
                _("Manual dates can only be used when recurrence is set to does not repeat."),
            )

        # Validate start time requirement
        if event_type != Event.EventType.INTERNAL and not starts_at and not manual_occurrences:
            self.add_error("starts_at", "Start date/time is required for non-internal events.")

        # Validate recurrence fields
        self._validate_recurrence_fields(
            cleaned, is_override, freq, weekday, week_of_month, day_of_month, starts_at, next_start
        )

        if manual_occurrences:
            cleaned["recurrence_frequency"] = Event.RecurrenceFrequency.NONE
            cleaned["recurrence_weekday"] = None
            cleaned["recurrence_week_of_month"] = None
            cleaned["recurrence_day_of_month"] = None
            next_manual = None
            for raw in manual_occurrences:
                parsed = datetime.fromisoformat(raw)
                if timezone.is_naive(parsed):
                    parsed = timezone.make_aware(parsed, tz)
                else:
                    parsed = timezone.localtime(parsed, tz)
                if parsed >= now_local:
                    next_manual = parsed
                    break
            if next_manual:
                cleaned["recurrence_next_start_at"] = next_manual.replace(tzinfo=None)
            if not starts_at and manual_occurrences:
                first_manual = datetime.fromisoformat(manual_occurrences[0])
                cleaned["starts_at"] = first_manual

        # Apply recurrence-specific logic
        if freq in {Event.RecurrenceFrequency.WEEKLY, Event.RecurrenceFrequency.BIWEEKLY}:
            self._align_weekly_biweekly_start(cleaned, weekday, tz, now_local)

        if (
            aware_start
            and freq == Event.RecurrenceFrequency.MONTHLY_DATE
            and day_of_month is not None
        ):
            self._calculate_monthly_date_start(cleaned, aware_start, day_of_month, tz, now_local)

        if (
            aware_start
            and freq == Event.RecurrenceFrequency.MONTHLY_WEEKDAY
            and week_of_month is not None
            and weekday is not None
        ):
            self._calculate_monthly_weekday_start(
                cleaned, aware_start, weekday, week_of_month, tz, now_local
            )

        # Normalize all datetime fields to naive values
        for field_name in [
            "doors_at",
            "starts_at",
            "ends_at",
            "curfew_at",
            "recurrence_next_start_at",
        ]:
            value = cleaned.get(field_name)
            if value and not timezone.is_naive(value):
                cleaned[field_name] = timezone.localtime(
                    value, timezone.get_current_timezone()
                ).replace(tzinfo=None)

        return cleaned

    def save(self, commit: bool = True):
        inst = super().save(commit=False)
        if "manual_occurrences" in self.cleaned_data:
            inst.manual_occurrences = self.cleaned_data.get("manual_occurrences") or []
        if self.user and not inst.pk:
            inst.created_by = self.user
        if self.user:
            inst.updated_by = self.user
        if commit:
            inst.save()
            self.save_m2m()
        else:
            # ensure categories saved when commit=False and saved later
            self._pending_m2m = self.cleaned_data.get("categories")
        return inst


class EventPerformerForm(forms.ModelForm):
    """Handles both linking an existing band and quick-adding one."""

    new_band_name = forms.CharField(
        required=False,
        label="Quick add band",
        help_text="Fill to create a new band on the fly if it does not exist.",
    )
    performer_type_override = forms.ChoiceField(
        required=False,
        choices=[("", "—")] + list(Band.PerformerType.choices),
        label="Performer type",
        help_text="Optional override if different from the band profile.",
    )

    class Meta:
        model = EventPerformer
        fields = [
            "band",
            "new_band_name",
            "display_name",
            "performer_type_override",
            "slot_starts_at",
            "slot_ends_at",
            "order",
            "notes",
        ]
        widgets = {
            "slot_starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "slot_ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def clean(self):
        cleaned = super().clean()
        band = cleaned.get("band")
        quick_name = cleaned.get("new_band_name", "").strip()
        if self.cleaned_data.get("DELETE"):
            return cleaned
        if self.empty_permitted and not (band or quick_name or cleaned.get("display_name")):
            return cleaned
        if not band and not quick_name:
            raise forms.ValidationError("Select a band or quick-add one.")
        return cleaned

    def save(self, commit: bool = True):
        band = self.cleaned_data.get("band")
        quick_name = (self.cleaned_data.get("new_band_name") or "").strip()
        performer_type = self.cleaned_data.get("performer_type_override") or ""

        if not band and quick_name:
            defaults = {
                "slug": slugify(quick_name)[:220],
                "performer_type": performer_type or Band.PerformerType.BAND,
            }
            band, _ = Band.objects.get_or_create(name=quick_name, defaults=defaults)
        instance: EventPerformer = super().save(commit=False)
        instance.band = band
        if performer_type:
            instance.performer_type = performer_type
        elif band and not instance.performer_type:
            instance.performer_type = band.performer_type
        if not instance.display_name and band:
            instance.display_name = band.name
        if commit:
            instance.save()
        return instance


class BasePerformerFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        totals = 0
        for form in self.forms:
            if not getattr(form, "cleaned_data", None) or form.cleaned_data.get("DELETE"):
                continue
            data = form.cleaned_data
            has_content = data.get("band") or data.get("new_band_name") or data.get("display_name")
            if has_content:
                totals += 1
        if totals == 0:
            status = getattr(self.instance, "status", Event.Status.DRAFT)
            if status == Event.Status.PUBLISHED:
                raise forms.ValidationError("Published events must list at least one performer.")


EventPerformerFormSet = inlineformset_factory(
    Event,
    EventPerformer,
    form=EventPerformerForm,
    formset=BasePerformerFormSet,
    extra=1,
    can_delete=True,
)


class EventCategoryForm(forms.ModelForm):
    class Meta:
        model = EventCategory
        fields = ["name", "slug", "description", "color", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "color": forms.TextInput(attrs={"type": "color"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self.fields["slug"].help_text = "Leave blank to auto-generate from the name."

    def save(self, commit: bool = True):
        inst = super().save(commit=False)
        if not inst.slug:
            inst.slug = slugify(inst.name)[:140]
        if commit:
            inst.save()
        return inst


class HolidayWindowForm(forms.ModelForm):
    """Simple form to manage blackout windows for recurring events."""

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        for key in ["starts_at", "ends_at"]:
            if key in self.fields:
                self.fields[key].widget = forms.DateTimeInput(attrs={"type": "datetime-local"})

    class Meta:
        model = HolidayWindow
        fields = [
            "name",
            "starts_at",
            "ends_at",
            "applies_to_public",
            "applies_to_internal",
            "note",
        ]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 2}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("starts_at")
        end = cleaned.get("ends_at")
        if start and end and end <= start:
            self.add_error("ends_at", _("End must be after the start."))
        return cleaned

    def save(self, commit: bool = True):
        instance = super().save(commit=False)
        if self.user:
            if not instance.pk:
                instance.created_by = self.user
            instance.updated_by = self.user
        if commit:
            instance.save()
        return instance


class EventFilterForm(forms.Form):
    class Timeframe(models.TextChoices):
        WEEK = "week", _("This week")
        MONTH = "month", _("This month")
        YEAR = "year", _("This year")
        ALL = "all", _("All")

    q = forms.CharField(required=False, label=_("Search title"))
    timeframe = forms.ChoiceField(choices=Timeframe.choices, initial=Timeframe.MONTH)
    include_past = forms.BooleanField(required=False, initial=False, label=_("Include past events"))
    period_offset = forms.IntegerField(required=False, widget=forms.HiddenInput(), initial=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "q" in self.fields:
            self.fields["q"].widget.attrs.setdefault("placeholder", _("Search title..."))
            self.fields["q"].widget.attrs.setdefault("type", "search")
