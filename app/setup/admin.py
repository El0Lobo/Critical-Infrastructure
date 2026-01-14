from django import forms
from django.conf import settings
from django.contrib import admin

from .models import MembershipTier, OpeningHour, SiteSettings, VisibilityRule


class SiteSettingsForm(forms.ModelForm):
    """Custom form for SiteSettings with a better UI for language selection."""

    enabled_languages = forms.MultipleChoiceField(
        choices=settings.LANGUAGES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select which languages to enable. Leave empty to enable all languages.",
    )

    class Meta:
        model = SiteSettings
        fields = [
            "mode",
            "org_name",
            "logo",
            "public_pages_enabled",
            "dev_login_enabled",
            "enabled_languages",
            "address_street",
            "address_number",
            "address_postal_code",
            "address_city",
            "address_state",
            "address_country",
            "address_autocomplete",
            "geo_lat",
            "geo_lng",
            "contact_email",
            "contact_phone",
            "website_url",
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
            "same_as",
            "price_range",
            "default_currency",
            "maximum_attendee_capacity",
            "publish_opening_times",
            "membership_enabled",
            "membership_hint",
            "smoking_allowed",
            "pets_allowed_text",
            "typical_age_range",
            "minors_policy_note",
            "lgbtq_friendly",
            "acc_step_free",
            "acc_wheelchair",
            "acc_accessible_wc",
            "acc_visual_aid",
            "acc_service_animals",
            "accessibility_summary",
            "awareness_team_available",
            "awareness_contact",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate with existing enabled languages
        if self.instance and self.instance.enabled_languages:
            self.initial["enabled_languages"] = self.instance.enabled_languages

    def clean_enabled_languages(self):
        """Convert list of selected language codes to the format expected by the model."""
        selected = self.cleaned_data.get("enabled_languages", [])
        # Return as list for JSONField
        return list(selected) if selected else []


class TierInline(admin.TabularInline):
    model = MembershipTier
    extra = 1


class HourInline(admin.TabularInline):
    model = OpeningHour
    extra = 0
    max_num = 7
    can_delete = False


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    form = SiteSettingsForm
    inlines = [TierInline, HourInline]
    list_display = ("mode", "org_name", "membership_enabled", "default_currency", "updated_at")
    fieldsets = (
        (
            "General",
            {
                "fields": (
                    "mode",
                    "org_name",
                    "logo",
                    "public_pages_enabled",
                    "dev_login_enabled",
                )
            },
        ),
        (
            "Multilingual Settings",
            {
                "fields": ("enabled_languages",),
                "description": "Configure which languages are available on your site. "
                "Uncheck all to enable all languages.",
            },
        ),
        (
            "Address",
            {
                "fields": (
                    "address_street",
                    "address_number",
                    "address_postal_code",
                    "address_city",
                    "address_state",
                    "address_country",
                    "address_autocomplete",
                    "geo_lat",
                    "geo_lng",
                )
            },
        ),
        (
            "Contact & Social",
            {
                "fields": (
                    "contact_email",
                    "contact_phone",
                    "website_url",
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
                    "same_as",
                )
            },
        ),
        (
            "Business Info",
            {
                "fields": (
                    "price_range",
                    "default_currency",
                    "maximum_attendee_capacity",
                    "publish_opening_times",
                )
            },
        ),
        (
            "Membership",
            {
                "fields": (
                    "membership_enabled",
                    "membership_hint",
                )
            },
        ),
        (
            "Policies & Accessibility",
            {
                "fields": (
                    "smoking_allowed",
                    "pets_allowed_text",
                    "typical_age_range",
                    "minors_policy_note",
                    "lgbtq_friendly",
                    "acc_step_free",
                    "acc_wheelchair",
                    "acc_accessible_wc",
                    "acc_visual_aid",
                    "acc_service_animals",
                    "accessibility_summary",
                    "awareness_team_available",
                    "awareness_contact",
                )
            },
        ),
    )


@admin.register(VisibilityRule)
class VisibilityRuleAdmin(admin.ModelAdmin):
    list_display = ("key", "label", "is_enabled")
    list_filter = ("is_enabled",)
    filter_horizontal = ("allowed_groups",)
