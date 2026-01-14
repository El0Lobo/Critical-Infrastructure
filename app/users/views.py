# app/users/views.py
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from app.setup.forms import GroupFormSet, TierFormSet
from app.setup.models import SiteSettings

from .forms import (
    BadgeDefinitionForm,
    GroupRankForm,  # for the hierarchy page
    MembershipSettingsForm,
    ProfileForm,
    UserCreateForm,
)
from .models import (
    BadgeDefinition,
    FieldPolicy,
    GroupMeta,  # holds Group.rank (lower = higher)
)

User = get_user_model()
IMPERSONATE_SESSION_KEY = getattr(settings, "IMPERSONATE_SESSION_KEY", "impersonate_user_id")
IMPERSONATOR_SESSION_KEY = getattr(settings, "IMPERSONATOR_SESSION_KEY", "impersonator_user_id")


def staff_or_super(u):
    return u.is_superuser or u.is_staff


# ---------------------------
# Helpers for group ranking
# ---------------------------
def _group_rank(g: Group) -> int:
    meta = getattr(g, "meta", None)
    return getattr(meta, "rank", 1000)


def _top_group_for_user(user):
    """Return the user's highest-priority group (lowest rank), or None."""
    best = None
    best_rank = 10_000
    for g in user.groups.all():
        r = _group_rank(g)
        if r < best_rank:
            best, best_rank = g, r
    return best


# ---------------------------
# Index: show each user once, under their highest group
# ---------------------------
@login_required
def index(request):
    # Preload groups with their meta (for ranks)
    groups_qs = Group.objects.all().prefetch_related("meta")

    # Preload users with profile/badges and groups (with meta)
    users_qs = (
        User.objects.all()
        .select_related("profile")
        .prefetch_related("groups__meta", "profile__badges")
        .order_by("username")
    )

    # Build mapping {group: [users]} and a list for users with no groups
    group_to_users = {g: [] for g in groups_qs}
    no_group_users = []

    for u in users_qs:
        tg = _top_group_for_user(u)
        if tg:
            group_to_users[tg].append(u)
        else:
            no_group_users.append(u)

    # Sort users within each group
    for users in group_to_users.values():
        users.sort(key=lambda x: x.username.lower())
    no_group_users.sort(key=lambda x: x.username.lower())

    # Order groups by rank then name
    groups_ordered = sorted(groups_qs, key=lambda g: (_group_rank(g), g.name.lower()))

    grouped = [(g, group_to_users.get(g, [])) for g in groups_ordered]

    return render(
        request,
        "users/index.html",
        {
            "grouped": grouped,
            "no_group_users": no_group_users,
        },
    )


