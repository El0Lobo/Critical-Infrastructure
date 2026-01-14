from django.shortcuts import get_object_or_404, render

from .models import Band


def public_list(request):
    qs = Band.objects.filter(is_published=True).order_by("name")
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(name__icontains=q)
    return render(request, "bands/public_list.html", {"bands": qs, "q": q})


def public_detail(request, slug):
    band = get_object_or_404(Band, slug=slug, is_published=True)
    return render(request, "bands/public_detail.html", {"band": band})
