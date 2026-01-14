import json

from django import forms
from django.conf import settings
from django.utils import translation
from django.utils.text import slugify
from .blocks import normalise_theme
from .models import Page


class PageForm(forms.ModelForm):
    body = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 18,
                "class": "code-field",
                "spellcheck": "false",
                "data-code-field": "html",
            }
        ),
        help_text="Full HTML document fragment rendered when custom code mode is enabled.",
    )
    custom_css = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 12,
                "class": "code-field",
                "spellcheck": "false",
                "data-code-field": "css",
            }
        ),
        help_text="Optional CSS overrides injected into the public page when custom code mode is enabled.",
    )
    custom_js = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 12,
                "class": "code-field",
                "spellcheck": "false",
                "data-code-field": "js",
            }
        ),
        help_text="Optional inline JavaScript executed at the end of the page.",
    )
    blocks = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"data-page-blocks": "json"}),
    )
    theme = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"data-page-theme": "json"}),
    )
    custom_nav_items = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"data-nav-items": "json"}),
    )
    layout_override = forms.BooleanField(
        required=False,
        label="Make layout unique for this language",
    )

    class Meta:
        model = Page
        fields = [
            "title",
            "slug",
            "summary",
            "status",
            "is_visible",
            "show_navigation_bar",
            "render_body_only",
            "navigation_order",
            "custom_nav_items",
            "hero_image",
            "body",
            "custom_css",
            "custom_js",
            "blocks",
            "theme",
        ]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "navigation_order": forms.NumberInput(attrs={"min": 0}),
            "render_body_only": forms.CheckboxInput(),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get("slug")
        title = self.cleaned_data.get("title")
        if slug:
            return slugify(slug)
        if title:
            return slugify(title)
        return slug

    def clean_blocks(self):
        data = self.cleaned_data.get("blocks")
        if not data:
            return []
        if isinstance(data, list):
            return data
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError as exc:  # pragma: no cover - user input
            raise forms.ValidationError("Blocks payload must be valid JSON.") from exc
        if not isinstance(parsed, list):
            raise forms.ValidationError("Blocks payload must be a JSON array.")
        return parsed

    def __init__(self, *args, language=None, **kwargs):
        self.language = language or translation.get_language() or settings.MODELTRANSLATION_DEFAULT_LANGUAGE
        super().__init__(*args, **kwargs)
        initial_nav = (
            self.instance.custom_nav_items
            if self.instance and self.instance.custom_nav_items
            else []
        )
        try:
            initial_json = json.dumps(initial_nav)
        except TypeError:
            initial_json = "[]"
        self.fields["custom_nav_items"].initial = initial_json
        self.initial["custom_nav_items"] = initial_json

        # Blocks per language
        if self.instance:
            blocks_initial = self.instance.get_blocks_for_language(self.language)
        else:
            blocks_initial = []
        try:
            blocks_json = json.dumps(blocks_initial)
        except TypeError:
            blocks_json = "[]"
        self.fields["blocks"].initial = blocks_json
        self.initial["blocks"] = blocks_json

        overrides = set(self.instance.layout_overrides or []) if self.instance else set()
        self.fields["layout_override"].initial = self.language in overrides

        theme_initial = {}
        if self.instance and self.instance.theme:
            theme_initial = self.instance.theme
        try:
            theme_json = json.dumps(theme_initial)
        except TypeError:
            theme_json = "{}"
        self.fields["theme"].initial = theme_json
        self.initial["theme"] = theme_json

    def clean_custom_nav_items(self):
        raw = self.cleaned_data.get("custom_nav_items") or "[]"
        if isinstance(raw, list):
            parsed = raw
        else:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise forms.ValidationError("Navigation items payload must be JSON.") from exc
        if not isinstance(parsed, list):
            raise forms.ValidationError("Navigation items must be an array.")
        cleaned = []
        for slug in parsed:
            if not isinstance(slug, str):
                continue
            slug_norm = slugify(slug.strip()) or slug.strip()
            if slug_norm == "__login":
                slug_norm = "login"
            if not slug_norm or slug_norm in cleaned:
                continue
            cleaned.append(slug_norm)
        return cleaned

    def clean(self):
        data = super().clean()
        return data

    def clean_theme(self):
        raw = self.cleaned_data.get("theme") or "{}"
        if isinstance(raw, dict):
            value = raw
        else:
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise forms.ValidationError("Theme payload must be JSON.") from exc
        if value is None:
            value = {}
        return normalise_theme(value)

    def save(self, commit=True):
        page = super().save(commit=False)
        page.theme = self.cleaned_data.get("theme") or {}
        blocks_data = self.cleaned_data.get("blocks") or []
        override = bool(self.cleaned_data.get("layout_override"))
        page.set_blocks_for_language(self.language, blocks_data, override)
        if commit:
            page.save()
            self.save_m2m()
        return page


class PagePreviewForm(PageForm):
    """
    Variant of PageForm that skips unique validation so we can preview drafts
    without colliding on existing slugs.
    """

    def validate_unique(self):
        # Skip unique checks for preview-only rendering.
        return
