"""Shift planning views."""

from __future__ import annotations

import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from app.core.date_utils import add_months
from app.events.models import Event
from app.shifts.forms import (
    EventShiftFormSet,
    ShiftAssignmentForm,
    ShiftFilterForm,
    ShiftStatsFilterForm,
    ShiftTemplateForm,
)
from app.shifts.models import Shift, ShiftAssignment, ShiftTemplate

User = get_user_model()


def _build_index_context(request):
    filter_form = ShiftFilterForm(request.GET or None)
    filters = filter_form.cleaned_data if filter_form.is_valid() else {}

    shifts_qs = (
        Shift.objects.select_related("event", "template")
        .prefetch_related("assignments__user__profile")
        .order_by("start_at")
    )

    include_past = bool(filters.get("include_past"))
    timeframe = filters.get("timeframe") or ShiftFilterForm.Timeframe.WEEK
    offset = filters.get("period_offset") or 0
    tz = timezone.get_current_timezone()
    now = timezone.now()
    local_now = timezone.localtime(now, tz)

    start_local = None
    end_local = None

    if timeframe == ShiftFilterForm.Timeframe.WEEK:
        base = (local_now - timedelta(days=local_now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        start_local = base + timedelta(weeks=offset)
        end_local = start_local + timedelta(weeks=1)
    elif timeframe == ShiftFilterForm.Timeframe.MONTH:
        base = local_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_local = add_months(base, offset)
        end_local = add_months(start_local, 1)
    elif timeframe == ShiftFilterForm.Timeframe.YEAR:
        base = local_now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        start_local = base.replace(year=base.year + offset)
        end_local = start_local.replace(year=start_local.year + 1)

    lower_bound = None
    if include_past:
        lower_bound = start_local
    else:
        if timeframe == ShiftFilterForm.Timeframe.ALL:
            lower_bound = now
        else:
            candidates = [dt for dt in [now, start_local] if dt is not None]
            lower_bound = max(candidates) if candidates else None

    if timeframe == ShiftFilterForm.Timeframe.MONTH:
        baseline = lower_bound if lower_bound is not None else start_local
        if baseline is not None:
            min_end = baseline + timedelta(days=28)
            if end_local is None or end_local < min_end:
                end_local = min_end

    if lower_bound is not None:
        shifts_qs = shifts_qs.filter(start_at__gte=lower_bound)

    if end_local is not None:
        shifts_qs = shifts_qs.filter(start_at__lte=end_local)

    if timeframe == ShiftFilterForm.Timeframe.WEEK and start_local and end_local:
        range_label = (
            f"{start_local.strftime('%b %d')} – {(end_local - timedelta(days=1)).strftime('%b %d')}"
        )
    elif timeframe == ShiftFilterForm.Timeframe.MONTH and start_local:
        range_label = start_local.strftime("%B %Y")
    elif timeframe == ShiftFilterForm.Timeframe.YEAR and start_local:
        range_label = start_local.strftime("%Y")
    else:
        range_label = "All shifts" if include_past else "Upcoming shifts"

    show_navigation = timeframe != ShiftFilterForm.Timeframe.ALL
    nav_prev = nav_next = None
    if show_navigation:

        def build_nav(delta: int) -> str:
            params = request.GET.copy()
            params["timeframe"] = timeframe
            new_offset = offset + delta
            if new_offset:
                params["period_offset"] = str(new_offset)
            elif "period_offset" in params:
                del params["period_offset"]
            return f"{request.path}?{params.urlencode()}"

        nav_prev = build_nav(-1)
        nav_next = build_nav(1)

    timeframe_label = dict(ShiftFilterForm.Timeframe.choices).get(timeframe, "")

    upcoming_shifts = list(shifts_qs)

    # Build simple assignment badges on each shift
    assignee_statuses = {
        ShiftAssignment.Status.ASSIGNED,
        ShiftAssignment.Status.COMPLETED,
    }
    for shift in upcoming_shifts:
        badges = []
        for assignment in shift.assignments.all():
            if assignment.status not in assignee_statuses:
                continue
            badges.append(
                {
                    "name": assignment.display_name,
                    "user_id": assignment.user_id,
                }
            )
        shift.assignment_badges = badges

    # Stats filter + bounds
    stats_form = ShiftStatsFilterForm(request.GET or None)
    stats_form.is_valid()
    since = stats_form.get_bounds()

    # Assignment stats
    assignments = ShiftAssignment.objects.select_related("shift", "user")
    if since:
        assignments = assignments.filter(assigned_at__gte=since)

    stats_data = assignments.values("user_id").annotate(total=Count("id")).order_by("-total")

    user_ids = [row["user_id"] for row in stats_data if row["user_id"]]
    users = {u.id: u for u in User.objects.filter(id__in=user_ids).select_related("profile")}

    def _display_name(user):
        if not user:
            return "�"
        profile = getattr(user, "profile", None)
        if profile:
            chosen = (getattr(profile, "chosen_name", "") or "").strip()
            if chosen:
                return chosen
            legal = (getattr(profile, "legal_name", "") or "").strip()
            if legal:
                return legal
        full_name = (getattr(user, "get_full_name", lambda: "")() or "").strip()
        if full_name:
            return full_name
        username = getattr(user, "get_username", lambda: str(getattr(user, "pk", "")))()
        return username or str(getattr(user, "pk", ""))

    stats = [
        {
            "user_id": row["user_id"],
            "total": row["total"],
            "display_name": _display_name(users.get(row["user_id"])),
        }
        for row in stats_data
    ]

    # Forms
    assign_form = ShiftAssignmentForm()
    assign_form.fields["user"].queryset = User.objects.all()  # adjust if you need filtering

    template_form = ShiftTemplateForm()
    templates = ShiftTemplate.objects.order_by("order", "name")
    template_edit_forms = {
        tmpl.id: ShiftTemplateForm(instance=tmpl, prefix=f"tmpl-{tmpl.id}") for tmpl in templates
    }
    template_forms = [(tmpl, template_edit_forms[tmpl.id]) for tmpl in templates]

    # Which shifts the current user already has
    taken_shift_ids = set()
    if request.user.is_authenticated:
        taken_shift_ids = set(
            ShiftAssignment.objects.filter(
                user=request.user,
                status__in=[
                    ShiftAssignment.Status.ASSIGNED,
                    ShiftAssignment.Status.COMPLETED,
                ],
                shift__in=upcoming_shifts,
            ).values_list("shift_id", flat=True)
        )

    # Group shifts by event (and fetch events efficiently)
    event_ids = {s.event_id for s in upcoming_shifts if s.event_id}
    event_map = {
        e.id: e
        for e in Event.objects.filter(pk__in=event_ids)
        .select_related("created_by", "updated_by")
        .prefetch_related("categories", "performers__band")
    }

    events_by_key = {}
    events_with_shifts = []
    for shift in upcoming_shifts:
        event = event_map.get(shift.event_id, getattr(shift, "event", None))
        if not event:
            continue
        occurrence_date = None
        if shift.start_at:
            occurrence_date = timezone.localtime(shift.start_at).date()
        key = (event.id, occurrence_date)
        entry = events_by_key.get(key)
        if not entry:
            entry = {
                "event": event,
                "shifts": [],
                "occurrence_date": occurrence_date,
                "occurrence_start": shift.start_at,
            }
            events_by_key[key] = entry
            events_with_shifts.append(entry)
        else:
            if shift.start_at and (
                entry["occurrence_start"] is None or shift.start_at < entry["occurrence_start"]
            ):
                entry["occurrence_start"] = shift.start_at
        entry["shifts"].append(shift)

    for entry in events_with_shifts:
        if entry["occurrence_start"]:
            entry["occurrence_label"] = timezone.localtime(entry["occurrence_start"]).strftime(
                "%a %d.%m.%Y %H:%M"
            )
        elif entry["occurrence_date"]:
            entry["occurrence_label"] = entry["occurrence_date"].strftime("%a %d.%m.%Y")
        else:
            entry["occurrence_label"] = "Unscheduled"

    # Build per-event assign options (ALWAYS define `options`)
    for entry in events_with_shifts:
        options = []
        for s in entry["shifts"]:
            title = getattr(s, "title", None) or str(s)

            try:
                start_label = timezone.localtime(s.start_at).strftime("%H:%M")
            except Exception:
                start_label = (
                    s.start_at.strftime("%H:%M") if hasattr(s.start_at, "strftime") else ""
                )

            try:
                end_label = timezone.localtime(s.end_at).strftime("%H:%M")
            except Exception:
                end_label = s.end_at.strftime("%H:%M") if hasattr(s.end_at, "strftime") else ""

            label = f"{title} ({start_label}-{end_label})" if start_label and end_label else title
            options.append({"id": s.id, "label": label, "title": title})

        # Safe JSON (won't crash on dates/decimals)
        entry["assign_options_json"] = json.dumps(options, default=str)
        entry["has_shift_options"] = bool(options)

    return {
        "shifts": upcoming_shifts,
        "events_with_shifts": events_with_shifts,
        "assign_form": assign_form,
        "shift_filter_form": filter_form,
        "shift_filter_range_label": range_label,
        "shift_filter_nav_prev_url": nav_prev,
        "shift_filter_nav_next_url": nav_next,
        "shift_filter_nav_show": show_navigation,
        "shift_filter_timeframe_label": timeframe_label,
        "shift_period_offset": offset,
        "stats_form": stats_form,
        "stats": stats,
        "taken_shift_ids": taken_shift_ids,
        "template_form": template_form,
        "templates": templates,
        "template_edit_forms": template_edit_forms,
        "template_forms": template_forms,
    }


@login_required
def index(request: HttpRequest) -> HttpResponse:
    context = _build_index_context(request)
    return render(request, "shifts/index.html", context)


@login_required
def assign(request: HttpRequest, shift_id: int) -> HttpResponse:
    if not request.user.is_superuser:
        messages.error(request, "Only administrators can assign other users to shifts.")
        return redirect("shifts:index")

    shift = get_object_or_404(Shift, pk=shift_id)
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    form = ShiftAssignmentForm(request.POST)
    if form.is_valid():
        user = form.cleaned_data.get("user")
        notes = form.cleaned_data.get("notes") or ""

        if not user:
            ShiftAssignment.objects.filter(shift=shift).delete()
            message_text = "Assignment cleared."
        else:
            assignment, _ = ShiftAssignment.objects.get_or_create(
                shift=shift,
                user=user,
                defaults={
                    "status": ShiftAssignment.Status.ASSIGNED,
                    "notes": notes,
                    "assigned_by": request.user,
                },
            )
            assignment.status = ShiftAssignment.Status.ASSIGNED
            assignment.notes = notes
            assignment.assigned_by = request.user
            assignment.save()
            message_text = "Assignment updated."

        messages.success(request, message_text)
        if request.htmx:
            response = HttpResponse(status=204)
            response["Hx-Trigger"] = "shift:assignment"
            response["Hx-Redirect"] = reverse("shifts:index")
            return response
        return redirect("shifts:index")

    return render(
        request,
        "shifts/partials/assignment_form_body.html",
        {"assign_form": form, "shift": shift},
        status=400,
    )


@login_required
def create_template(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    form = ShiftTemplateForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Standard shift saved.")
        if request.htmx:
            response = HttpResponse(status=204)
            response["Hx-Redirect"] = reverse("shifts:index")
            return response
        return redirect("shifts:index")

    return render(
        request,
        "shifts/partials/template_form_body.html",
        {"template_form": form},
        status=400,
    )


@login_required
def update_template(request: HttpRequest, pk: int) -> HttpResponse:
    template = get_object_or_404(ShiftTemplate, pk=pk)
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    form = ShiftTemplateForm(request.POST, instance=template, prefix=f"tmpl-{pk}")
    if form.is_valid():
        form.save()
        messages.success(request, "Standard shift updated.")
        return redirect("shifts:index")

    messages.error(request, "Please correct the errors below.")
    context = _build_index_context(request)
    context["template_edit_forms"][pk] = form
    context["template_forms"] = [
        (tmpl, context["template_edit_forms"][tmpl.id]) for tmpl in context["templates"]
    ]
    return render(request, "shifts/index.html", context, status=400)


@login_required
def delete_template(request: HttpRequest, pk: int) -> HttpResponse:
    template = get_object_or_404(ShiftTemplate, pk=pk)
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    template.delete()
    messages.success(request, "Standard shift deleted.")
    return redirect("shifts:index")


@login_required
def take(request: HttpRequest, shift_id: int) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    shift = get_object_or_404(Shift, pk=shift_id)

    if not shift.allow_signup:
        messages.error(request, "This shift is not open for self sign-up.")
        return redirect("shifts:index")

    if shift.is_full and not shift.is_taken_by(request.user):
        messages.error(request, "This shift is already filled.")
        return redirect("shifts:index")

    assignment, _ = ShiftAssignment.objects.get_or_create(
        shift=shift,
        user=request.user,
        defaults={
            "status": ShiftAssignment.Status.ASSIGNED,
            "assigned_by": request.user,
        },
    )

    assignment.status = ShiftAssignment.Status.ASSIGNED
    assignment.assigned_by = request.user
    assignment.save()

    messages.success(request, "You have been assigned to this shift.")
    return redirect("shifts:index")


@login_required
def manage_event(request: HttpRequest, event_slug: str) -> HttpResponse:
    event = get_object_or_404(Event, slug=event_slug)
    if request.method == "POST":
        formset = EventShiftFormSet(request.POST, instance=event)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for inst in instances:
                inst.updated_by = request.user
                if not inst.pk:
                    inst.created_by = request.user
                inst.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, "Shifts updated.")
            return redirect("shifts:manage_event", event_slug=event.slug)
    else:
        formset = EventShiftFormSet(instance=event)
    return render(
        request,
        "shifts/manage_event.html",
        {"event": event, "formset": formset},
    )
