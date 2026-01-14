from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import BandForm
from .models import Band


@login_required
def index(request):
    q = request.GET.get("q", "").strip()
    f_type = request.GET.get("type", "").strip()
    f_pub = request.GET.get("pub", "").strip()

    qs = Band.objects.all()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(genre__icontains=q))
    if f_type in {"band", "dj", "solo"}:
        qs = qs.filter(performer_type=f_type)
    if f_pub in {"0", "1"}:
        qs = qs.filter(is_published=(f_pub == "1"))

    return render(
        request, "bands/index.html", {"bands": qs, "q": q, "f_type": f_type, "f_pub": f_pub}
    )


@login_required
def edit(request, pk=None):
    instance = get_object_or_404(Band, pk=pk) if pk else None
    if request.method == "POST":
        form = BandForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            band = form.save()
            if band.is_published and not band.published_at:
                band.published_at = timezone.now()
                band.save(update_fields=["published_at"])
            return redirect("bands:index")
    else:
        form = BandForm(instance=instance)
    return render(request, "bands/form.html", {"form": form, "item": instance})


@login_required
def delete(request, pk):
    band = get_object_or_404(Band, pk=pk)
    if request.method == "POST":
        band.delete()
        return redirect("bands:index")
    return render(request, "bands/confirm_delete.html", {"obj": band, "back_url": "bands:index"})


# --- NEW ---
def public_detail(request, slug):
    """Public-facing profile; 404 if not published."""
    band = get_object_or_404(Band, slug=slug, is_published=True)
    return render(request, "bands/public_detail.html", {"band": band})
