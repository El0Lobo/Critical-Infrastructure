from __future__ import annotations

from django import forms
from django.utils import timezone

from .models import NewsPoll, NewsPost, bulk_set_poll_options


class NewsPostForm(forms.ModelForm):
    class Meta:
        model = NewsPost
        fields = [
            "title",
            "slug",
            "summary",
            "body",
            "category",
            "hero_image",
            "visibility",
            "status",
            "pin_until",
        ]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "body": forms.Textarea(attrs={"class": "tinymce-editor"}),
            "pin_until": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean_pin_until(self):
        value = self.cleaned_data.get("pin_until")
        if value and value <= timezone.now():
            raise forms.ValidationError("Pin expiry must be in the future.")
        return value


class NewsPollForm(forms.ModelForm):
    options = forms.CharField(
        help_text="Enter one option per line (minimum 2).",
        widget=forms.Textarea(attrs={"rows": 5}),
    )

    class Meta:
        model = NewsPoll
        fields = [
            "question",
            "description",
            "allow_multiple",
            "anonymous",
            "allow_results_before_vote",
            "opens_at",
            "closes_at",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "opens_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "closes_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        options_initial = kwargs.pop("options_initial", None)
        super().__init__(*args, **kwargs)
        if options_initial is not None:
            self.fields["options"].initial = options_initial
        elif self.instance.pk:
            existing = "\n".join(opt.label for opt in self.instance.options.all())
            self.fields["options"].initial = existing

    def clean_options(self):
        raw = self.cleaned_data.get("options", "")
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if len(lines) < 2:
            raise forms.ValidationError("Provide at least two options.")
        if len(lines) != len(set(lines)):
            raise forms.ValidationError("Each option must be unique.")
        return lines

    def save(self, commit=True):
        poll = super().save(commit)
        if commit:
            self.save_options(poll)
        return poll

    def save_options(self, poll):
        options = self.cleaned_data.get("options", [])
        if poll.pk and options:
            bulk_set_poll_options(poll, options)
