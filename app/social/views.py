from django.contrib.auth.decorators import login_required
from django.shortcuts import render

SAMPLE = [
    {
        "title": "Instagram",
        "slug": "instagram",
        "channel": "Instagram",
        "mode": "Draft",
        "last post": "—",
        "status": "OK",
    }
]


@login_required
def index(request):
    return render(request, "social/index.html", {"rows": SAMPLE})


@login_required
def create(request):
    return render(request, "social/form.html", {"mode": "create"})


@login_required
def edit(request, slug):
    item = next((r for r in SAMPLE if r.get("slug") == slug), None)
    return render(request, "social/form.html", {"mode": "edit", "item": item})
