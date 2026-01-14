# app/setup/forms.py
# ---------------------------------------------------------------------------
# Forms for the BAR CMS "setup" section (global site settings, hours, tiers,
# visibility rules). Everything is optional to allow partial saves.
# ---------------------------------------------------------------------------

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from django import forms
from django.conf import settings as dj_settings
from django.contrib.auth.models import Group
from django.forms import ModelForm
from django.forms.models import inlineformset_factory, modelformset_factory

from .models import MembershipTier, OpeningHour, SiteSettings, VisibilityRule
from .widgets import SetupClearableFileInput

SMOKING_CHOICES = (
    ("", "— not specified —"),
    ("true", "Allowed"),
    ("false", "Not allowed"),
)


def guess_default_currency() -> str:
    tz = (getattr(dj_settings, "TIME_ZONE", "") or "").lower()
    if "london" in tz:
        return "GBP"
    if any(x in tz for x in ["zurich", "berlin", "paris", "madrid", "rome", "amsterdam", "vienna"]):
        return "EUR"
    if any(x in tz for x in ["new_york", "los_angeles", "chicago"]):
        return "USD"
    return "EUR"


def _update_widget(field: forms.Field, **attrs) -> None:
    field.widget.attrs.update(attrs)


class SettingsForm(ModelForm):
    """Primary form for global site settings."""

    enabled_languages = forms.MultipleChoiceField(
        required=False,
        choices=dj_settings.LANGUAGES,
        widget=forms.CheckboxSelectMultiple,
        label="Enabled languages",
        help_text="Uncheck a language to hide it from both the public site and the CMS language switcher.",
    )
    currency_text = forms.CharField(
        required=False,
        help_text="Pick from list or type your own.",
        widget=forms.TextInput(
            attrs={"list": "currency_list", "placeholder": "EUR", "id": "currency_text"}
        ),
    )

    # Policies & accessibility (unchanged)
    smoking_allowed = forms.TypedChoiceField(
        required=False,
        choices=SMOKING_CHOICES,
        widget=forms.Select,
        coerce=lambda v: {"true": True, "false": False}.get(v),
        label="Smoking allowed?",
        help_text="If left unspecified, no smoking policy is published.",
    )
    pets_allowed_text = forms.CharField(required=False, label="Pets")
    typical_age_range = forms.CharField(required=False, label="Typical age range")
    minors_policy_note = forms.CharField(required=False, label="Kids/Minors note")

    acc_step_free = forms.BooleanField(required=False, label="Step-free entrance")
    acc_wheelchair = forms.BooleanField(required=False, label="Wheelchair accessible")
    acc_accessible_wc = forms.BooleanField(required=False, label="Accessible restroom")
    acc_visual_aid = forms.BooleanField(required=False, label="Visual assistance available")
    acc_service_animals = forms.BooleanField(required=False, label="Service animals welcome")
    lgbtq_friendly = forms.BooleanField(required=False, label="LGBTQIA+ friendly")

    accessibility_summary = forms.CharField(required=False, widget=forms.Textarea)
    maximum_attendee_capacity = forms.IntegerField(required=False, min_value=0)
    awareness_team_available = forms.BooleanField(required=False)
    awareness_contact = forms.CharField(required=False, label="Awareness contact (free text)")
    icon_pack = forms.FileField(
        required=False,
        label="Site icon pack (ZIP)",
        widget=SetupClearableFileInput,
        help_text=(
            "Upload favicon.ico, favicon.svg, apple-touch-icon.png, favicon-96x96.png, "
            "web-app-manifest-192x192.png, web-app-manifest-512x512.png, and site.webmanifest. "
            'Generate these files via <a href="https://realfavicongenerator.net/" target="_blank" '
            'rel="noopener">RealFaviconGenerator</a> (download the favicon package ZIP) and upload it here. '
            "Replaces previous icons."
        ),
    )

    class Meta:
        model = SiteSettings
        fields = [
            # General
            "org_name",
            "logo",
            "publish_opening_times",
            "public_pages_enabled",
            "dev_login_enabled",
            "enabled_languages",
            # Address & geodata
            "address_street",
            "address_number",
            "address_postal_code",
            "address_city",
            "address_state",
            "address_country",
            "address_autocomplete",
            "geo_lat",
            "geo_lng",
            "price_range",
            "default_currency",
            # Contact & web
            "contact_email",
            "contact_phone",
            "website_url",
            # Socials
            "social_facebook",
            "social_instagram",
            "social_twitter",
            "social_tiktok",
            "social_youtube",
            "social_spotify",
            "social_soundcloud",
            "social_bandcamp",
            "social_linkedin",
            "social_mastodon",
            # SameAs
            "same_as",
            # Policies & accessibility
            "smoking_allowed",
            "pets_allowed_text",
            "typical_age_range",
            "minors_policy_note",
            "acc_step_free",
            "acc_wheelchair",
            "acc_accessible_wc",
            "acc_visual_aid",
            "acc_service_animals",
            "lgbtq_friendly",
            "accessibility_summary",
            "maximum_attendee_capacity",
            "awareness_team_available",
            "awareness_contact",
        ]
        widgets = {
            "same_as": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "https://example.com\nhttps://twitter.com/your-handle",
                }
            ),
            "price_range": forms.TextInput(attrs={"placeholder": "$$, $$$"}),
            "contact_email": forms.EmailInput(attrs={"placeholder": "you@example.com"}),
            "website_url": forms.URLInput(attrs={"placeholder": "https://example.com"}),
            "social_facebook": forms.URLInput(
                attrs={"placeholder": "https://facebook.com/yourpage"}
            ),
            "social_instagram": forms.URLInput(
                attrs={"placeholder": "https://instagram.com/yourhandle"}
            ),
            "social_twitter": forms.URLInput(attrs={"placeholder": "https://x.com/yourhandle"}),
            "social_tiktok": forms.URLInput(
                attrs={"placeholder": "https://tiktok.com/@yourhandle"}
            ),
            "social_youtube": forms.URLInput(
                attrs={"placeholder": "https://youtube.com/@yourchannel"}
            ),
            "social_spotify": forms.URLInput(
                attrs={"placeholder": "https://open.spotify.com/artist/..."}
            ),
            "social_soundcloud": forms.URLInput(
                attrs={"placeholder": "https://soundcloud.com/yourhandle"}
            ),
            "social_bandcamp": forms.URLInput(
                attrs={"placeholder": "https://yourname.bandcamp.com"}
            ),
            "social_linkedin": forms.URLInput(
                attrs={"placeholder": "https://linkedin.com/company/your-company"}
            ),
            "social_mastodon": forms.URLInput(
                attrs={"placeholder": "https://mastodon.social/@yourhandle"}
            ),
        }
        labels = {
            "address_street": "Street address",
            "address_number": "Street number",
            "address_postal_code": "ZIP or postal code (optional)",
            "address_city": "City",
            "address_state": "State / region",
            "address_country": "Country or region",
            "contact_email": "Email",
            "contact_phone": "Phone",
            "website_url": "Website",
            "same_as": "Same as",
            "price_range": "Price range",
            "default_currency": "Default currency",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ("logo",):
            if field_name in self.fields:
                self.fields[field_name].widget = SetupClearableFileInput()
                self.fields[field_name].widget.attrs["data_preview"] = "image"
        if "icon_pack" in self.fields and not isinstance(
            self.fields["icon_pack"].widget, SetupClearableFileInput
        ):
            self.fields["icon_pack"].widget = SetupClearableFileInput()
        if getattr(self.instance, "logo", None) and self.instance.logo.name:
            self.fields["logo"].widget.attrs["data-current"] = self.instance.logo.name
        if getattr(self.instance, "icon_pack_filename", ""):
            self.fields["icon_pack"].widget.attrs["data-current"] = self.instance.icon_pack_filename

        if "enabled_languages" in self.fields:
            if getattr(self.instance, "enabled_languages", None):
                initial_langs = list(getattr(self.instance, "enabled_languages", []))
            else:
                initial_langs = [code for code, _ in dj_settings.LANGUAGES]
            self.initial["enabled_languages"] = initial_langs
            self.fields["enabled_languages"].initial = initial_langs

        self.fields["currency_text"].initial = (
            self.instance.default_currency or guess_default_currency()
        )

        self.use_required_attribute = False
        for f in self.fields.values():
            f.required = False
            f.error_messages["required"] = ""

        def _update_widget_fields(name, **attrs):
            return _update_widget(self.fields[name], **attrs) if name in self.fields else None

        if "org_name" in self.fields:
            existing = dict(self.fields["org_name"].widget.attrs)
            self.fields["org_name"].widget = forms.TextInput(attrs=existing)
        _update_widget_fields(
            "address_street", id="street-address", autocomplete="address-line1", enterkeyhint="next"
        )
        _update_widget_fields(
            "address_number", id="street-number", autocomplete="address-line2", enterkeyhint="next"
        )
        _update_widget_fields(
            "address_postal_code",
            id="postal-code",
            autocomplete="postal-code",
            enterkeyhint="next",
            **{"class": "postal-code"},
        )
        _update_widget_fields(
            "address_city", id="city", autocomplete="address-level2", enterkeyhint="next"
        )
        _update_widget_fields(
            "address_state", id="state", autocomplete="address-level1", enterkeyhint="next"
        )
        _update_widget_fields(
            "address_country", id="country", autocomplete="country", enterkeyhint="done"
        )
        _update_widget_fields("geo_lat", id="geo-lat", step="0.000001", inputmode="decimal")
        _update_widget_fields("geo_lng", id="geo-lng", step="0.000001", inputmode="decimal")
        for multi in ("inventory_notification_groups", "inventory_dashboard_groups"):
            if multi in self.fields:
                self.fields[multi].widget.attrs.update({"class": "form-select", "size": "6"})

    def _quantize_coord(self, value):
        if value in (None, ""):
            return value
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    def clean_geo_lat(self):
        value = self.cleaned_data.get("geo_lat")
        if value in (None, ""):
            return value
        try:
            return self._quantize_coord(value)
        except Exception:
            raise forms.ValidationError("Enter a valid latitude with up to 6 decimals.")

    def clean_geo_lng(self):
        value = self.cleaned_data.get("geo_lng")
        if value in (None, ""):
            return value
        try:
            return self._quantize_coord(value)
        except Exception:
            raise forms.ValidationError("Enter a valid longitude with up to 6 decimals.")

    def clean_enabled_languages(self):
        """
        Persist selected languages as a list. Returning [] signals that all languages are allowed.
        If the user keeps every language selected, collapse back to [] so new languages appear automatically.
        """
        values = self.cleaned_data.get("enabled_languages") or []
        selected = set(values)
        all_codes = {code for code, _ in dj_settings.LANGUAGES}
        if all_codes and selected == all_codes:
            return []
        return list(values)

    def clean(self):
        data = super().clean()
        # ---- Currency
        cur_from_post = self.data.get("currency_text")
        cur_from_clean = self.cleaned_data.get("currency_text")
        cur_from_model_field = self.cleaned_data.get("default_currency")
        cur = (
            cur_from_post
            or cur_from_clean
            or cur_from_model_field
            or guess_default_currency()
            or "EUR"
        ).upper()
        data["default_currency"] = cur
        self.cleaned_data["default_currency"] = cur

        return data


class OpeningHourForm(ModelForm):
    class Meta:
        model = OpeningHour
        fields = ["weekday", "closed", "open_time", "close_time"]
        widgets = {
            "weekday": forms.HiddenInput(),
            "open_time": forms.TimeInput(attrs={"type": "time"}),
            "close_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def clean_weekday(self):
        return self.instance.weekday


TierFormSet = inlineformset_factory(
    parent_model=SiteSettings,
    model=MembershipTier,
    fields=["name", "months", "price_minor", "active"],
    extra=1,
    can_delete=True,
)

HourFormSet = inlineformset_factory(
    parent_model=SiteSettings,
    model=OpeningHour,
    form=OpeningHourForm,
    fields=["weekday", "closed", "open_time", "close_time"],
    extra=0,
    can_delete=False,
    max_num=7,
)

GroupFormSet = modelformset_factory(
    model=Group,
    fields=["name"],
    extra=1,
    can_delete=True,
)

class VisibilityRuleForm(ModelForm):
    class Meta:
        model = VisibilityRule
        fields = ["key", "label", "is_enabled", "allowed_groups", "notes"]
        widgets = {"allowed_groups": forms.CheckboxSelectMultiple}
    inventory_notification_groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.order_by("name"),
        required=False,
        widget=forms.SelectMultiple(attrs={"size": 6}),
        label="Inventory notifications",
        help_text="Members of these groups receive reorder messages.",
    )
    inventory_dashboard_groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.order_by("name"),
        required=False,
        widget=forms.SelectMultiple(attrs={"size": 6}),
        label="Dashboard visibility",
        help_text="Members of these groups see inventory alerts on the dashboard.",
    )
