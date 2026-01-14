from django import template
from django.db.models import Exists, OuterRef, Q

register = template.Library()


@register.simple_tag(takes_context=True)
def has_unread_comms(context):
    """
    True if the current user has any visible, non-archived thread with a message
    from others that they haven't read. Mirrors inbox logic, but imports are done
    lazily so a bad import won't prevent template load.
    """
    request = context.get("request")
    u = getattr(request, "user", None)
    if not getattr(u, "is_authenticated", False):
        return False

    # Lazy imports so tag still registers even if comms internals move.
    try:
        from app.comms.models import Message, MessageThread, UserThreadState
    except Exception:
        return False

    # Try to use the same visibility helper as the inbox view; if missing, fall back.
    try:
        from app.comms.services.audience import visible_threads_qs

        threads = visible_threads_qs(u, MessageThread.objects.all()).distinct()
    except Exception:
        # Fallback visibility: user audience or messages sent by the user
        threads = MessageThread.objects.filter(
            Q(audiences__user=u) | Q(messages__sender_user=u)
        ).distinct()

    # Superuser special-case (skip when impersonating)
    if getattr(u, "is_superuser", False) and not getattr(request, "impersonating", False):
        threads = threads.filter(Q(audiences__user=u) | Q(messages__sender_user=u)).distinct()

    # Exclude archived-for-me
    threads = threads.annotate(
        _archived_for_me=Exists(
            UserThreadState.objects.filter(thread=OuterRef("pk"), user=u, archived=True)
        )
    ).filter(_archived_for_me=False)

    # Unread = any message from others without my receipt
    unread_from_others = Exists(
        Message.objects.filter(thread=OuterRef("pk"))
        .exclude(sender_user=u)
        .exclude(read_receipts__user=u)
    )

    return threads.annotate(_unread=unread_from_others).filter(_unread=True).exists()
