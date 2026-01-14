# views inbox.py

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import BooleanField, Case, Exists, OuterRef, Q, Subquery, Value, When
from django.shortcuts import render

from .models import Draft, Message, MessageThread, ReadReceipt, UserThreadState
from .services.audience import visible_threads_qs


def _with_read_annotations(qs, user):
    """Annotate each thread with is_read_local (for me) and a basic is_ack_by_others."""
    unread_from_others_exists = Exists(
        Message.objects.filter(thread=OuterRef("pk"))
        .exclude(sender_user=user)
        .exclude(read_receipts__user=user)
    )

    last_outgoing_id = Subquery(
        Message.objects.filter(thread=OuterRef("pk"), sender_user=user)
        .order_by("-id")
        .values("id")[:1]
    )

    last_outgoing_read_by_others = Exists(
        ReadReceipt.objects.filter(message_id=last_outgoing_id).exclude(user=user)
    )

    return qs.annotate(
        _unread_exists=unread_from_others_exists,
        is_read_local=Case(
            When(_unread_exists=True, then=Value(False)),
            default=Value(True),
            output_field=BooleanField(),
        ),
        is_ack_by_others=last_outgoing_read_by_others,
    ).distinct()


def _attach_display_fields(qs, me):
    """
    Attach:
      - partner_name
      - last_unread_count (legacy)
      - last_out_read_by_names: list[str] of recipients who read my last outgoing
      - is_ack_by_others (override from precise names)
    """
    items = list(qs)
    me_id = getattr(me, "id", None)

    for t in items:
        msgs = list(t.messages.all())  # already prefetched
        last = msgs[-1] if msgs else None

        # partner_name: prefer last sender (not me), else first audience (not me)
        name = None
        if last and last.sender_user_id and last.sender_user_id != me_id:
            name = getattr(getattr(last, "sender_user", None), "username", None)
        if not name and last and getattr(last, "sender_display", None):
            name = last.sender_display
        if not name:
            try:
                for a in t.audiences.all():
                    if getattr(a, "user_id", None) and a.user_id != me_id:
                        name = a.user.username
                        break
            except Exception:
                pass
        t.partner_name = name or "Conversation"

        # legacy: unread based on latest message from others
        last_unread = 0
        if last and last.sender_user_id != me_id:
            try:
                seen = last.read_receipts.filter(user_id=me_id).exists()
                last_unread = 0 if seen else 1
            except Exception:
                last_unread = 1
        t.last_unread_count = last_unread

        # ---- NEW: names who read my last outgoing message ----
        # find my last outgoing
        last_out = None
        for m in reversed(msgs):
            if m.sender_user_id == me_id:
                last_out = m
                break

        read_names = []
        if last_out:
            # recipients (others in the audience)
            recipients = {
                getattr(a.user, "id", None): getattr(a.user, "username", "")
                for a in t.audiences.all()
                if getattr(a, "user_id", None) and a.user_id != me_id
            }
            # receipts on last outgoing (exclude me) that match participants
            for rr in last_out.read_receipts.all():
                if rr.user_id != me_id and rr.user_id in recipients:
                    n = recipients[rr.user_id] or getattr(rr.user, "username", "")
                    if n:
                        read_names.append(n)

        # de-dupe + stable sort (by name)
        read_names = sorted(set(read_names), key=str.lower)

        t.last_out_read_by_names = read_names
        # Prefer precise names to decide ack flag
        t.is_ack_by_others = bool(read_names)

        # safety fallbacks
        if not hasattr(t, "is_read_local"):
            t.is_read_local = last_unread == 0

    return items


@login_required
def inbox(request):
    me = request.user

    threads = visible_threads_qs(me, MessageThread.objects.all()).distinct()
    if getattr(me, "is_superuser", False) and not getattr(request, "impersonating", False):
        threads = threads.filter(Q(audiences__user=me) | Q(messages__sender_user=me)).distinct()

    archived_ids = list(
        UserThreadState.objects.filter(user=me, archived=True).values_list("thread_id", flat=True)
    )

    # NOTE the __user on prefetch so we can read rr.user.username without extra queries
    base_prefetch = (
        "audiences__user",
        "messages__sender_user",
        "messages__read_receipts__user",
    )

    live_internal = (
        threads.exclude(id__in=archived_ids)
        .filter(type=MessageThread.TYPE_INTERNAL)
        .prefetch_related(*base_prefetch)
    )
    live_email = (
        threads.exclude(id__in=archived_ids)
        .filter(type=MessageThread.TYPE_EMAIL)
        .prefetch_related(*base_prefetch)
    )

    arch_internal = threads.filter(
        id__in=archived_ids, type=MessageThread.TYPE_INTERNAL
    ).prefetch_related(*base_prefetch)
    arch_email = threads.filter(
        id__in=archived_ids, type=MessageThread.TYPE_EMAIL
    ).prefetch_related(*base_prefetch)

    # annotate basic booleans
    live_internal = _with_read_annotations(live_internal, me).order_by("-last_activity_at")
    live_email = _with_read_annotations(live_email, me).order_by("-last_activity_at")
    arch_internal = _with_read_annotations(arch_internal, me).order_by("-last_activity_at")
    arch_email = _with_read_annotations(arch_email, me).order_by("-last_activity_at")

    # attach display fields incl. last_out_read_by_names
    internal_threads = _attach_display_fields(live_internal, me)
    email_threads = _attach_display_fields(live_email, me)
    archived_internal_threads = _attach_display_fields(arch_internal, me)
    archived_email_threads = _attach_display_fields(arch_email, me)

    email_drafts = Draft.objects.filter(
        author=me, account__isnull=False, status=Draft.STATUS_EDITING
    )

    return render(
        request,
        "comms/inbox.html",
        {
            "internal_threads": internal_threads,
            "email_threads": email_threads,
            "archived_internal_threads": archived_internal_threads,
            "archived_email_threads": archived_email_threads,
            "email_drafts": email_drafts,
            "accounts": [],
            "users_all": get_user_model().objects.all().only("id", "username").order_by("username"),
            "groups_all": Group.objects.all().only("id", "name").order_by("name"),
        },
    )
