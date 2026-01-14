import contextlib
import os

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.shortcuts import redirect, render
from django.utils import timezone

from app.comms.forms import InternalComposeForm
from app.comms.models import Attachment, Message, MessageThread
from app.comms.services.audience import visible_threads_qs
from app.comms.services.send_internal import post_internal


def _has_cog(request, key: str) -> bool:
    """Template layer uses allow_for; here we trust server-side always allow superusers."""
    u = request.user
    return getattr(u, "is_superuser", False)  # TODO: integrate with your cog system server-side


@login_required
def compose_internal(request):
    # Allow any authenticated user to compose internal messages (MVP)

    if request.method == "POST":
        form = InternalComposeForm(request.POST)
        if form.is_valid():
            thread = post_internal(
                author=request.user,
                subject=form.cleaned_data.get("subject", ""),
                body_text=form.cleaned_data["body"],
                targets={
                    "users": list(form.cleaned_data.get("users", []).values_list("id", flat=True)),
                    "groups": list(
                        form.cleaned_data.get("groups", []).values_list("id", flat=True)
                    ),
                    "badges": (
                        list(form.cleaned_data.get("badges", []).values_list("id", flat=True))
                        if form.cleaned_data.get("badges") is not None
                        else []
                    ),
                },
            )
            messages.success(request, "Internal message sent.")
            return redirect("comms:thread_detail", thread_id=thread.id)
    else:
        form = InternalComposeForm()

    return render(request, "comms/compose_internal.html", {"form": form})


@login_required
def drafts_list(request):
    # Placeholder: future V1 drafts UI; for now redirect to compose
    return redirect("comms:compose_internal")


@login_required
def compose_internal_modal(request):
    """Lightweight handler for the inbox modal: create draft or send."""
    # Allow any authenticated user to use the modal (MVP)

    if request.method != "POST":
        return redirect("comms:inbox")

    # action = request.POST.get("action", "send")  # Currently unused, kept for future reference
    subject = (request.POST.get("subject") or "").strip()
    body = (request.POST.get("body") or "").strip()
    to_usernames = (request.POST.get("to_usernames") or "").strip()
    thread_id = (request.POST.get("thread_id") or "").strip()
    # internal drafts removed; ignore draft_id if present

    # Dropdown selections
    sel_user_ids = request.POST.getlist("to_user_ids") or []
    sel_group_ids = request.POST.getlist("to_group_ids") or []

    # Resolve recipients (usernames, comma-separated)
    User = get_user_model()
    user_ids = []
    if to_usernames:
        names = [s.strip() for s in to_usernames.split(",") if s.strip()]
        if names:
            user_ids = list(User.objects.filter(username__in=names).values_list("id", flat=True))

    # Merge with selected user ids
    if sel_user_ids:
        with contextlib.suppress(ValueError):
            user_ids = list(set(user_ids) | {int(x) for x in sel_user_ids})
    # Expand selected groups into user ids
    if sel_group_ids:
        try:
            gids = [int(x) for x in sel_group_ids]
            group_user_ids = list(
                User.objects.filter(groups__id__in=gids).values_list("id", flat=True).distinct()
            )
            user_ids = list(set(user_ids) | set(group_user_ids))
        except ValueError:
            pass

    # no internal draft path anymore

    # If replying into an existing internal thread, append message (ignore recipients)
    if thread_id:
        try:
            tid = int(thread_id)
        except ValueError:
            tid = None
        if tid:
            base_qs = visible_threads_qs(request.user, MessageThread.objects.all())
            try:
                thread = base_qs.get(pk=tid, type=MessageThread.TYPE_INTERNAL)
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
                return redirect("comms:thread_detail", thread_id=thread.id)
            except MessageThread.DoesNotExist:
                pass

    # Otherwise: start a new internal thread with resolved recipients
    if not user_ids:
        messages.error(request, "Select at least one recipient (user or group).")
        return redirect("comms:inbox")
    thread = post_internal(
        author=request.user,
        subject=subject,
        body_text=body,
        targets={
            "users": user_ids,
            "groups": [],
            "badges": [],
        },
    )
    # add attachments to first (author) message of new thread
    try:
        msg = thread.messages.order_by("id").last()
        if msg:
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
    except Exception:
        pass
    return redirect("comms:thread_detail", thread_id=thread.id)
