"""Forms for shift presets, event-specific shifts, and assignments."""

from __future__ import annotations

from datetime import timedelta

from django import forms
from django.db import models
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.utils import timezone

from app.events.models import Event
from app.shifts.models import (
    Shift,
    ShiftAssignment,
    ShiftPreset,
    ShiftPresetSlot,
    ShiftTemplate,
)


class ShiftPresetForm(forms.ModelForm):
    class Meta:
        model = ShiftPreset
        fields = ["name", "slug", "description", "is_default", "visibility_key"]

    def clean_slug(self):
        slug = self.cleaned_data.get("slug")
        if slug:
            qs = ShiftPreset.objects.exclude(pk=self.instance.pk)
            if qs.filter(slug=slug).exists():
                raise forms.ValidationError("Slug already in use.")
        return slug


class ShiftPresetSlotForm(forms.ModelForm):
    class Meta:
        model = ShiftPresetSlot
        fields = [
            "title",
            "order",
            "start_offset_minutes",
            "duration_minutes",
            "capacity",
            "allow_signup",
            "notes",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2})}


ShiftPresetSlotFormSet = inlineformset_factory(
    ShiftPreset,
    ShiftPresetSlot,
    form=ShiftPresetSlotForm,
    extra=1,
    can_delete=True,
)


class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = [
            "title",
            "description",
            "start_at",
            "end_at",
            "capacity",
            "allow_signup",
            "template",
            "visibility_key",
            "status",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_at")
        end = cleaned.get("end_at")
        if start and end and end <= start:
            raise forms.ValidationError("Shift end must be after the start time.")
        return cleaned


class BaseShiftInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        errors = []
        for form in self.forms:
            if not getattr(form, "cleaned_data", None) or form.cleaned_data.get("DELETE"):
                continue
            start = form.cleaned_data.get("start_at")
            end = form.cleaned_data.get("end_at")
            if start and end and end <= start:
                errors.append(
                    forms.ValidationError(
                        f"Shift '{form.cleaned_data.get('title') or 'unnamed'}' ends before it starts."
                    )
                )
        if errors:
            raise forms.ValidationError(errors)


EventShiftFormSet = inlineformset_factory(
    Event,
    Shift,
    form=ShiftForm,
    formset=BaseShiftInlineFormSet,
    extra=1,
    can_delete=True,
)


class ShiftAssignmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user_field = self.fields["user"]
        user_field.queryset = user_field.queryset.order_by("first_name", "last_name")
        user_field.required = False
        user_field.empty_label = "-- Unassigned --"
        self.fields["notes"].required = False

    class Meta:
        model = ShiftAssignment
        fields = ["user", "notes"]


class ShiftStatsFilterForm(forms.Form):
    PERIOD_CHOICES = [
        ("30", "Past month"),
        ("90", "Past 3 months"),
        ("180", "Past 6 months"),
        ("0", "All time"),
    ]

    period = forms.ChoiceField(choices=PERIOD_CHOICES, initial="90")

    def get_bounds(self):
        cleaned = getattr(self, "cleaned_data", {})
        period = cleaned.get("period") or self.data.get("period") or "0"
        days = int(period)
        if days <= 0:
            return None
        return timezone.now() - timedelta(days=days)


class ShiftFilterForm(forms.Form):
    class Timeframe(models.TextChoices):
        WEEK = "week", "Week"
        MONTH = "month", "Month"
        YEAR = "year", "Year"
        ALL = "all", "All"

    timeframe = forms.ChoiceField(choices=Timeframe.choices, initial=Timeframe.WEEK)
    include_past = forms.BooleanField(required=False, initial=False, label="Include past shifts")
    period_offset = forms.IntegerField(required=False, widget=forms.HiddenInput(), initial=0)


class ShiftTemplateForm(forms.ModelForm):
    class Meta:
        model = ShiftTemplate
        fields = [
            "name",
            "slug",
            "description",
            "order",
            "start_reference",
            "start_offset_minutes",
            "end_offset_minutes",
            "duration_minutes",
            "segment_count",
            "capacity",
            "allow_signup",
            "visibility_key",
        ]

    def clean_slug(self):
        slug = self.cleaned_data.get("slug")
        if slug:
            qs = ShiftTemplate.objects.exclude(pk=self.instance.pk)
            if qs.filter(slug=slug).exists():
                raise forms.ValidationError("Slug already in use.")
        return slug

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self.fields["slug"].help_text = "Leave blank to auto-generate."
        if "segment_count" in self.fields:
            self.fields["segment_count"].min_value = 1
        if "capacity" in self.fields:
            self.fields["capacity"].min_value = 1
