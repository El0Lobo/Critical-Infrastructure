from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Band(models.Model):
    class PerformerType(models.TextChoices):
        BAND = "band", "Band"
        DJ = "dj", "DJ"
        SOLO = "solo", "Solo artist"

    class ContactType(models.TextChoices):
        EMAIL = "email", "Email"
        PHONE = "phone", "Phone"
        URL = "url", "Website/Link"
        OTHER = "other", "Other"

    class CompensationType(models.TextChoices):
        FIXED = "fixed", "Fixed fee"
        DOOR = "door", "Door deal"
        UNPAID = "unpaid", "Unpaid / promo"

    performer_type = models.CharField(
        max_length=10, choices=PerformerType.choices, default=PerformerType.BAND
    )
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=220, help_text="Auto-filled from name; you can edit.")
    description = models.TextField(blank=True)
    genre = models.CharField(max_length=120, blank=True, help_text="Music style (e.g., techno, indie rock).")
    photo = models.ImageField(upload_to="bands/", blank=True, null=True)

    contact_type = models.CharField(max_length=10, choices=ContactType.choices, blank=True)
    contact_value = models.CharField(
        max_length=255, blank=True, help_text="Email, phone number, or URL."
    )
    contact_notes = models.CharField(
        max_length=255, blank=True, help_text="How contact was made / extra notes."
    )

    # Default to unpaid so the form can save even if radios untouched
    compensation_type = models.CharField(
        max_length=10, choices=CompensationType.choices, default=CompensationType.UNPAID
    )
    fee_amount = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Paid amount for fixed fee.",
    )
    entry_price = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True, help_text="Entry price if door deal."
    )
    payout_amount = models.DecimalField(
        max_digits=9, decimal_places=2, blank=True, null=True, help_text="Payout amount they got."
    )

    comment_internal = models.TextField(
        blank=True, help_text="Private notes for staff (not public)."
    )

    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(blank=True, null=True)

    last_performed_on = models.DateField(
        blank=True, null=True, help_text="Date they performed at our venue."
    )

    seo_title = models.CharField(max_length=70, blank=True, help_text="Optional <title> override.")
    seo_description = models.CharField(max_length=160, blank=True, help_text="Meta description.")
    og_image_override = models.ImageField(upload_to="bands/og/", blank=True, null=True)

    website = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    bandcamp = models.URLField(blank=True)
    soundcloud = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    # Backstop to guarantee slug is present even outside forms/admin
    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify(self.name)[:220]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("bands_pub:public_detail", args=[self.slug])

    @property
    def og_image_url(self):
        img = self.og_image_override or self.photo
        return img.url if img else ""
