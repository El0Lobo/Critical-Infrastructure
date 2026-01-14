from django.contrib.auth.decorators import login_required
from django.shortcuts import render

SAMPLE = [
    {
        "title": "OSM/Photon",
        "slug": "osm",
        "provider": "OSM/Photon",
        "status": "OK",
        "notes": "Using server proxy (todo)",
    }
]


@login_required
def index(request):
    return render(request, "maps/index.html", {"rows": SAMPLE})


@login_required
def create(request):
    return render(request, "maps/form.html", {"mode": "create"})


@login_required
def edit(request, slug):
    item = next((r for r in SAMPLE if r.get("slug") == slug), None)
    return render(request, "maps/form.html", {"mode": "edit", "item": item})
