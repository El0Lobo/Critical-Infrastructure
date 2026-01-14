from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from app.events.models import Event
from app.inventory.models import InventoryItem
from app.inventory.utils import user_can_see_inventory_dashboard
from app.shifts.models import Shift, ShiftAssignment
from app.news.models import NewsPoll, NewsPost


@login_required
def dashboard(request):
    cards = []
    inventory_alerts = []
    shift_glance = None

    if user_can_see_inventory_dashboard(request.user):
        inventory_alerts = list(
            InventoryItem.objects.filter(needs_reorder=True)
            .order_by("name")
            .values("name", "current_stock", "desired_stock", "location")[:8]
        )

    start = timezone.now()
    end = start + timedelta(days=7)
    upcoming_shifts = (
        Shift.objects.filter(start_at__gte=start, start_at__lt=end)
        .select_related("event")
        .annotate(
            filled=Count(
                "assignments",
                filter=Q(
                    assignments__status__in=[
                        ShiftAssignment.Status.ASSIGNED,
                        ShiftAssignment.Status.COMPLETED,
                    ]
                ),
            )
        )
    )
    total_slots = upcoming_shifts.aggregate(total=Sum("capacity")).get("total") or 0
    open_items = []
    open_total = 0
    open_by_event = {}
    for shift in upcoming_shifts:
        open_slots = max(shift.capacity - getattr(shift, "filled", 0), 0)
        if open_slots > 0 and shift.event:
            key = shift.event.pk
            open_by_event.setdefault(
                key,
                {
                    "event": shift.event,
                    "open": 0,
                },
            )
            open_by_event[key]["open"] += open_slots
            open_total += open_slots
    open_items = sorted(open_by_event.values(), key=lambda item: item["event"].starts_at)[:5]
    if total_slots:
        shift_glance = {
            "total": total_slots,
            "filled": total_slots - open_total,
            "open": open_total,
            "open_items": open_items,
        }

    recent_events = list(
        Event.objects.filter(recurrence_parent__isnull=True)
        .order_by("-created_at")
        .only("title", "starts_at", "slug")[:3]
    )
    news_digest: list[dict] = []
    posts = list(
        NewsPost.objects.published()
        .internal()
        .order_by("-published_at", "-created_at")
        .only("title", "summary", "slug", "published_at", "created_at")[:3]
    )
    polls = list(NewsPoll.objects.active().order_by("-created_at")[:3])
    for post in posts:
        news_digest.append(
            {
                "type": "post",
                "title": post.title,
                "description": (post.summary or "")[:180],
                "timestamp": post.published_at or post.created_at,
                "url": reverse("news:feed"),
                "badge": _("News"),
            }
        )
    for poll in polls:
        if not poll.is_open:
            continue
        news_digest.append(
            {
                "type": "poll",
                "title": poll.question,
                "description": (poll.description or "")[:180],
                "timestamp": poll.opens_at or poll.created_at,
                "url": reverse("news:feed"),
                "badge": _("Poll"),
                "closing_label": poll.closing_label(),
            }
        )
    news_digest.sort(key=lambda item: item.get("timestamp") or timezone.now(), reverse=True)
    news_digest = news_digest[:3]

    context = {
        "cards": cards,
        "inventory_alerts": inventory_alerts,
        "shift_glance": shift_glance,
        "recent_events": recent_events,
        "news_digest": news_digest,
        "news_feed_url": reverse("news:feed"),
    }
    return render(request, "cms/dashboard.html", context)


@login_required
def account(request):
    return render(request, "cms/account.html")
