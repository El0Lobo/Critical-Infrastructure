"""Tests for Band model."""

from datetime import date
from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from app.bands.models import Band


class BandModelTests(TestCase):
    """Test Band model fields and methods."""

    def test_create_band(self):
        """Test creating a band."""
        band = Band.objects.create(
            name="The Test Band", slug="the-test-band", performer_type=Band.PerformerType.BAND
        )
        self.assertEqual(band.name, "The Test Band")
        self.assertEqual(band.slug, "the-test-band")
        self.assertEqual(band.performer_type, Band.PerformerType.BAND)

    def test_band_auto_slug(self):
        """Band should auto-generate slug from name."""
        band = Band.objects.create(name="Amazing Jazz Trio")
        self.assertEqual(band.slug, "amazing-jazz-trio")

    def test_band_str(self):
        """__str__ should return band name."""
        band = Band.objects.create(name="Test Band")
        self.assertEqual(str(band), "Test Band")

    def test_performer_types(self):
        """Test all performer type choices."""
        types = [
            (Band.PerformerType.BAND, "Band"),
            (Band.PerformerType.DJ, "DJ"),
            (Band.PerformerType.SOLO, "Solo artist"),
        ]
        for ptype, _ in types:
            with self.subTest(performer_type=ptype):
                band = Band.objects.create(name=f"Test {ptype}", performer_type=ptype)
                self.assertEqual(band.performer_type, ptype)

    def test_compensation_types(self):
        """Test all compensation type choices."""
        types = [
            (Band.CompensationType.FIXED, Decimal("500.00")),
            (Band.CompensationType.DOOR, Decimal("10.00")),
            (Band.CompensationType.UNPAID, None),
        ]
        for ctype, fee in types:
            with self.subTest(compensation_type=ctype):
                band = Band.objects.create(
                    name=f"Test {ctype}",
                    compensation_type=ctype,
                    fee_amount=fee if ctype == Band.CompensationType.FIXED else None,
                    entry_price=fee if ctype == Band.CompensationType.DOOR else None,
                )
                self.assertEqual(band.compensation_type, ctype)

    def test_compensation_default_unpaid(self):
        """Compensation should default to unpaid."""
        band = Band.objects.create(name="Test Band")
        self.assertEqual(band.compensation_type, Band.CompensationType.UNPAID)

    def test_contact_type_choices(self):
        """Test all contact type choices."""
        types = [
            (Band.ContactType.EMAIL, "test@example.com"),
            (Band.ContactType.PHONE, "+1234567890"),
            (Band.ContactType.URL, "https://example.com"),
            (Band.ContactType.OTHER, "Discord: testuser#1234"),
        ]
        for ctype, value in types:
            with self.subTest(contact_type=ctype):
                band = Band.objects.create(
                    name=f"Test {ctype}", contact_type=ctype, contact_value=value
                )
                self.assertEqual(band.contact_type, ctype)
                self.assertEqual(band.contact_value, value)

    def test_band_compensation_tracking(self):
        """Test compensation tracking fields."""
        band = Band.objects.create(
            name="Paid Band",
            compensation_type=Band.CompensationType.FIXED,
            fee_amount=Decimal("500.00"),
            payout_amount=Decimal("500.00"),
        )
        self.assertEqual(band.fee_amount, Decimal("500.00"))
        self.assertEqual(band.payout_amount, Decimal("500.00"))

    def test_band_door_deal_tracking(self):
        """Test door deal tracking fields."""
        band = Band.objects.create(
            name="Door Deal Band",
            compensation_type=Band.CompensationType.DOOR,
            entry_price=Decimal("15.00"),
            payout_amount=Decimal("450.00"),
        )
        self.assertEqual(band.entry_price, Decimal("15.00"))
        self.assertEqual(band.payout_amount, Decimal("450.00"))

    def test_band_last_performed_on(self):
        """Test last_performed_on field."""
        performed_date = date(2024, 1, 15)
        band = Band.objects.create(name="Regular Band", last_performed_on=performed_date)
        self.assertEqual(band.last_performed_on, performed_date)

    def test_band_publication_status(self):
        """Test publication status fields."""
        band = Band.objects.create(name="Published Band", is_published=True)
        self.assertTrue(band.is_published)

        band2 = Band.objects.create(name="Unpublished Band", is_published=False)
        self.assertFalse(band2.is_published)

    def test_band_social_media_links(self):
        """Test social media link fields."""
        band = Band.objects.create(
            name="Social Band",
            website="https://example.com",
            instagram="https://instagram.com/band",
            facebook="https://facebook.com/band",
            youtube="https://youtube.com/band",
            bandcamp="https://bandcamp.com/band",
            soundcloud="https://soundcloud.com/band",
        )
        self.assertEqual(band.website, "https://example.com")
        self.assertEqual(band.instagram, "https://instagram.com/band")
        self.assertEqual(band.facebook, "https://facebook.com/band")
        self.assertEqual(band.youtube, "https://youtube.com/band")
        self.assertEqual(band.bandcamp, "https://bandcamp.com/band")
        self.assertEqual(band.soundcloud, "https://soundcloud.com/band")

    def test_band_seo_fields(self):
        """Test SEO field storage."""
        band = Band.objects.create(
            name="SEO Band",
            seo_title="Best Band Ever",
            seo_description="The best band you'll ever see live",
        )
        self.assertEqual(band.seo_title, "Best Band Ever")
        self.assertEqual(band.seo_description, "The best band you'll ever see live")

    def test_band_internal_notes(self):
        """Test internal comment field."""
        band = Band.objects.create(
            name="Test Band", comment_internal="Great to work with, very professional"
        )
        self.assertEqual(band.comment_internal, "Great to work with, very professional")

    def test_band_genre_field(self):
        """Bands can store a genre label."""
        band = Band.objects.create(name="Genre Band", genre="Techno")
        self.assertEqual(band.genre, "Techno")

    def test_band_contact_notes(self):
        """Test contact notes field."""
        band = Band.objects.create(
            name="Test Band",
            contact_type=Band.ContactType.EMAIL,
            contact_value="test@example.com",
            contact_notes="Prefers email, responds quickly",
        )
        self.assertEqual(band.contact_notes, "Prefers email, responds quickly")

    def test_band_og_image_url_property(self):
        """Test og_image_url property returns empty string when no image."""
        band = Band.objects.create(name="Test Band")
        self.assertEqual(band.og_image_url, "")

    def test_band_ordering(self):
        """Bands should be ordered by name."""
        Band.objects.create(name="Zebra Band")
        Band.objects.create(name="Alpha Band")
        Band.objects.create(name="Mike Band")

        bands = list(Band.objects.all())
        self.assertEqual(bands[0].name, "Alpha Band")
        self.assertEqual(bands[1].name, "Mike Band")
        self.assertEqual(bands[2].name, "Zebra Band")

    def test_band_name_unique(self):
        """Band names should be unique."""
        Band.objects.create(name="Unique Band")

        with self.assertRaises(IntegrityError):
            Band.objects.create(name="Unique Band")
