"""
Unified Comms — data models

This module powers the unified inbox (internal messages + email). It is written to:
- Keep internal messaging working even if no MailAccount exists.
- Enforce audience/visibility on the server side.
- Avoid breaking existing migrations / code paths (“don’t break old stuff”).

Notes:
- CheckConstraint literals are used (e.g., type='email') to avoid class-constant scope issues in Meta.
- unique_together is intentionally kept (even if UniqueConstraint is newer) to avoid churn.
"""

from django.conf import settings
from django.db import models
from django.db.models import (
    CheckConstraint,
    Q,
)  # F is imported for potential future atomic updates
from django.utils import timezone

# Using settings.AUTH_USER_MODEL for portability; keep alias for readability.
User = settings.AUTH_USER_MODEL


# ---------------------------------------------------------------------
# Mail accounts (optional). Internal works without any MailAccount rows.
# ---------------------------------------------------------------------
class MailAccount(models.Model):
    """
    Represents an email identity / transport config.
    Internal threads will have account = NULL.
    """

    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)

    # Display identity (outbound)
    from_name = models.CharField(max_length=120, blank=True, default="")
    from_address = models.EmailField(blank=True, default="")
    signature_html = models.TextField(blank=True, default="")
    signature_text = models.TextField(blank=True, default="")

    # Operational state
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------
# Threads unify internal and email conversations.
# For email threads, account MUST be set. For internal, it MUST be NULL.
# ---------------------------------------------------------------------
class MessageThread(models.Model):
    TYPE_INTERNAL = "internal"
    TYPE_EMAIL = "email"
    TYPE_CHOICES = [
        (TYPE_INTERNAL, "Internal"),
        (TYPE_EMAIL, "Email"),
    ]

    # Thread kind and association to an email account (email-only)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_INTERNAL)
    account = models.ForeignKey(MailAccount, null=True, blank=True, on_delete=models.PROTECT)

    # Presentation and lifecycle
    subject = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now=True)
    has_attachments = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-last_activity_at"]
        constraints = [
            # Enforce that email threads have an account, and internal threads don't.
            CheckConstraint(
                check=Q(type="email", account__isnull=False)
                | Q(type="internal", account__isnull=True),
                name="comms_thread_type_account_consistency",
            ),
        ]

    def __str__(self) -> str:
        return f"[{self.get_type_display()}] {self.subject or f'Thread #{self.pk}'}"


# ---------------------------------------------------------------------
# Messages within a thread: inbound/outbound email or internal posts.
# For internal messages, account MUST be NULL. For email in/out, account allowed.
# ---------------------------------------------------------------------
class Message(models.Model):
    DIR_INBOUND = "inbound"
    DIR_OUTBOUND = "outbound"
    DIR_INTERNAL = "internal"
    DIR_CHOICES = [
        (DIR_INBOUND, "Inbound"),
        (DIR_OUTBOUND, "Outbound"),
        (DIR_INTERNAL, "Internal"),
    ]

    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name="messages")

    # Direction and email account association (internal must remain NULL)
    direction = models.CharField(max_length=10, choices=DIR_CHOICES, default=DIR_INTERNAL)
    account = models.ForeignKey(MailAccount, null=True, blank=True, on_delete=models.PROTECT)

    # Who sent it (for internal/outbound email). For inbound email, this may be empty
    # and represented via headers/sender_display.
    sender_user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="sent_messages"
    )
    sender_display = models.CharField(
        max_length=200, blank=True, default=""
    )  # For email "From:" display names

    # Timing
    received_at = models.DateTimeField(null=True, blank=True)  # inbound email
    sent_at = models.DateTimeField(null=True, blank=True)  # outbound email/internal
    created_at = models.DateTimeField(auto_now_add=True)  # server insert time

    # Email-specific metadata (for threading / headers)
    message_id = models.CharField(max_length=512, blank=True, default="")  # email-only
    in_reply_to = models.CharField(max_length=512, blank=True, default="")  # email-only
    references = models.TextField(blank=True, default="")  # email-only
    headers = models.JSONField(blank=True, null=True)  # email-only

    # Body: we keep a text version and (sanitized) HTML version
    body_text = models.TextField(blank=True, default="")
    body_html_sanitized = models.TextField(blank=True, default="")

    # Safety / size
    has_trackers = models.BooleanField(default=False)
    size_bytes = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            # Internal messages must not have an account; email in/out are allowed with account.
            CheckConstraint(
                check=(
                    Q(direction="internal", account__isnull=True)
                    | Q(direction__in=["inbound", "outbound"])
                ),
                name="comms_message_direction_account_consistency",
            ),
        ]

    def __str__(self) -> str:
        # Helpful for admin/debug
        kind = self.get_direction_display()
        subj = self.thread.subject or f"Thread #{self.thread_id}"
        return f"{kind} · {subj} · {self.created_at:%Y-%m-%d %H:%M}"


