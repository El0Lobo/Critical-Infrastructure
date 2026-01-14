from __future__ import annotations

import uuid
from typing import Iterable

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class NewsPostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=NewsPost.Status.PUBLISHED)

    def public(self):
        return self.filter(visibility=NewsPost.Visibility.PUBLIC)

    def internal(self):
        return self.filter(visibility=NewsPost.Visibility.INTERNAL)


class NewsPost(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")

    class Visibility(models.TextChoices):
        INTERNAL = "internal", _("Internal only")
        PUBLIC = "public", _("Public")

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255, blank=True)
    summary = models.TextField(blank=True)
    body = models.TextField()
    category = models.CharField(max_length=120, blank=True)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    visibility = models.CharField(
        max_length=12, choices=Visibility.choices, default=Visibility.INTERNAL, db_index=True
    )
    hero_image = models.URLField(blank=True)
    published_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="news_posts_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="news_posts_updated",
    )
    pin_until = models.DateTimeField(blank=True, null=True)

    objects = NewsPostQuerySet.as_manager()

    class Meta:
        ordering = ("-published_at", "-created_at")

    def __str__(self) -> str:  # pragma: no cover - display helper
        return self.title

    def _generate_unique_slug(self, value=None):
        base_value = value or self.slug or self.title
        base = slugify(base_value) or uuid.uuid4().hex[:8]
        slug = base
        suffix = 2
        while (
            NewsPost.objects.filter(slug=slug)
            .exclude(pk=self.pk)
            .exists()
        ):
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug(self.title)
        else:
            clean_slug = slugify(self.slug) or uuid.uuid4().hex[:8]
            if clean_slug != self.slug:
                self.slug = clean_slug
            if (
                NewsPost.objects.filter(slug=self.slug)
                .exclude(pk=self.pk)
                .exists()
            ):
                self.slug = self._generate_unique_slug(self.slug)
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        if self.status != self.Status.PUBLISHED:
            self.published_at = None
        super().save(*args, **kwargs)

    @property
    def is_public(self) -> bool:
        return self.visibility == self.Visibility.PUBLIC

    @property
    def is_internal(self) -> bool:
        return self.visibility == self.Visibility.INTERNAL

    @property
    def display_timestamp(self):
        return self.published_at or self.created_at

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("news_public:public_news_detail", kwargs={"slug": self.slug})


class PollQuerySet(models.QuerySet):
    def active(self):
        now = timezone.now()
        return self.filter(
            models.Q(opens_at__isnull=True) | models.Q(opens_at__lte=now),
            models.Q(closes_at__isnull=True) | models.Q(closes_at__gt=now),
        )


class NewsPoll(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    allow_multiple = models.BooleanField(default=False)
    anonymous = models.BooleanField(default=True)
    allow_results_before_vote = models.BooleanField(default=True)
    opens_at = models.DateTimeField(blank=True, null=True)
    closes_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="news_polls_created",
    )

    objects = PollQuerySet.as_manager()

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:  # pragma: no cover
        return self.question

    @property
    def is_open(self) -> bool:
        now = timezone.now()
        if self.opens_at and self.opens_at > now:
            return False
        if self.closes_at and self.closes_at <= now:
            return False
        return True

    def total_votes(self) -> int:
        return PollVote.objects.filter(poll=self).count()

    def closing_label(self) -> str | None:
        if self.closes_at:
            if self.closes_at <= timezone.now():
                return _("Closed")
            return _("Closes %(date)s") % {"date": timezone.localtime(self.closes_at).strftime("%b %d, %H:%M")}
        return None


class PollOption(models.Model):
    poll = models.ForeignKey(NewsPoll, related_name="options", on_delete=models.CASCADE)
    label = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "id")

    def __str__(self):  # pragma: no cover
        return self.label


class PollVote(models.Model):
    poll = models.ForeignKey(NewsPoll, related_name="votes", on_delete=models.CASCADE)
    option = models.ForeignKey(PollOption, related_name="votes", on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="news_poll_votes", on_delete=models.CASCADE
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("option", "user")

    def __str__(self):  # pragma: no cover
        return f"{self.user} -> {self.option}"


def bulk_set_poll_options(poll: NewsPoll, labels: Iterable[str]) -> None:
    """Replace poll options preserving order and removing stale entries."""

    existing = {opt.label.strip(): opt for opt in poll.options.all()}
    new_objects: list[PollOption] = []
    order = 0
    for label in labels:
        clean = (label or "").strip()
        if not clean:
            continue
        opt = existing.pop(clean, None)
        if opt:
            if opt.order != order:
                opt.order = order
                opt.save(update_fields=["order"])
        else:
            new_objects.append(PollOption(poll=poll, label=clean, order=order))
        order += 1
    if new_objects:
        PollOption.objects.bulk_create(new_objects)
    if existing:
        PollOption.objects.filter(id__in=[opt.id for opt in existing.values()]).delete()
