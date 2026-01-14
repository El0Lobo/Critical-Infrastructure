"""Tests for UserProfile model, signals, and related models."""

from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.test import TestCase

from app.users.models import BadgeDefinition, FieldPolicy, GroupMeta, UserProfile

User = get_user_model()


class UserProfileSignalTests(TestCase):
    """Test that UserProfile is automatically created when User is created."""

    def test_profile_created_on_user_creation(self):
        """UserProfile should be auto-created via post_save signal."""
        user = User.objects.create_user(username="testuser", password="password123")

        # Profile should exist
        self.assertTrue(hasattr(user, "profile"))
        self.assertIsNotNone(user.profile)
        self.assertEqual(user.profile.user, user)

    def test_profile_not_duplicated_on_user_update(self):
        """Updating a user should not create duplicate profiles."""
        user = User.objects.create_user(username="testuser", password="password123")
        profile_id = user.profile.id

        # Update user
        user.is_active = False
        user.save()

        # Should still have the same profile
        user.refresh_from_db()
        self.assertEqual(user.profile.id, profile_id)
        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)

    def test_multiple_users_get_separate_profiles(self):
        """Each user should get their own profile."""
        user1 = User.objects.create_user(username="user1", password="password123")
        user2 = User.objects.create_user(username="user2", password="password123")

        self.assertNotEqual(user1.profile.id, user2.profile.id)
        self.assertEqual(user1.profile.user, user1)
        self.assertEqual(user2.profile.user, user2)