# ---------------------------------------------------------------------
# Attachments stored independently (scanning, inlining, etc.).
# ---------------------------------------------------------------------
class Attachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="attachments")
    filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100, blank=True, default="")
    size_bytes = models.BigIntegerField(null=True, blank=True)

    # Path/key into your storage (filesystem, S3, etc.)
    storage_path = models.CharField(max_length=500, blank=True, default="")
    sha256 = models.CharField(max_length=64, blank=True, default="")

    # Email inline attachments (CID)
    is_inline = models.BooleanField(default=False)
    content_id = models.CharField(max_length=255, blank=True, default="")

    # Scan status and any details from AV/anti-malware
    SCAN_PENDING = "pending"
    SCAN_CLEAN = "clean"
    SCAN_BLOCKED = "blocked"
    SCAN_ERROR = "error"
    SCAN_CHOICES = [
        (SCAN_PENDING, "Pending"),
        (SCAN_CLEAN, "Clean"),
        (SCAN_BLOCKED, "Blocked"),
        (SCAN_ERROR, "Error"),
    ]
    scan_status = models.CharField(max_length=16, choices=SCAN_CHOICES, default=SCAN_PENDING)
    scan_detail = models.TextField(blank=True, default="")

    def __str__(self) -> str:
        return self.filename or f"Attachment #{self.pk}"


# ---------------------------------------------------------------------
# Per-user read receipts to track which messages have been viewed.
# ---------------------------------------------------------------------
class ReadReceipt(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="read_receipts")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comms_reads")
    read_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("message", "user")]
        indexes = [models.Index(fields=["user", "-read_at"])]

    def __str__(self) -> str:
        return f"{self.user} read msg {self.message_id} @ {self.read_at:%Y-%m-%d %H:%M}"


# ---------------------------------------------------------------------
# Optional labels (per account). We keep unique_together to avoid churn.
# ---------------------------------------------------------------------
class Label(models.Model):
    account = models.ForeignKey(MailAccount, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    slug = models.SlugField()
    is_system = models.BooleanField(default=False)

    class Meta:
        unique_together = [("account", "slug")]

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------
# Per-user thread state (archive/star/labels).
# ---------------------------------------------------------------------
class UserThreadState(models.Model):
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name="user_states")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="thread_states")

    archived = models.BooleanField(default=False)
    starred = models.BooleanField(default=False)
    last_read_at = models.DateTimeField(null=True, blank=True)

    # Optional labeling
    labels = models.ManyToManyField(Label, blank=True)

    class Meta:
        unique_together = [("thread", "user")]
        indexes = [
            models.Index(fields=["user", "archived", "-last_read_at"]),
            models.Index(fields=["user", "starred", "-last_read_at"]),
        ]

    def __str__(self) -> str:
        flags = []
        if self.archived:
            flags.append("archived")
        if self.starred:
            flags.append("starred")
        flags = ", ".join(flags) or "—"
        return f"{self.user} / {self.thread_id} ({flags})"


