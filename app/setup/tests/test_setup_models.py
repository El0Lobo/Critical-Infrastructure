"""Tests for Setup models (SiteSettings, MembershipTier, OpeningHour, VisibilityRule)."""

from datetime import time
from decimal import Decimal

from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.test import TestCase

from app.setup.models import MembershipTier, OpeningHour, SiteSettings, VisibilityRule


class SiteSettingsModelTests(TestCase):
    """Test SiteSettings singleton model."""

    def test_get_solo_creates_instance(self):
        """get_solo should create instance if it doesn't exist."""
        settings = SiteSettings.get_solo()
        self.assertIsNotNone(settings)
        self.assertEqual(settings.id, 1)

    def test_get_solo_returns_existing_instance(self):
        """get_solo should return existing instance."""
        settings1 = SiteSettings.get_solo()
        settings2 = SiteSettings.get_solo()
        self.assertEqual(settings1.id, settings2.id)

    def test_settings_str(self):
        """__str__ should show mode display."""
        settings = SiteSettings.get_solo()
        settings.mode = SiteSettings.Mode.VENUE
        settings.save()
        self.assertIn("Venue", str(settings))

    def test_settings_mode_choices(self):
        """Test all mode choices."""
        modes = [
            SiteSettings.Mode.VENUE,
            SiteSettings.Mode.BAND,
            SiteSettings.Mode.PERSON,
        ]
        settings = SiteSettings.get_solo()
        for mode in modes:
            with self.subTest(mode=mode):
                settings.mode = mode
                settings.save()
                settings.refresh_from_db()
                self.assertEqual(settings.mode, mode)

    def test_settings_encrypted_fields(self):
        """Test encrypted field storage and retrieval."""
        settings = SiteSettings.get_solo()
        settings.org_name = "Test Venue"
        settings.address_street = "Main Street"
        settings.address_number = "123"
        settings.address_postal_code = "12345"
        settings.address_city = "Test City"
        settings.address_state = "Test State"
        settings.address_country = "Test Country"
        settings.contact_email = "test@example.com"
        settings.contact_phone = "+1234567890"
        settings.save()

        settings.refresh_from_db()
        self.assertEqual(settings.org_name, "Test Venue")
        self.assertEqual(settings.address_street, "Main Street")
        self.assertEqual(settings.address_number, "123")
        self.assertEqual(settings.address_postal_code, "12345")
        self.assertEqual(settings.address_city, "Test City")
        self.assertEqual(settings.address_state, "Test State")
        self.assertEqual(settings.address_country, "Test Country")
        self.assertEqual(settings.contact_email, "test@example.com")
        self.assertEqual(settings.contact_phone, "+1234567890")

    def test_settings_social_media_fields(self):
        """Test social media URL fields."""
        settings = SiteSettings.get_solo()
        settings.social_facebook = "https://facebook.com/venue"
        settings.social_instagram = "https://instagram.com/venue"
        settings.social_twitter = "https://twitter.com/venue"
        settings.social_tiktok = "https://tiktok.com/@venue"
        settings.social_youtube = "https://youtube.com/venue"
        settings.save()

        settings.refresh_from_db()
        self.assertEqual(settings.social_facebook, "https://facebook.com/venue")
        self.assertEqual(settings.social_instagram, "https://instagram.com/venue")
        self.assertEqual(settings.social_twitter, "https://twitter.com/venue")
        self.assertEqual(settings.social_tiktok, "https://tiktok.com/@venue")
        self.assertEqual(settings.social_youtube, "https://youtube.com/venue")

    def test_settings_geo_coordinates(self):
        """Test geo latitude and longitude fields."""
        settings = SiteSettings.get_solo()
        settings.geo_lat = Decimal("47.123456")
        settings.geo_lng = Decimal("8.654321")
        settings.save()

        settings.refresh_from_db()
        self.assertEqual(settings.geo_lat, Decimal("47.123456"))
        self.assertEqual(settings.geo_lng, Decimal("8.654321"))

    def test_settings_accessibility_flags(self):
        """Test accessibility flag fields."""
        settings = SiteSettings.get_solo()
        settings.acc_step_free = True
        settings.acc_wheelchair = True
        settings.acc_accessible_wc = True
        settings.acc_visual_aid = True
        settings.acc_service_animals = True
        settings.save()

        settings.refresh_from_db()
        self.assertTrue(settings.acc_step_free)
        self.assertTrue(settings.acc_wheelchair)
        self.assertTrue(settings.acc_accessible_wc)
        self.assertTrue(settings.acc_visual_aid)
        self.assertTrue(settings.acc_service_animals)

    def test_settings_lgbtq_friendly_flag(self):
        """Test LGBTQ+ friendly flag."""
        settings = SiteSettings.get_solo()
        settings.lgbtq_friendly = True
        settings.save()

        settings.refresh_from_db()
        self.assertTrue(settings.lgbtq_friendly)

    def test_settings_smoking_allowed_tristate(self):
        """Test smoking_allowed tristate (null, True, False)."""
        settings = SiteSettings.get_solo()

        settings.smoking_allowed = None
        settings.save()
        settings.refresh_from_db()
        self.assertIsNone(settings.smoking_allowed)

        settings.smoking_allowed = True
        settings.save()
        settings.refresh_from_db()
        self.assertTrue(settings.smoking_allowed)

        settings.smoking_allowed = False
        settings.save()
        settings.refresh_from_db()
        self.assertFalse(settings.smoking_allowed)

    def test_settings_membership_enabled(self):
        """Test membership_enabled flag."""
        settings = SiteSettings.get_solo()
        settings.membership_enabled = True
        settings.save()

        settings.refresh_from_db()
        self.assertTrue(settings.membership_enabled)

    def test_settings_awareness_team(self):
        """Test awareness team fields."""
        settings = SiteSettings.get_solo()
        settings.awareness_team_available = True
        settings.awareness_contact = "awareness@example.com"
        settings.save()

        settings.refresh_from_db()
        self.assertTrue(settings.awareness_team_available)
        self.assertEqual(settings.awareness_contact, "awareness@example.com")


