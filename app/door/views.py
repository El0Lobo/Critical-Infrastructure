from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from app.setup.models import SiteSettings

SAMPLE = [
    {
        "title": "Tonight",
        "slug": "tonight",
        "date": "Today",
        "max": "120",
        "current": "45",
        "status": "Open",
    }
]


@login_required
def index(request):
    max_capacity = SiteSettings.get_solo().maximum_attendee_capacity
    return render(request, "door/index.html", {"rows": SAMPLE, "max_capacity": max_capacity})


@login_required
def create(request):
    return render(request, "door/form.html", {"mode": "create"})


@login_required
def edit(request, slug):
    item = next((r for r in SAMPLE if r.get("slug") == slug), None)
    return render(request, "door/form.html", {"mode": "edit", "item": item})