class UserProfileModelTests(TestCase):
    """Test UserProfile model fields and methods."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.profile = self.user.profile

    def test_profile_defaults(self):
        """Test default values for UserProfile."""
        self.assertEqual(self.profile.legal_name, "")
        self.assertEqual(self.profile.chosen_name, "")
        self.assertEqual(self.profile.pronouns, "")
        self.assertIsNone(self.profile.birth_date)
        self.assertEqual(self.profile.email, "")
        self.assertEqual(self.profile.phone, "")
        self.assertEqual(self.profile.address, "")
        self.assertEqual(self.profile.role_title, "")
        self.assertEqual(self.profile.duties, "")
        self.assertIsNone(self.profile.primary_group)
        self.assertTrue(self.profile.force_password_change)
        self.assertFalse(self.profile.has_selected_visibility)

    def test_encrypted_fields_can_be_set(self):
        """Test that encrypted fields can be set and retrieved."""
        self.profile.legal_name = "Jane Doe"
        self.profile.chosen_name = "Jay"
        self.profile.pronouns = "they/them"
        self.profile.email = "jane@example.com"
        self.profile.phone = "+1234567890"
        self.profile.address = "123 Main St, City, Country"
        self.profile.role_title = "Bar Lead"
        self.profile.duties = "Manage bar staff and inventory"
        self.profile.save()

        # Refresh from DB
        self.profile.refresh_from_db()

        self.assertEqual(self.profile.legal_name, "Jane Doe")
        self.assertEqual(self.profile.chosen_name, "Jay")
        self.assertEqual(self.profile.pronouns, "they/them")
        self.assertEqual(self.profile.email, "jane@example.com")
        self.assertEqual(self.profile.phone, "+1234567890")
        self.assertEqual(self.profile.address, "123 Main St, City, Country")
        self.assertEqual(self.profile.role_title, "Bar Lead")
        self.assertEqual(self.profile.duties, "Manage bar staff and inventory")

    def test_birth_date_field(self):
        """Test birth_date field can store dates."""
        birth_date = date(1990, 5, 15)
        self.profile.birth_date = birth_date
        self.profile.save()

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.birth_date, birth_date)

    def test_str_method_prefers_chosen_name(self):
        """__str__ should prefer chosen_name over legal_name."""
        self.profile.legal_name = "Jane Doe"
        self.profile.chosen_name = "Jay"
        self.profile.save()

        self.assertEqual(str(self.profile), "Jay")

    def test_str_method_falls_back_to_legal_name(self):
        """__str__ should use legal_name if chosen_name is empty."""
        self.profile.legal_name = "Jane Doe"
        self.profile.chosen_name = ""
        self.profile.save()

        self.assertEqual(str(self.profile), "Jane Doe")

    def test_str_method_falls_back_to_username(self):
        """__str__ should use username if both names are empty."""
        self.profile.legal_name = ""
        self.profile.chosen_name = ""
        self.profile.save()

        self.assertEqual(str(self.profile), "testuser")

    def test_primary_group_can_be_set(self):
        """Test primary_group foreign key."""
        group = Group.objects.create(name="Staff")
        self.profile.primary_group = group
        self.profile.save()

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.primary_group, group)

    def test_badges_many_to_many(self):
        """Test badges many-to-many relationship."""
        badge1 = BadgeDefinition.objects.create(name="Veteran", emoji="🏆")
        badge2 = BadgeDefinition.objects.create(name="Bartender", emoji="🍺")

        self.profile.badges.add(badge1, badge2)

        self.assertEqual(self.profile.badges.count(), 2)
        self.assertIn(badge1, self.profile.badges.all())
        self.assertIn(badge2, self.profile.badges.all())

    def test_onboarding_flags(self):
        """Test onboarding flag fields."""
        self.assertTrue(self.profile.force_password_change)
        self.assertFalse(self.profile.has_selected_visibility)

        self.profile.force_password_change = False
        self.profile.has_selected_visibility = True
        self.profile.save()

        self.profile.refresh_from_db()
        self.assertFalse(self.profile.force_password_change)
        self.assertTrue(self.profile.has_selected_visibility)


class BadgeDefinitionTests(TestCase):
    """Test BadgeDefinition model."""

    def test_create_badge(self):
        """Test creating a badge."""
        badge = BadgeDefinition.objects.create(
            name="Bartender", emoji="🍺", description="Serves drinks at the bar"
        )

        self.assertEqual(badge.name, "Bartender")
        self.assertEqual(badge.emoji, "🍺")
        self.assertEqual(badge.description, "Serves drinks at the bar")

    def test_badge_str_with_emoji(self):
        """Test __str__ method with emoji."""
        badge = BadgeDefinition.objects.create(name="Bartender", emoji="🍺")
        self.assertEqual(str(badge), "🍺 Bartender")

    def test_badge_str_without_emoji(self):
        """Test __str__ method without emoji."""
        badge = BadgeDefinition.objects.create(name="Volunteer")
        self.assertEqual(str(badge), "Volunteer")

    def test_badge_name_unique(self):
        """Badge names should be unique."""
        BadgeDefinition.objects.create(name="Bartender")

        with self.assertRaises(IntegrityError):
            BadgeDefinition.objects.create(name="Bartender")

    def test_badge_ordering(self):
        """Badges should be ordered by name."""
        BadgeDefinition.objects.create(name="Zulu")
        BadgeDefinition.objects.create(name="Alpha")
        BadgeDefinition.objects.create(name="Mike")

        badges = list(BadgeDefinition.objects.all())
        self.assertEqual(badges[0].name, "Alpha")
        self.assertEqual(badges[1].name, "Mike")
        self.assertEqual(badges[2].name, "Zulu")


class FieldPolicyTests(TestCase):
    """Test FieldPolicy model."""

    def test_create_field_policy(self):
        """Test creating a field policy."""
        policy = FieldPolicy.objects.create(
            field_name="phone", visibility=FieldPolicy.Visibility.STAFF_ONLY
        )

        self.assertEqual(policy.field_name, "phone")
        self.assertEqual(policy.visibility, FieldPolicy.Visibility.STAFF_ONLY)

    def test_field_policy_default_visibility(self):
        """Test default visibility is AUTHENTICATED."""
        policy = FieldPolicy.objects.create(field_name="email")
        self.assertEqual(policy.visibility, FieldPolicy.Visibility.AUTHENTICATED)

    def test_field_policy_str(self):
        """Test __str__ method."""
        policy = FieldPolicy.objects.create(
            field_name="phone", visibility=FieldPolicy.Visibility.ADMIN_ONLY
        )
        self.assertEqual(str(policy), "phone → ADMIN_ONLY")

    def test_field_name_unique(self):
        """Field names should be unique."""
        FieldPolicy.objects.create(field_name="phone")

        with self.assertRaises(IntegrityError):
            FieldPolicy.objects.create(field_name="phone")

    def test_all_visibility_choices(self):
        """Test all visibility level choices."""
        choices = [
            FieldPolicy.Visibility.ADMIN_ONLY,
            FieldPolicy.Visibility.STAFF_ONLY,
            FieldPolicy.Visibility.AUTHENTICATED,
            FieldPolicy.Visibility.PUBLIC,
        ]

        for idx, choice in enumerate(choices):
            policy = FieldPolicy.objects.create(field_name=f"field_{idx}", visibility=choice)
            self.assertEqual(policy.visibility, choice)


class GroupMetaTests(TestCase):
    """Test GroupMeta model for group priority ranking."""

    def test_create_group_meta(self):
        """Test creating GroupMeta."""
        group = Group.objects.create(name="Admins")
        meta = GroupMeta.objects.create(group=group, rank=1)

        self.assertEqual(meta.group, group)
        self.assertEqual(meta.rank, 1)

    def test_group_meta_default_rank(self):
        """Test default rank is 1000."""
        group = Group.objects.create(name="Volunteers")
        meta = GroupMeta.objects.create(group=group)

        self.assertEqual(meta.rank, 1000)

    def test_group_meta_str(self):
        """Test __str__ method."""
        group = Group.objects.create(name="Staff")
        meta = GroupMeta.objects.create(group=group, rank=10)

        self.assertEqual(str(meta), "Staff (rank 10)")

    def test_group_meta_ordering(self):
        """GroupMeta should be ordered by rank, then group name."""
        group1 = Group.objects.create(name="Zulu")
        group2 = Group.objects.create(name="Alpha")
        group3 = Group.objects.create(name="Beta")

        GroupMeta.objects.create(group=group1, rank=10)
        GroupMeta.objects.create(group=group2, rank=5)
        GroupMeta.objects.create(group=group3, rank=5)

        metas = list(GroupMeta.objects.all())
        # Rank 5 comes first, then alphabetically Alpha, Beta
        self.assertEqual(metas[0].group.name, "Alpha")
        self.assertEqual(metas[0].rank, 5)
        self.assertEqual(metas[1].group.name, "Beta")
        self.assertEqual(metas[1].rank, 5)
        self.assertEqual(metas[2].group.name, "Zulu")
        self.assertEqual(metas[2].rank, 10)

    def test_group_meta_one_to_one_relationship(self):
        """Each group can only have one GroupMeta."""
        group = Group.objects.create(name="Staff")
        GroupMeta.objects.create(group=group, rank=5)

        with self.assertRaises(IntegrityError):
            GroupMeta.objects.create(group=group, rank=10)

    def test_group_meta_related_name(self):
        """Test related_name 'meta' works."""
        group = Group.objects.create(name="Managers")
        meta = GroupMeta.objects.create(group=group, rank=3)

        self.assertEqual(group.meta, meta)
