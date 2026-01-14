from decimal import Decimal

from django.contrib.auth.models import Group
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from app.core.encryption import EncryptedCharField, EncryptedEmailField, EncryptedTextField


class SiteSettings(models.Model):
    class Mode(models.TextChoices):
        VENUE = "VENUE", _("Venue / Club")
        BAND = "BAND", _("Band / Artist")
        PERSON = "PERSON", _("Person / Blog")

    # General
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.VENUE)
    org_name = EncryptedCharField(max_length=200, blank=True)
    logo = models.FileField(upload_to="logos/", blank=True, null=True)
    icon_pack_filename = models.CharField(max_length=255, blank=True, help_text="Last uploaded icon pack filename.")

    # Address (structured)
    address_street = EncryptedCharField(max_length=200, blank=True)
    address_number = EncryptedCharField(max_length=20, blank=True)
    address_postal_code = EncryptedCharField(max_length=20, blank=True)
    address_city = EncryptedCharField(max_length=120, blank=True)
    address_state = EncryptedCharField(max_length=120, blank=True)
    address_country = EncryptedCharField(max_length=120, blank=True)
    address_autocomplete = models.BooleanField(
        default=False,
        help_text=_("Enable address autocomplete (requires JS integration)."),
    )

    # Contact / Socials
    contact_email = EncryptedEmailField(blank=True)
    contact_phone = EncryptedCharField(max_length=64, blank=True)
    website_url = models.URLField(blank=True)
    social_facebook = models.URLField(blank=True)
    social_instagram = models.URLField(blank=True)
    social_twitter = models.URLField(blank=True, help_text=_("X / Twitter URL"))
    social_tiktok = models.URLField(blank=True)
    social_youtube = models.URLField(blank=True)
    social_spotify = models.URLField(blank=True)
    social_soundcloud = models.URLField(blank=True)
    social_bandcamp = models.URLField(blank=True)
    social_linkedin = models.URLField(blank=True)
    social_mastodon = models.URLField(blank=True)
    same_as = EncryptedTextField(blank=True, help_text=_("schema.org sameAs: one URL per line"))

    # schema.org-ish extras
    geo_lat = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True, help_text=_("Latitude")
    )
    geo_lng = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True, help_text=_("Longitude")
    )
    price_range = models.CharField(max_length=20, blank=True, help_text=_("e.g., $, $$, $$$"))
    default_currency = models.CharField(
        max_length=8, default="EUR", help_text=_("Currency code (suggested list + free text)")
    )

    # Membership config
    membership_enabled = models.BooleanField(default=False)
    membership_hint = models.CharField(
        max_length=200, blank=True, help_text=_("Short label shown next to money icon.")
    )

    public_pages_enabled = models.BooleanField(
        default=True,
        help_text=_("Expose the public-facing site powered by the Pages app."),
    )
    dev_login_enabled = models.BooleanField(
        default=True,
        help_text=_("Show the developer login shortcut when running in development/test."),
    )
    pos_show_discounts = models.BooleanField(
        default=True,
        help_text=_("Show the Quick Discounts panel in the POS."),
    )
    pos_apply_discounts = models.BooleanField(
        default=True,
        help_text=_("Allow item/order discounts to modify POS totals."),
    )
    pos_show_tax = models.BooleanField(
        default=True,
        help_text=_("Show tax rows in the POS UI."),
    )
    pos_apply_tax = models.BooleanField(
        default=True,
        help_text=_("Apply tax to POS carts when calculating totals."),
    )
    pos_tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("19.00"),
        help_text=_("Default POS tax rate (%)"),
    )

    # Multilingual settings
    enabled_languages = models.JSONField(
        default=list,
        blank=True,
        help_text=_(
            "List of enabled language codes (e.g., ['en', 'es', 'de']). Leave empty to enable all languages."
        ),
    )

    # Legacy field (kept to avoid data loss, no longer edited in the UI)
    required_pages = models.TextField(
        blank=True,
        help_text=_("Legacy field for auto-created pages; no longer used by the UI."),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- Policies & accessibility ------------------------------------------------

    # Smoking policy (tri-state)
    smoking_allowed = models.BooleanField(null=True, blank=True)

    # Pets free text (“dogs only”, “no pets”, etc.)
    pets_allowed_text = models.CharField(max_length=120, blank=True)

    # Family friendliness (age range)
    typical_age_range = models.CharField(max_length=20, blank=True)

    # Accessibility toggles
    acc_step_free = models.BooleanField(default=False)
    acc_wheelchair = models.BooleanField(default=False)
    acc_accessible_wc = models.BooleanField(default=False)
    acc_visual_aid = models.BooleanField(default=False)
    acc_service_animals = models.BooleanField(default=False)

    accessibility_summary = models.TextField(blank=True)

    # LGBTQIA+ friendly badge/toggle
    lgbtq_friendly = models.BooleanField(default=False)

    # Short note for minors policy, e.g. “People under 16 only in company of an adult.”
    minors_policy_note = models.CharField(max_length=200, blank=True)

    # Capacity default for events
    maximum_attendee_capacity = models.PositiveIntegerField(null=True, blank=True)

    # Awareness team availability + single free-text contact
    awareness_team_available = models.BooleanField(default=False)
    awareness_contact = EncryptedCharField(
        max_length=200,
        blank=True,
        help_text=_("Phone, email, URL, or a short instruction (free text)."),
    )
    publish_opening_times = models.BooleanField(
        default=False,
        verbose_name="Show opening times on public pages",
        help_text="If checked, opening times will be rendered on public pages.",
    )
    inventory_notification_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="inventory_notification_sites",
        help_text=_("Users in these groups receive inventory reorder messages. Leave empty to notify superusers only."),
    )
    inventory_dashboard_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="inventory_dashboard_sites",
        help_text=_("Users in these groups see inventory alerts on the dashboard. Leave empty to restrict to superusers."),
    )

    def __str__(self):
        return f"Site Settings ({self.get_mode_display()})"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj

    def get_enabled_languages(self):
        """
        Return list of enabled languages.
        If enabled_languages is empty, return all configured languages from settings.
        Returns list of tuples: [(code, name), ...]
        """
        from django.conf import settings

        all_languages = dict(settings.LANGUAGES)

        # If no languages are explicitly enabled, return all
        if not self.enabled_languages:
            return list(settings.LANGUAGES)

        # Return only enabled languages
        return [
            (code, all_languages[code]) for code in self.enabled_languages if code in all_languages
        ]