class MembershipTierModelTests(TestCase):
    """Test MembershipTier model."""

    def setUp(self):
        self.settings = SiteSettings.get_solo()

    def test_create_membership_tier(self):
        """Test creating a membership tier."""
        tier = MembershipTier.objects.create(
            settings=self.settings, name="Annual", months=12, price_minor=5000
        )
        self.assertEqual(tier.name, "Annual")
        self.assertEqual(tier.months, 12)
        self.assertEqual(tier.price_minor, 5000)
        self.assertTrue(tier.active)

    def test_tier_str(self):
        """__str__ should show name and months."""
        tier = MembershipTier.objects.create(settings=self.settings, name="Quarterly", months=3)
        self.assertIn("Quarterly", str(tier))
        self.assertIn("3", str(tier))

    def test_tier_active_default_true(self):
        """Active should default to True."""
        tier = MembershipTier.objects.create(settings=self.settings, name="Test")
        self.assertTrue(tier.active)

    def test_tier_months_default(self):
        """Months should default to 12."""
        tier = MembershipTier.objects.create(settings=self.settings, name="Test")
        self.assertEqual(tier.months, 12)

    def test_tier_price_minor_default(self):
        """price_minor should default to 0."""
        tier = MembershipTier.objects.create(settings=self.settings, name="Free")
        self.assertEqual(tier.price_minor, 0)

    def test_tier_unique_together(self):
        """Tier name should be unique per settings."""
        MembershipTier.objects.create(settings=self.settings, name="Annual")

        with self.assertRaises(IntegrityError):
            MembershipTier.objects.create(settings=self.settings, name="Annual")


