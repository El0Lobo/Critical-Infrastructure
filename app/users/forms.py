# app/users/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import Group

from app.setup.models import SiteSettings

from .models import BadgeDefinition, UserProfile  # GroupMeta for hierarchy

User = get_user_model()


# ---------------------------
# Helpers
# ---------------------------
def groups_qs():
    """Base queryset for groups (alphabetical for display)."""
    return Group.objects.all().order_by("name")


def top_group_for(groups_iterable):
    """Return the highest-priority group (lowest GroupMeta.rank) from an iterable of Groups."""
    best = None
    best_rank = 10_000
    for g in groups_iterable:
        rank = getattr(getattr(g, "meta", None), "rank", 1000)
        if rank < best_rank:
            best, best_rank = g, rank
    return best


# ---------------------------
# Group hierarchy admin form (for the /groups/hierarchy/ page)
# ---------------------------
class GroupRankForm(forms.Form):
    group_id = forms.IntegerField(widget=forms.HiddenInput)
    name = forms.CharField(disabled=True, required=False, label="Group")
    rank = forms.IntegerField(min_value=0, label="Rank (lower = higher)")

    @classmethod
    def from_group(cls, group):
        meta = getattr(group, "meta", None)
        current_rank = getattr(meta, "rank", 1000)
        return cls(initial={"group_id": group.id, "name": group.name, "rank": current_rank})


# =====================================
# Create User (checkbox groups)
# =====================================
class UserCreateForm(forms.Form):
    # Account
    username = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    temp_password = forms.CharField(
        widget=forms.PasswordInput, help_text="You can set a temporary password."
    )

    # Groups (multi) + optional new group
    groups = forms.ModelMultipleChoiceField(
        queryset=groups_qs(), required=False, widget=forms.CheckboxSelectMultiple, label="Groups"
    )
    new_group_name = forms.CharField(
        required=False, help_text="Create and add a new group (optional)."
    )

    # Role/identity/contact
    role_title = forms.CharField(required=False)
    legal_name = forms.CharField(required=False)
    chosen_name = forms.CharField(required=False)
    pronouns = forms.CharField(required=False)
    birth_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    phone = forms.CharField(required=False)
    address = forms.CharField(required=False)
    duties = forms.CharField(required=False, widget=forms.Textarea)

    # Badges
    badges = forms.ModelMultipleChoiceField(
        queryset=BadgeDefinition.objects.all(), required=False, widget=forms.CheckboxSelectMultiple
    )

    def save(self):
        data = self.cleaned_data

        user = User.objects.create_user(
            username=data["username"],
            email="",
            password=data["temp_password"],
            is_active=True,
        )

        # collect groups (including optional new one)
        chosen_groups = list(data.get("groups") or [])
        new_name = (data.get("new_group_name") or "").strip()
        if new_name:
            g, _ = Group.objects.get_or_create(name=new_name)
            chosen_groups.append(g)

        # set memberships
        if chosen_groups:
            user.groups.set(chosen_groups)
        else:
            user.groups.clear()

        # profile + fields
        profile, _ = UserProfile.objects.get_or_create(user=user)
        for f in [
            "legal_name",
            "chosen_name",
            "pronouns",
            "birth_date",
            "phone",
            "address",
            "duties",
            "role_title",
            "email",
        ]:
            setattr(profile, f, data.get(f))

        # compute primary_group = highest-ranked of chosen
        if chosen_groups:
            groups_full = Group.objects.filter(
                id__in=[g.id for g in chosen_groups]
            ).prefetch_related("meta")
            profile.primary_group = top_group_for(groups_full)
        else:
            profile.primary_group = None

        profile.force_password_change = True
        profile.save()

        # badges
        if data.get("badges"):
            profile.badges.set(data["badges"])
        else:
            profile.badges.clear()

        return user


# =====================================
# Edit Profile (checkbox groups)
# =====================================
class ProfileForm(forms.ModelForm):
    birth_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

    # Groups (multi) + optional new group
    groups = forms.ModelMultipleChoiceField(
        queryset=groups_qs(), required=False, widget=forms.CheckboxSelectMultiple, label="Groups"
    )
    new_group_name = forms.CharField(
        required=False, label="New Group", help_text="Create and add a new group (optional)."
    )

    class Meta:
        model = UserProfile
        fields = [
            "legal_name",
            "chosen_name",
            "pronouns",
            "birth_date",
            "email",
            "phone",
            "address",
            "role_title",
            "duties",
            "badges",
        ]
        widgets = {
            "duties": forms.Textarea(attrs={"rows": 4}),
            "badges": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # order badges nicely
        if "badges" in self.fields:
            self.fields["badges"].queryset = BadgeDefinition.objects.order_by("name")

        # preselect groups from the user's memberships
        if not self.is_bound and self.instance and getattr(self.instance, "user_id", None):
            self.fields["groups"].initial = self.instance.user.groups.all()

    def save(self, commit=True):
        profile = super().save(commit=False)

        # collect groups (including optional new one)
        chosen_groups = list(self.cleaned_data.get("groups") or [])
        new_name = (self.cleaned_data.get("new_group_name") or "").strip()
        if new_name:
            g, _ = Group.objects.get_or_create(name=new_name)
            chosen_groups.append(g)

        # sync user.groups and compute primary_group
        if hasattr(profile, "user") and profile.user_id:
            user = profile.user

            if chosen_groups:
                user.groups.set(chosen_groups)
                groups_full = Group.objects.filter(
                    id__in=[g.id for g in chosen_groups]
                ).prefetch_related("meta")
                profile.primary_group = top_group_for(groups_full)
            else:
                user.groups.clear()
                profile.primary_group = None

            user.save()

        if commit:
            profile.save()
            self.save_m2m()

        return profile


# =====================================
# Badges CRUD
# =====================================
class BadgeDefinitionForm(forms.ModelForm):
    class Meta:
        model = BadgeDefinition
        fields = ["name", "emoji", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class MembershipSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ["membership_enabled", "membership_hint"]
        widgets = {"membership_hint": forms.Textarea(attrs={"rows": 3})}


# =====================================
# First login password change
# =====================================
class PasswordChangeFirstLoginForm(SetPasswordForm):
    pass
