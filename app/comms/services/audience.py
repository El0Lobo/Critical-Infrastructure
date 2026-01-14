from django.db.models import Q

from app.comms.models import MessageThread


def user_membership_ids(user):
    """Return (badge_ids, group_ids) for the user; tolerate missing badges relation."""
    badge_ids = set()
    try:
        profile = user.profile
        badge_ids = set(profile.badges.values_list("id", flat=True))
    except Exception:
        pass
    group_ids = set(user.groups.values_list("id", flat=True))
    return badge_ids, group_ids


def visible_threads_qs(user, base_qs=None):
    """Server-side audience filtering: thread audiences ∩ user memberships."""
    if base_qs is None:
        base_qs = MessageThread.objects.all()

    badge_ids, group_ids = user_membership_ids(user)
    cond = Q(audiences__user=user)
    if badge_ids:
        cond |= Q(audiences__badge_id__in=badge_ids)
    if group_ids:
        cond |= Q(audiences__group_id__in=group_ids)

    qs = base_qs.filter(cond).distinct()
    return qs