class OpeningHourModelTests(TestCase):
    """Test OpeningHour model."""

    def setUp(self):
        self.settings = SiteSettings.get_solo()

    def test_create_opening_hour(self):
        """Test creating an opening hour."""
        hour = OpeningHour.objects.create(
            settings=self.settings,
            weekday=0,  # Monday
            open_time=time(18, 0),
            close_time=time(2, 0),
        )
        self.assertEqual(hour.weekday, 0)
        self.assertEqual(hour.open_time, time(18, 0))
        self.assertEqual(hour.close_time, time(2, 0))
        self.assertFalse(hour.closed)

    def test_opening_hour_closed_day(self):
        """Test marking a day as closed."""
        hour = OpeningHour.objects.create(settings=self.settings, weekday=1, closed=True)  # Tuesday
        self.assertTrue(hour.closed)

    def test_opening_hour_str_open(self):
        """__str__ should show weekday and hours when open."""
        hour = OpeningHour.objects.create(
            settings=self.settings,
            weekday=5,  # Saturday
            open_time=time(20, 0),
            close_time=time(3, 0),
        )
        hour_str = str(hour)
        self.assertIn("Sat", hour_str)
        self.assertIn("20:00", hour_str)
        self.assertIn("03:00", hour_str)

    def test_opening_hour_str_closed(self):
        """__str__ should show 'closed' when day is closed."""
        hour = OpeningHour.objects.create(settings=self.settings, weekday=6, closed=True)  # Sunday
        hour_str = str(hour)
        self.assertIn("Sun", hour_str)
        self.assertIn("closed", hour_str)

    def test_opening_hour_weekday_choices(self):
        """Test all weekday choices."""
        for day in range(7):
            with self.subTest(weekday=day):
                hour = OpeningHour.objects.create(
                    settings=self.settings,
                    weekday=day,
                    open_time=time(12, 0),
                    close_time=time(23, 0),
                )
                self.assertEqual(hour.weekday, day)

    def test_opening_hour_unique_together(self):
        """Weekday should be unique per settings."""
        OpeningHour.objects.create(
            settings=self.settings, weekday=0, open_time=time(18, 0), close_time=time(2, 0)
        )

        with self.assertRaises(IntegrityError):
            OpeningHour.objects.create(
                settings=self.settings, weekday=0, open_time=time(19, 0), close_time=time(3, 0)
            )


class VisibilityRuleModelTests(TestCase):
    """Test VisibilityRule model."""

    def test_create_visibility_rule(self):
        """Test creating a visibility rule."""
        rule = VisibilityRule.objects.create(
            key="feature.advanced_settings", label="Advanced Settings"
        )
        self.assertEqual(rule.key, "feature.advanced_settings")
        self.assertEqual(rule.label, "Advanced Settings")
        self.assertTrue(rule.is_enabled)

    def test_rule_str_with_label(self):
        """__str__ should return label if set."""
        rule = VisibilityRule.objects.create(key="test.feature", label="Test Feature")
        self.assertEqual(str(rule), "Test Feature")

    def test_rule_str_without_label(self):
        """__str__ should return key if no label."""
        rule = VisibilityRule.objects.create(key="test.feature")
        self.assertEqual(str(rule), "test.feature")

    def test_rule_is_enabled_default_true(self):
        """is_enabled should default to True."""
        rule = VisibilityRule.objects.create(key="test")
        self.assertTrue(rule.is_enabled)

    def test_rule_allowed_groups(self):
        """Test allowed_groups many-to-many relationship."""
        group1 = Group.objects.create(name="Admins")
        group2 = Group.objects.create(name="Staff")

        rule = VisibilityRule.objects.create(key="admin.feature")
        rule.allowed_groups.add(group1, group2)

        self.assertEqual(rule.allowed_groups.count(), 2)
        self.assertIn(group1, rule.allowed_groups.all())
        self.assertIn(group2, rule.allowed_groups.all())

    def test_rule_key_unique(self):
        """Rule keys should be unique."""
        VisibilityRule.objects.create(key="unique.key")

        with self.assertRaises(IntegrityError):
            VisibilityRule.objects.create(key="unique.key")

    def test_rule_key_validation(self):
        """Test key validation pattern."""
        # Valid keys
        valid_keys = [
            "simple",
            "dotted.key",
            "hyphen-key",
            "under_score",
            "colon:key",
            "complex.key-with_all:chars",
        ]
        for key in valid_keys:
            with self.subTest(key=key):
                rule = VisibilityRule.objects.create(key=key)
                self.assertEqual(rule.key, key)
                rule.delete()  # Clean up for next iteration

    def test_rule_notes_field(self):
        """Test notes field."""
        rule = VisibilityRule.objects.create(key="test", notes="Only for admin users")
        self.assertEqual(rule.notes, "Only for admin users")
