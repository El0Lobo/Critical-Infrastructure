import os

from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from app.comms.models import Attachment, Message, MessageThread, ReadReceipt, UserThreadState
from app.comms.services.audience import visible_threads_qs


@login_required
def detail(request, thread_id: int):
    base_qs = visible_threads_qs(request.user, MessageThread.objects.all())
    if getattr(request.user, "is_superuser", False) and not getattr(
        request, "impersonating", False
    ):
        base_qs = base_qs.filter(
            Q(audiences__user=request.user) | Q(messages__sender_user=request.user)
        ).distinct()
    thread = get_object_or_404(base_qs.prefetch_related("messages__attachments"), pk=thread_id)

    # Mark read
    for m in thread.messages.all():
        ReadReceipt.objects.get_or_create(
            message=m, user=request.user, defaults={"read_at": timezone.now()}
        )

    return render(request, "comms/thread_detail.html", {"thread": thread})


@login_required
def archive(request, thread_id: int):
    if request.method != "POST":
        return HttpResponseForbidden("POST only")
    base_qs = visible_threads_qs(request.user, MessageThread.objects.all())
    if getattr(request.user, "is_superuser", False) and not getattr(
        request, "impersonating", False
    ):
        base_qs = base_qs.filter(
            Q(audiences__user=request.user) | Q(messages__sender_user=request.user)
        ).distinct()
    thread = get_object_or_404(base_qs, pk=thread_id)
    uts, _ = UserThreadState.objects.get_or_create(thread=thread, user=request.user)
    uts.archived = True
    uts.save(update_fields=["archived"])
    return redirect("comms:inbox")


@login_required
def unarchive(request, thread_id: int):
    if request.method != "POST":
        return HttpResponseForbidden("POST only")
    base_qs = visible_threads_qs(request.user, MessageThread.objects.all())
    if getattr(request.user, "is_superuser", False) and not getattr(
        request, "impersonating", False
    ):
        base_qs = base_qs.filter(
            Q(audiences__user=request.user) | Q(messages__sender_user=request.user)
        ).distinct()
    thread = get_object_or_404(base_qs, pk=thread_id)
    uts, _ = UserThreadState.objects.get_or_create(thread=thread, user=request.user)
    uts.archived = False
    uts.save(update_fields=["archived"])
    return redirect("comms:inbox")


@login_required
def labels(request, thread_id: int):
    # Placeholder: labels UI not shipped in V1 MVP
    return redirect("comms:thread_detail", thread_id=thread_id)


@login_required
def reply_internal(request, thread_id: int):
    """Append an internal reply to a thread the user can see."""
    if request.method != "POST":
        return HttpResponseForbidden("POST only")

    base_qs = visible_threads_qs(request.user, MessageThread.objects.all())
    if getattr(request.user, "is_superuser", False) and not getattr(
        request, "impersonating", False
    ):
        base_qs = base_qs.filter(
            Q(audiences__user=request.user) | Q(messages__sender_user=request.user)
        ).distinct()

    thread = get_object_or_404(base_qs, pk=thread_id, type=MessageThread.TYPE_INTERNAL)

    body = (request.POST.get("body") or "").strip()
    if not body:
        return redirect("comms:inbox")

    msg = Message.objects.create(
        thread=thread,
        direction=Message.DIR_INTERNAL,
        sender_user=request.user,
        sent_at=timezone.now(),
        body_text=body,
        body_html_sanitized="",
    )

    # attachments
    for f in request.FILES.getlist("attachments"):
        try:
            path = os.path.join("comms", "attachments", str(msg.id), f.name)
            saved = default_storage.save(path, f)
            Attachment.objects.create(
                message=msg,
                filename=f.name,
                mime_type=getattr(f, "content_type", ""),
                size_bytes=getattr(f, "size", None),
                storage_path=saved,
            )
        except Exception:
            pass

    return redirect("comms:inbox")


@login_required
def modal(request, thread_id: int):
    base_qs = visible_threads_qs(request.user, MessageThread.objects.all())
    thread = get_object_or_404(base_qs.prefetch_related("messages__attachments"), pk=thread_id)
    # Mark read when opening in modal
    for m in thread.messages.all():
        ReadReceipt.objects.get_or_create(
            message=m, user=request.user, defaults={"read_at": timezone.now()}
        )
    return render(request, "comms/partials/thread_modal.html", {"thread": thread})
