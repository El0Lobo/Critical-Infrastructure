from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from app.comms.models import Draft, MailAccount, MessageThread


@login_required
def compose_email_modal(request):
    """Minimal handler for the inbox compose email modal.

    For now, this saves a Draft (using the first active MailAccount if available)
    and redirects back. Sending is not implemented yet and will store a draft.
    """
    if request.method != "POST":
        return redirect("comms:inbox")

    action = request.POST.get("action", "draft")
    subject = (request.POST.get("subject") or "").strip()
    body = (request.POST.get("body") or "").strip()

    account = MailAccount.objects.filter(is_active=True).first()

    Draft.objects.create(
        author=request.user,
        account=account,
        subject=subject,
        body_text=body,
        status=Draft.STATUS_EDITING,
    )

    if action == "send":
        messages.warning(request, "Email sending not implemented yet; saved as draft.")
    else:
        messages.success(request, "Draft saved.")

    return redirect("comms:inbox")


@login_required
def reply_email_modal(request, thread_id: int):
    """Minimal handler to save a reply draft for an email thread."""
    if request.method != "POST":
        return redirect("comms:thread_detail", thread_id=thread_id)

    subject = (request.POST.get("subject") or "").strip()
    body = (request.POST.get("body") or "").strip()

    thread = get_object_or_404(MessageThread, pk=thread_id, type=MessageThread.TYPE_EMAIL)

    Draft.objects.create(
        author=request.user,
        account=thread.account,
        thread=thread,
        subject=subject,
        body_text=body,
        status=Draft.STATUS_EDITING,
    )

    messages.success(request, "Reply draft saved.")
    return redirect("comms:thread_detail", thread_id=thread_id)
