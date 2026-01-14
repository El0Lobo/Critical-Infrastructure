from django.contrib.auth.decorators import login_required
from django.shortcuts import render

SAMPLE = [
    {
        "title": "Sales 2025-08-30",
        "slug": "sales-2025-08-30",
        "journal": "Sales",
        "date": "2025-08-30",
        "lines": "54",
        "total": "€812.00",
    }
]


@login_required
def index(request):
    return render(request, "accounting/index.html", {"rows": SAMPLE})


@login_required
def create(request):
    return render(request, "accounting/form.html", {"mode": "create"})


@login_required
def edit(request, slug):
    item = next((r for r in SAMPLE if r.get("slug") == slug), None)
    return render(request, "accounting/form.html", {"mode": "edit", "item": item})
