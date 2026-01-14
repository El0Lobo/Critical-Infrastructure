from .site_config import get_config


def sitecfg(request):
    return {"sitecfg": get_config()}


def inbox_status(request):
    """
    Global unread flag for the nav. Mirrors inbox view logic:
    - same visibility (visible_threads_qs)
    - same superuser/impersonation special-case
    - ignore archived-for-me
    - unread = any message from others without my read receipt
    """
    u = getattr(request, "user", None)
    has_unread = False
    if getattr(u, "is_authenticated", False):
        try:
            from django.db.models import Exists, OuterRef, Q

            from app.comms.models import Message, MessageThread, UserThreadState

            # visibility
            try:
                from app.comms.services.audience import visible_threads_qs

                threads = visible_threads_qs(u, MessageThread.objects.all()).distinct()
            except Exception:
                # fallback if helper not available
                threads = MessageThread.objects.filter(
                    Q(audiences__user=u) | Q(messages__sender_user=u)
                ).distinct()

            # superuser special-case (skip when impersonating)
            if getattr(u, "is_superuser", False) and not getattr(request, "impersonating", False):
                threads = threads.filter(
                    Q(audiences__user=u) | Q(messages__sender_user=u)
                ).distinct()

            # exclude archived-for-me
            threads = threads.annotate(
                _archived_for_me=Exists(
                    UserThreadState.objects.filter(thread=OuterRef("pk"), user=u, archived=True)
                )
            ).filter(_archived_for_me=False)

            # unread if any message from others lacks my receipt
            unread_from_others = Exists(
                Message.objects.filter(thread=OuterRef("pk"))
                .exclude(sender_user=u)
                .exclude(read_receipts__user=u)
            )

            has_unread = threads.annotate(_unread=unread_from_others).filter(_unread=True).exists()
        except Exception:
            has_unread = False

    return {"has_unread_messages": has_unread}


def site_languages(request):
    """
    Add enabled languages to template context.
    Uses SiteSettings to determine which languages are enabled.
    """
    from django.conf import settings as django_settings

    from app.setup.models import SiteSettings

    try:
        site_settings = SiteSettings.get_solo()
        enabled_languages = site_settings.get_enabled_languages()
    except Exception:
        # Fallback to all languages if SiteSettings not available
        enabled_languages = list(django_settings.LANGUAGES)

    return {
        "enabled_languages": enabled_languages,
    }
