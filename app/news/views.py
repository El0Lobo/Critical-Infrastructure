from __future__ import annotations

from collections import Counter

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import FieldError
from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .forms import NewsPollForm, NewsPostForm
from .models import NewsPoll, NewsPost, PollOption, PollVote


def _poll_base_queryset(user):
    all_votes = Prefetch(
        "votes",
        queryset=PollVote.objects.select_related("option", "user"),
        to_attr="prefetched_votes",
    )
    user_votes = Prefetch(
        "votes",
        queryset=PollVote.objects.filter(user=user).select_related("option"),
        to_attr="prefetched_user_votes",
    )
    options = Prefetch("options", queryset=PollOption.objects.all())
    return (
        NewsPoll.objects.prefetch_related(options, all_votes, user_votes)
        .select_related("created_by")
        .order_by("-created_at")
    )


def build_poll_state(poll: NewsPoll, *, user):
    all_votes = getattr(poll, "prefetched_votes", None)
    if all_votes is None:
        all_votes = list(poll.votes.select_related("option", "user"))
    option_counts = Counter(vote.option_id for vote in all_votes)
    total_votes = sum(option_counts.values())

    user_votes = getattr(poll, "prefetched_user_votes", None)
    if user_votes is None:
        user_votes = list(poll.votes.filter(user=user).select_related("option"))
    user_option_ids = {vote.option_id for vote in user_votes}

    option_payload = []
    for option in poll.options.all():
        count = option_counts.get(option.id, 0)
        voters = []
        if not poll.anonymous:
            voters = [
                vote.user.get_full_name() or vote.user.get_username()
                for vote in all_votes
                if vote.option_id == option.id
            ]
        option_payload.append(
            {
                "option": option,
                "count": count,
                "percent": (count / total_votes * 100) if total_votes else 0,
                "voters": voters,
                "selected": option.id in user_option_ids,
            }
        )

    has_voted = bool(user_option_ids)
    show_results = has_voted or not poll.is_open or poll.allow_results_before_vote
    return {
        "options": option_payload,
        "total": total_votes,
        "has_voted": has_voted,
        "show_results": show_results,
        "can_vote": poll.is_open,
        "closing_label": poll.closing_label(),
    }


def _get_post_by_any_slug(slug: str) -> NewsPost | None:
    query = Q()
    try:
        for code in settings.MODELTRANSLATION_LANGUAGES:
            query |= Q(**{f"slug_{code}": slug})
        query |= Q(slug=slug)
        return NewsPost.objects.filter(query).first()
    except FieldError:
        return NewsPost.objects.filter(slug=slug).first()


@login_required
def feed(request):
    posts = list(
        NewsPost.objects.select_related("created_by", "updated_by").order_by(
            "-published_at", "-created_at"
        )
    )
    polls = list(_poll_base_queryset(request.user))

    feed_items = []
    for post in posts:
        feed_items.append(
            {
                "type": "post",
                "post": post,
                "timestamp": post.display_timestamp or post.created_at,
            }
        )
    for poll in polls:
        feed_items.append(
            {
                "type": "poll",
                "poll": poll,
                "state": build_poll_state(poll, user=request.user),
                "timestamp": poll.created_at,
            }
        )
    feed_items.sort(key=lambda item: item["timestamp"] or timezone.now(), reverse=True)

    return render(
        request,
        "news/feed.html",
        {
            "feed_items": feed_items,
            "post_create_url": reverse("news:post_create"),
            "poll_create_url": reverse("news:poll_create"),
        },
    )


@login_required
def post_create(request):
    if request.method == "POST":
        form = NewsPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.created_by = request.user
            post.updated_by = request.user
            post.save()
            messages.success(request, "News post created.")
            return redirect("news:feed")
    else:
        form = NewsPostForm(initial={"status": NewsPost.Status.PUBLISHED})
    return render(request, "news/post_form.html", {"form": form, "mode": "create"})


@login_required
def post_edit(request, pk):
    post = get_object_or_404(NewsPost, pk=pk)
    if request.method == "POST":
        form = NewsPostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.updated_by = request.user
            post.save()
            messages.success(request, "News post updated.")
            return redirect("news:feed")
    else:
        form = NewsPostForm(instance=post)
    return render(request, "news/post_form.html", {"form": form, "mode": "edit", "post": post})


@login_required
@require_POST
def post_delete(request, pk):
    post = get_object_or_404(NewsPost, pk=pk)
    post.delete()
    messages.success(request, _("News post deleted."))
    return redirect("news:feed")


@login_required
def post_edit_legacy(request, slug):
    post = _get_post_by_any_slug(slug)
    if not post:
        raise Http404("No NewsPost matches the given query.")
    return redirect("news:post_edit", pk=post.pk)


@login_required
@require_POST
def post_delete_legacy(request, slug):
    post = _get_post_by_any_slug(slug)
    if not post:
        raise Http404("No NewsPost matches the given query.")
    post.delete()
    messages.success(request, _("News post deleted."))
    return redirect("news:feed")


@login_required
def poll_create(request):
    if request.method == "POST":
        form = NewsPollForm(request.POST)
        if form.is_valid():
            poll = form.save(commit=False)
            poll.created_by = request.user
            poll.save()
            form.save_options(poll)
            messages.success(request, "Poll created.")
            return redirect("news:feed")
    else:
        form = NewsPollForm(initial={"allow_results_before_vote": True})
    return render(request, "news/poll_form.html", {"form": form, "mode": "create"})


@login_required
def poll_edit(request, pk):
    poll = get_object_or_404(NewsPoll, pk=pk)
    if request.method == "POST":
        form = NewsPollForm(request.POST, instance=poll)
        if form.is_valid():
            poll = form.save(commit=False)
            poll.save()
            form.save_options(poll)
            messages.success(request, "Poll updated.")
            return redirect("news:feed")
    else:
        form = NewsPollForm(instance=poll)
    return render(request, "news/poll_form.html", {"form": form, "mode": "edit", "poll": poll})


@login_required
@require_POST
def poll_delete(request, pk):
    poll = get_object_or_404(NewsPoll, pk=pk)
    poll.delete()
    messages.success(request, _("Poll deleted."))
    return redirect("news:feed")


@login_required
@require_POST
def poll_vote(request, pk):
    poll = get_object_or_404(NewsPoll, pk=pk)
    if not poll.is_open:
        messages.error(request, "This poll is closed.")
        return redirect("news:feed")
    option_ids = request.POST.getlist("options")
    if not option_ids:
        messages.error(request, "Select at least one option.")
        return redirect("news:feed")
    try:
        option_ids_int = [int(value) for value in option_ids]
    except ValueError:
        messages.error(request, "Invalid option.")
        return redirect("news:feed")

    options = list(poll.options.filter(id__in=option_ids_int))
    if len(options) != len(set(option_ids_int)):
        messages.error(request, "Invalid poll option selection.")
        return redirect("news:feed")
    if not poll.allow_multiple and len(option_ids_int) > 1:
        messages.error(request, "This poll only allows one choice.")
        return redirect("news:feed")

    with transaction.atomic():
        already_voted = PollVote.objects.filter(poll=poll, user=request.user).exists()
        if already_voted:
            messages.error(request, "You have already voted in this poll.")
            return redirect(f"{reverse('news:feed')}#poll-{poll.pk}")
        for option in options:
            PollVote.objects.create(poll=poll, option=option, user=request.user)

    messages.success(request, "Your vote has been recorded.")
    return redirect(f"{reverse('news:feed')}#poll-{poll.pk}")
