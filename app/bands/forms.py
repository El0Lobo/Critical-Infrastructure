# app/bands/forms.py
from django import forms
from django.utils.text import slugify

from .models import Band


class BandForm(forms.ModelForm):
    class Meta:
        model = Band
        fields = [
            "performer_type",
            "name",
            "slug",
            "description",
            "genre",
            "photo",
            "last_performed_on",
            "contact_type",
            "contact_value",
            "contact_notes",
            "compensation_type",
            "fee_amount",
            "entry_price",
            "payout_amount",
            "comment_internal",
            "is_published",
            "published_at",
            "seo_title",
            "seo_description",
            "og_image_override",
            "website",
            "instagram",
            "facebook",
            "youtube",
            "bandcamp",
            "soundcloud",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "genre": forms.TextInput(attrs={"placeholder": "House, Indie Rock, Techno…"}),
            "comment_internal": forms.Textarea(attrs={"rows": 4}),
            "seo_description": forms.Textarea(attrs={"rows": 2}),
            "last_performed_on": forms.DateInput(attrs={"type": "date"}),
            "published_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ↓↓↓ key line: prevent field-level "required" from firing before we auto-fill
        self.fields["slug"].required = False

    def clean_slug(self):
        """
        Runs during field-level cleaning, *after* Django's own cleaning but
        before form.clean(). Because we set required=False above, this will
        be called with an empty value and we can generate it here.
        """
        val = self.cleaned_data.get("slug") or ""
        name = self.cleaned_data.get("name") or ""
        if not val and name:
            return slugify(name)[:220]
        return val

    def clean(self):
        cleaned = super().clean()

        # Normalize blank contact values to None (keep the pair consistent)
        for k in ("contact_type", "contact_value"):
            if not cleaned.get(k):
                cleaned[k] = None

        # Default compensation type if radios were untouched
        if not cleaned.get("compensation_type"):
            cleaned["compensation_type"] = "unpaid"

        ctype = cleaned.get("compensation_type")

        # Validation + clear irrelevant money fields
        if ctype == "fixed":
            if not cleaned.get("fee_amount"):
                self.add_error("fee_amount", "Required for fixed fee.")
            cleaned["entry_price"] = (
                None if "entry_price" not in self.errors else cleaned.get("entry_price")
            )
            cleaned["payout_amount"] = (
                None if "payout_amount" not in self.errors else cleaned.get("payout_amount")
            )

        elif ctype == "door":
            if not cleaned.get("entry_price"):
                self.add_error("entry_price", "Entry price required for door deal.")
            if not cleaned.get("payout_amount"):
                self.add_error("payout_amount", "Payout amount required for door deal.")
            cleaned["fee_amount"] = (
                None if "fee_amount" not in self.errors else cleaned.get("fee_amount")
            )

        else:  # unpaid
            for k in ("fee_amount", "entry_price", "payout_amount"):
                if k not in self.errors:
                    cleaned[k] = None

        return cleaned

    def save(self, commit=True):
        obj: Band = super().save(commit=False)

        # Final backstop (normally already set by clean_slug)
        if (not obj.slug) and obj.name:
            obj.slug = slugify(obj.name)[:220]

        # Auto SEO if blank (preserve manual overrides)
        if not obj.seo_title and obj.name:
            obj.seo_title = obj.name
        if not obj.seo_description:
            base = (obj.description or obj.name or "").strip()
            obj.seo_description = base[:155]

        # Keep contact pair consistent
        if not obj.contact_type:
            obj.contact_value = None

        if commit:
            obj.save()
        return obj