# ---------------------------------------------------------------------
# Thread-level audience entries (exactly one of user/group/badge).
# This is the core for visibility: a thread is visible if intersecting
# the viewer's badges/groups/user id.
# ---------------------------------------------------------------------
class AudienceLink(models.Model):
    """Visibility audiences at thread level (one row per target)."""

    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name="audiences")
    badge = models.ForeignKey(
        "users.BadgeDefinition", null=True, blank=True, on_delete=models.CASCADE
    )
    group = models.ForeignKey("auth.Group", null=True, blank=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)

    # Provenance of how this audience member was added (manual/alias/tag/etc.)
    source = models.CharField(max_length=20, default="manual")

    class Meta:
        constraints = [
            # Exactly one of badge/group/user must be non-null.
            CheckConstraint(
                check=(
                    Q(badge__isnull=False, group__isnull=True, user__isnull=True)
                    | Q(badge__isnull=True, group__isnull=False, user__isnull=True)
                    | Q(badge__isnull=True, group__isnull=True, user__isnull=False)
                ),
                name="comms_audience_exactly_one_target",
            ),
            # Avoid duplicate audience entries for the same member.
            models.UniqueConstraint(
                fields=["thread", "badge", "group", "user"],
                name="comms_audience_unique_member",
            ),
        ]

    def __str__(self) -> str:
        target = self.user or self.group or self.badge
        return f"Audience({target}) for thread {self.thread_id}"


# ---------------------------------------------------------------------
# Internal compose intent (who was targeted). Mirrors AudienceLink but
# kept distinct to preserve semantics in analytics/audit.
# ---------------------------------------------------------------------
class InternalTarget(models.Model):
    """Targets for internal compose (redundant with AudienceLink but explicit for intent)."""

    thread = models.ForeignKey(
        MessageThread, on_delete=models.CASCADE, related_name="internal_targets"
    )
    badge = models.ForeignKey(
        "users.BadgeDefinition", null=True, blank=True, on_delete=models.CASCADE
    )
    group = models.ForeignKey("auth.Group", null=True, blank=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            # Exactly one of badge/group/user must be non-null.
            CheckConstraint(
                check=(
                    Q(badge__isnull=False, group__isnull=True, user__isnull=True)
                    | Q(badge__isnull=True, group__isnull=False, user__isnull=True)
                    | Q(badge__isnull=True, group__isnull=True, user__isnull=False)
                ),
                name="comms_internal_target_exactly_one_target",
            ),
            models.UniqueConstraint(
                fields=["thread", "badge", "group", "user"],
                name="comms_internal_target_unique_member",
            ),
        ]

    def __str__(self) -> str:
        target = self.user or self.group or self.badge
        return f"InternalTarget({target}) for thread {self.thread_id}"


# ---------------------------------------------------------------------
# Drafts (internal & email). Email drafts carry addressing in JSON.
# ---------------------------------------------------------------------
class Draft(models.Model):
    STATUS_EDITING = "editing"
    STATUS_SCHEDULED = "scheduled"
    STATUS_SENT = "sent"
    STATUS_DISCARDED = "discarded"
    STATUS_CHOICES = [
        (STATUS_EDITING, "Editing"),
        (STATUS_SCHEDULED, "Scheduled"),
        (STATUS_SENT, "Sent"),
        (STATUS_DISCARDED, "Discarded"),
    ]

    # For email drafts this should be set; internal drafts can keep it NULL.
    account = models.ForeignKey(MailAccount, null=True, blank=True, on_delete=models.PROTECT)

    # Who is editing/owning this draft
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comms_drafts")

    # Optional anchor to a thread (e.g., reply draft). New-composition drafts may be NULL.
    thread = models.ForeignKey(MessageThread, null=True, blank=True, on_delete=models.SET_NULL)

    # Content
    subject = models.CharField(max_length=500, blank=True, default="")
    body_text = models.TextField(blank=True, default="")
    body_html = models.TextField(blank=True, default="")

    # Email addressing (for email drafts only)
    # Store as list of dicts [{"name": "...", "email": "..."}] to preserve display names.
    to_json = models.JSONField(blank=True, null=True, default=list)
    cc_json = models.JSONField(blank=True, null=True, default=list)
    bcc_json = models.JSONField(blank=True, null=True, default=list)

    # Attachment staging metadata (paths, filenames, etc. as needed)
    attachments_meta = models.JSONField(blank=True, null=True, default=list)

    # Lifecycle
    autosaved_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_EDITING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        who = getattr(self, "author", None)
        return f"Draft #{self.pk} by {who}" if who else f"Draft #{self.pk}"
