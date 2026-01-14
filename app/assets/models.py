# app/assets/models.py
import mimetypes
import os

from django.contrib.auth.models import Group
from django.db import models
from django.utils.text import slugify

# Ensure common font types are recognized
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("font/woff", ".woff")
mimetypes.add_type("font/ttf", ".ttf")
mimetypes.add_type("font/otf", ".otf")
mimetypes.add_type("application/font-woff", ".woff")  # legacy label some tools use


# -----------------------------
# Choices
# -----------------------------
VISIBILITY_MODE_CHOICES = [
    ("public", "Public"),
    ("internal", "Internal (staff)"),
    ("groups", "Groups"),
]

ASSET_VISIBILITY_CHOICES = [
    ("inherit", "Inherit from collection"),
    ("public", "Public"),
    ("internal", "Internal"),
]

ASSET_KIND_CHOICES = [
    ("image", "Image"),
    ("video", "Video"),
    ("audio", "Audio"),
    ("pdf", "PDF"),
    ("doc", "Document"),
    ("archive", "Archive"),
    ("link", "Link"),
    ("note", "Text/Note"),
    ("font", "Font"),  # <-- added for font previews
    ("other", "Other"),
]


# -----------------------------
# Helpers
# -----------------------------
def infer_kind(filename: str, mime: str | None, has_text: bool = False) -> str:
    if has_text:
        return "note"
    if mime:
        if mime.startswith("image/"):
            return "image"
        if mime.startswith("video/"):
            return "video"
        if mime.startswith("audio/"):
            return "audio"
        if mime in ("font/woff2", "font/woff", "font/ttf", "font/otf", "application/font-woff"):
            return "font"
        if mime == "application/pdf":
            return "pdf"
        if mime in (
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "text/plain",
            "application/rtf",
            "application/vnd.oasis.opendocument.text",
        ):
            return "doc"
        if mime in (
            "application/zip",
            "application/x-zip-compressed",
            "application/x-tar",
            "application/gzip",
            "application/x-7z-compressed",
        ):
            return "archive"
    ext = os.path.splitext(filename or "")[1].lower()
    if ext in (".woff2", ".woff", ".ttf", ".otf"):
        return "font"
    if ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".svg"):
        return "image"
    if ext in (".mp4", ".webm", ".mov", ".m4v", ".ogv"):
        return "video"
    if ext in (".mp3", ".wav", ".ogg", ".m4a", ".flac"):
        return "audio"
    if ext == ".pdf":
        return "pdf"
    if ext in (".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".rtf", ".odt"):
        return "doc"
    if ext in (".zip", ".tar", ".gz", ".7z"):
        return "archive"
    return "other"


def asset_upload_to(instance, filename):
    col_slug = instance.collection.slug if instance.collection_id else "uncategorized"
    return f"assets/{col_slug}/{filename}"


# -----------------------------
# Models
# -----------------------------
class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Collection(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        help_text="Leave blank for auto-slug.",
    )
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    visibility_mode = models.CharField(
        max_length=20, choices=VISIBILITY_MODE_CHOICES, default="public"
    )
    allowed_groups = models.ManyToManyField(Group, blank=True, related_name="asset_collections")
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)
    tags = models.ManyToManyField(Tag, blank=True, related_name="collections")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["parent__id", "sort_order", "title"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:200] or "collection"
        super().save(*args, **kwargs)

    @property
    def allowed_group_ids_csv(self) -> str:
        return ",".join(str(pk) for pk in self.allowed_groups.values_list("id", flat=True))


class Asset(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="assets")
    title = models.CharField(max_length=255)
    slug = models.SlugField(
        max_length=255,
        blank=True,
        help_text="Unique within collection. Leave blank to auto-slug.",
    )
    visibility = models.CharField(
        max_length=20, choices=ASSET_VISIBILITY_CHOICES, default="inherit"
    )
    description = models.TextField(blank=True)

    # one of these three is expected (form enforces exactly one)
    file = models.FileField(upload_to=asset_upload_to, blank=True, null=True)
    url = models.URLField(blank=True, null=True, help_text="External link or embed URL")
    text_content = models.TextField(blank=True, help_text="Plain text / note / credentials")

    appears_on = models.CharField(
        max_length=500, blank=True, help_text="Auto-filled by editor; informative only."
    )

    mime_type = models.CharField(max_length=100, blank=True)
    kind = models.CharField(max_length=20, choices=ASSET_KIND_CHOICES, default="other")
    size_bytes = models.BigIntegerField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    pages = models.IntegerField(null=True, blank=True)

    tags = models.ManyToManyField(Tag, blank=True, related_name="assets")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("collection", "slug")]
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        # Auto slug
        if not self.slug:
            self.slug = slugify(self.title)[:255] or "asset"

        # Determine a source name for MIME detection
        src_name = None
        if self.file:
            src_name = os.path.basename(self.file.name)
        elif self.url:
            from urllib.parse import urlparse

            parsed = urlparse(self.url)
            src_name = os.path.basename(parsed.path)

        # Guess mime if missing; set for text notes too
        guessed_mime, _ = mimetypes.guess_type(src_name or "")
        if not self.mime_type:
            if self.text_content and not (self.file or self.url):
                self.mime_type = "text/plain"
            else:
                self.mime_type = guessed_mime or ""

        # Classify kind (note wins if text present)
        self.kind = infer_kind(
            src_name or "", self.mime_type or None, has_text=bool(self.text_content)
        )

        # Size (only for uploaded files we hold)
        if self.file and hasattr(self.file, "size"):
            self.size_bytes = self.file.size

        super().save(*args, **kwargs)

    # convenience flags
    @property
    def is_external(self) -> bool:
        return bool(self.url) and not bool(self.file)

    @property
    def external_domain(self):
        if not self.url:
            return None
        from urllib.parse import urlparse

        return urlparse(self.url).netloc

    @property
    def effective_visibility(self) -> str:
        """
        Resolve to the visibility that actually applies:
        - 'inherit' -> collection.visibility_mode (including 'groups')
        - otherwise -> self.visibility
        """
        if self.visibility == "inherit":
            return self.collection.visibility_mode
        return self.visibility
