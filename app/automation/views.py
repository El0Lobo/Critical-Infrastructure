from django.contrib.auth.decorators import login_required
from django.shortcuts import render

SAMPLE = [
    {
        "title": "Open Venue",
        "slug": "open-venue",
        "scene": "Open Venue",
        "type": "HA scene",
        "bound to": "Event start -1h",
        "status": "OK",
    }
]


@login_required
def index(request):
    return render(request, "automation/index.html", {"rows": SAMPLE})


@login_required
def create(request):
    return render(request, "automation/form.html", {"mode": "create"})


@login_required
def edit(request, slug):
    item = next((r for r in SAMPLE if r.get("slug") == slug), None)
    return render(request, "automation/form.html", {"mode": "edit", "item": item})
