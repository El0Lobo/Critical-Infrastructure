from datetime import date, datetime

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.utils.translation import gettext_lazy as _

from app.core.encryption import (
    EncryptedCharField,
    EncryptedDateField,
    EncryptedEmailField,
    EncryptedTextField,
)

User = settings.AUTH_USER_MODEL


class BadgeDefinition(models.Model):
    name = models.CharField(max_length=100, unique=True)
    emoji = models.CharField(
        max_length=8, blank=True, help_text=_("Optional short emoji label (e.g. '🍺')")
    )
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{(self.emoji + ' ') if self.emoji else ''}{self.name}"


class FieldPolicy(models.Model):
    class Visibility(models.TextChoices):
        ADMIN_ONLY = "ADMIN_ONLY", _("Admins only")
        STAFF_ONLY = "STAFF_ONLY", _("Staff users")
        AUTHENTICATED = "AUTHENTICATED", _("All logged-in users")
        PUBLIC = "PUBLIC", _("Public/Anyone")

    field_name = models.CharField(
        max_length=100,
        unique=True,  # unique_together on a single field is redundant—use unique=True
        help_text=_("e.g. 'phone', 'address', 'birth_date', 'email', 'role_title'"),
    )
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.AUTHENTICATED,
    )

    class Meta:
        verbose_name_plural = "field policies"

    def __str__(self):
        return f"{self.field_name} → {self.visibility}"


class GroupMeta(models.Model):
    """
    Stores precedence for each auth Group. Lower rank = higher priority (1 is top).
    """

    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name="meta")
    rank = models.PositiveIntegerField(default=1000, help_text=_("Lower = higher priority"))

    class Meta:
        ordering = ["rank", "group__name"]

    def __str__(self):
        return f"{self.group.name} (rank {self.rank})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # Identity
    legal_name = EncryptedCharField(max_length=200, blank=True)
    chosen_name = EncryptedCharField(max_length=200, blank=True)
    pronouns = EncryptedCharField(
        max_length=64, blank=True, help_text=_("e.g. she/her, he/him, they/them")
    )
    birth_date = EncryptedDateField(null=True, blank=True)  # replaces 'age'

    # Contact
    email = EncryptedEmailField(blank=True)
    phone = EncryptedCharField(max_length=64, blank=True)
    address = EncryptedTextField(blank=True)

    # Role/Duties
    role_title = EncryptedCharField(
        max_length=120, blank=True, help_text=_("Free-text role label, e.g. 'Bar lead'")
    )
    duties = EncryptedTextField(blank=True)
    primary_group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="primary_members",
    )

    # Badges
    badges = models.ManyToManyField(BadgeDefinition, blank=True)

    # Onboarding flags
    force_password_change = models.BooleanField(default=True)
    has_selected_visibility = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]
        permissions = (
            # Attach the custom permission here instead of using a dummy model.
            ("can_impersonate", "Can impersonate other users"),
        )

    def __str__(self):
        # Prefer chosen_name, then legal_name, else user's username
        if self.chosen_name:
            return self.chosen_name
        if self.legal_name:
            return self.legal_name
        # self.user is a User instance; get a stable string
        try:
            return self.user.get_username()
        except Exception:
            return str(self.user_id)


@property
def age_years(self):
    """Compute age from birth_date; returns int or None if unknown/invalid."""
    bd = getattr(self, "birth_date", None)
    if not bd:
        return None

    # Normalize to a date
    if isinstance(bd, str):
        s = bd.strip()
        try:
            # Fast path for ISO format
            bd = date.fromisoformat(s)
        except ValueError:
            # Fallback explicit parse (same format; keeps Python 3.10 happy)
            try:
                bd = datetime.strptime(s, "%Y-%m-%d").date()
            except ValueError:
                return None
    elif isinstance(bd, datetime):
        bd = bd.date()
    elif not isinstance(bd, date):
        return None

    # Use Django's localdate when available (falls back to date.today)
    try:
        from django.utils import timezone

        today = timezone.localdate()
    except Exception:
        today = date.today()

    years = today.year - bd.year
    if (today.month, today.day) < (bd.month, bd.day):
        years -= 1
    return years