# ---------------------------
# Create user
# ---------------------------
@login_required
@user_passes_test(staff_or_super)
def create_user(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User {user.username} created.")
            return redirect("users:index")
    else:
        form = UserCreateForm()
    return render(request, "users/form.html", {"form": form, "title": "Create User"})


# ---------------------------
# Profile detail (read-only)
# ---------------------------
@login_required
def profile_detail(request, user_id):
    obj = get_object_or_404(User, id=user_id)
    profile = obj.profile

    def can_show(vis):
        if vis == FieldPolicy.Visibility.PUBLIC:
            return True
        if vis == FieldPolicy.Visibility.AUTHENTICATED:
            return request.user.is_authenticated
        if vis == FieldPolicy.Visibility.STAFF_ONLY:
            return request.user.is_staff or request.user.is_superuser
        if vis == FieldPolicy.Visibility.ADMIN_ONLY:
            return request.user.is_superuser
        return False

    policies = {p.field_name: p.visibility for p in FieldPolicy.objects.all()}
    return render(
        request,
        "users/profile.html",
        {
            "obj": obj,
            "profile": profile,
            "can_show": can_show,
            "policies": policies,
        },
    )


# ---------------------------
# Profile edit
# ---------------------------
@login_required
def profile_edit(request, user_id):
    # Only the owner or staff/superusers can edit
    if (request.user.id != user_id) and not staff_or_super(request.user):
        messages.error(request, "You don't have permission to edit this profile.")
        return redirect("users:index")

    target_user = get_object_or_404(User, id=user_id)
    profile = target_user.profile

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()  # ProfileForm handles syncing groups + primary_group
            messages.success(request, f"Profile for {target_user.username} updated.")
            return redirect("users:index")  # ✅ Redirect to index after saving
    else:
        form = ProfileForm(instance=profile)

    return render(
        request,
        "users/form.html",
        {
            "form": form,
            "title": f"Edit Profile: {target_user.username}",
        },
    )


@login_required
@user_passes_test(staff_or_super)
def membership_settings(request):
    settings_obj = SiteSettings.get_solo()
    if request.method == "POST":
        form = MembershipSettingsForm(request.POST, instance=settings_obj)
        tiers = TierFormSet(request.POST, instance=settings_obj, prefix="tiers")
        form_valid = form.is_valid()
        tiers_valid = tiers.is_valid()
        if form_valid and tiers_valid:
            form.save()
            tiers.save()
            messages.success(request, "Membership settings updated.")
            return redirect("users:membership_settings")
        if not form_valid:
            messages.error(request, "Fix the highlighted membership settings errors.")
        if not tiers_valid:
            messages.error(request, "Check the membership tiers before saving.")
    else:
        form = MembershipSettingsForm(instance=settings_obj)
        tiers = TierFormSet(instance=settings_obj, prefix="tiers")
    return render(
        request,
        "users/membership_settings.html",
        {
            "form": form,
            "tiers": tiers,
        },
    )


@login_required
@user_passes_test(staff_or_super)
def roles_settings(request):
    formset = GroupFormSet(
        request.POST or None,
        queryset=Group.objects.all().order_by("name"),
        prefix="roles",
    )
    if request.method == "POST":
        if formset.is_valid():
            formset.save()
            messages.success(request, "Roles updated.")
            return redirect("users:roles_settings")
        messages.error(request, "Fix the highlighted errors before saving roles.")
    return render(
        request,
        "users/roles_settings.html",
        {
            "roles": formset,
        },
    )


# ---------- Badge CRUD ----------
@login_required
@user_passes_test(staff_or_super)
def badges_list(request):
    badges = BadgeDefinition.objects.all()
    return render(request, "users/badges_list.html", {"badges": badges})


@login_required
@user_passes_test(staff_or_super)
def badges_create(request):
    if request.method == "POST":
        form = BadgeDefinitionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Badge created.")
            return redirect("users:badges_list")
    else:
        form = BadgeDefinitionForm()
    return render(request, "users/badges_form.html", {"form": form, "title": "New Badge"})


@login_required
@user_passes_test(staff_or_super)
def badges_edit(request, pk):
    badge = get_object_or_404(BadgeDefinition, pk=pk)
    if request.method == "POST":
        form = BadgeDefinitionForm(request.POST, instance=badge)
        if form.is_valid():
            form.save()
            messages.success(request, "Badge updated.")
            return redirect("users:badges_list")
    else:
        form = BadgeDefinitionForm(instance=badge)
    return render(
        request, "users/badges_form.html", {"form": form, "title": f"Edit Badge: {badge.name}"}
    )


@login_required
@user_passes_test(staff_or_super)
def badges_delete(request, pk):
    badge = get_object_or_404(BadgeDefinition, pk=pk)
    if request.method == "POST":
        badge.delete()
        messages.success(request, "Badge deleted.")
        return redirect("users:badges_list")
    return render(request, "users/badges_confirm_delete.html", {"badge": badge})


# ---------- Delete user ----------
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def user_delete(request, user_id):
    if request.method != "POST":
        return redirect("users:index")
    u = get_object_or_404(User, id=user_id)
    username = u.username
    u.delete()
    messages.success(request, f"Deleted {username}.")
    return redirect("users:index")


# ---------- Group hierarchy (Option B) ----------
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def group_hierarchy(request):
    groups = Group.objects.all().order_by("name")

    if request.method == "POST":
        valid = True
        for g in groups:
            prefix = f"g{g.id}"
            form = GroupRankForm(request.POST, prefix=prefix)
            if form.is_valid():
                meta, _ = GroupMeta.objects.get_or_create(group=g)
                meta.rank = form.cleaned_data["rank"]
                meta.save()
            else:
                valid = False

        if valid:
            messages.success(request, "Group hierarchy saved.")
            return redirect("users:index")
        else:
            messages.error(request, "Please correct the errors below.")

    # GET (or invalid POST): build forms with current ranks
    forms_list = []
    for g in groups:
        meta, _ = GroupMeta.objects.get_or_create(group=g)
        forms_list.append(
            (
                g,
                GroupRankForm(
                    prefix=f"g{g.id}", initial={"group_id": g.id, "name": g.name, "rank": meta.rank}
                ),
            )
        )

    return render(request, "users/group_hierarchy.html", {"forms_list": forms_list})


def _can_impersonate(user):
    # Your policy here. Options:
    # 1) Superusers:
    if user.is_superuser:
        return True
    # 2) Django perm:
    # 3) Or your cog system (pseudo):
    # from app.users.helpers import user_has_cog
    # if user_has_cog(user, "cms.users.impersonate"):
    #     return True
    return user.has_perm("users.can_impersonate")


class ImpersonateStartView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Start impersonation by setting session keys. Redirects back to 'next' or CMS index.
    """

    def test_func(self):
        return _can_impersonate(self.request.user)

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to impersonate users.")
        return redirect(self.request.META.get("HTTP_REFERER", "/"))

    def get(self, request, user_id):
        if str(request.user.pk) == str(user_id):
            messages.info(request, "You are already yourself. No need to impersonate.")
            return redirect(request.META.get("HTTP_REFERER", "/"))

        target = get_object_or_404(User, pk=user_id, is_active=True)

        # Optional safety: block impersonating superusers unless you’re superuser
        if target.is_superuser and not request.user.is_superuser:
            messages.error(request, "You cannot impersonate a superuser.")
            return redirect(request.META.get("HTTP_REFERER", "/"))

        request.session[IMPERSONATE_SESSION_KEY] = target.pk
        request.session[IMPERSONATOR_SESSION_KEY] = request.user.pk

        messages.success(request, f"Now viewing the CMS as {target.get_username()}.")
        return redirect(request.GET.get("next") or reverse("cms:index"))


class ImpersonateStopView(LoginRequiredMixin, View):
    """
    Stop impersonation by clearing session keys. Redirects back.
    """

    def get(self, request):
        if IMPERSONATE_SESSION_KEY in request.session:
            request.session.pop(IMPERSONATE_SESSION_KEY, None)
            request.session.pop(IMPERSONATOR_SESSION_KEY, None)
            messages.success(request, "Impersonation ended. You are yourself again.")
        else:
            messages.info(request, "You were not impersonating anyone.")
        return redirect(request.META.get("HTTP_REFERER", "/"))