class MembershipTier(models.Model):
    settings = models.ForeignKey(SiteSettings, on_delete=models.CASCADE, related_name="tiers")
    name = models.CharField(max_length=120)
    months = models.PositiveIntegerField(default=12)
    price_minor = models.PositiveIntegerField(
        default=0, help_text=_("In minor units (e.g. cents/rappen)")
    )
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("settings", "name")

    def __str__(self):
        return f"{self.name} ({self.months} months)"


class OpeningHour(models.Model):
    settings = models.ForeignKey(SiteSettings, on_delete=models.CASCADE, related_name="hours")
    weekday = models.IntegerField(
        choices=[(i, d) for i, d in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])],
        default=0,
    )
    closed = models.BooleanField(default=False)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = ("settings", "weekday")

    def __str__(self):
        if self.closed:
            return f"{self.get_weekday_display()}: closed"
        return f"{self.get_weekday_display()}: {self.open_time}–{self.close_time}"


class VisibilityRule(models.Model):
    """Attach visibility (allowed groups) to a component key used in templates."""

    key = models.CharField(
        max_length=120,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                r"^[\w\.\-:]+$",
                "Key may contain letters, numbers, underscores, hyphens, dots, or colons.",
            )
        ],
    )
    label = models.CharField(
        max_length=200, blank=True, help_text=_("Human-friendly name; editable.")
    )
    is_enabled = models.BooleanField(default=True)
    allowed_groups = models.ManyToManyField(Group, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.label or self.key
