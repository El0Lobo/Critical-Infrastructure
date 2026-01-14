from __future__ import annotations

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import NewsPost


def news_index(request):
    queryset = NewsPost.objects.published().public()
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()

    if query:
        queryset = queryset.filter(
            Q(title__icontains=query) | Q(summary__icontains=query) | Q(body__icontains=query)
        )
    if category:
        queryset = queryset.filter(category__iexact=category)

    paginator = Paginator(queryset, 6)
    page = paginator.get_page(request.GET.get("page"))

    categories = (
        NewsPost.objects.published()
        .public()
        .exclude(category="")
        .values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )

    return render(
        request,
        "news/public_index.html",
        {
            "page_obj": page,
            "query": query,
            "active_category": category,
            "categories": categories,
        },
    )


def news_detail(request, slug):
    post = get_object_or_404(NewsPost.objects.published().public(), slug=slug)
    return render(request, "news/public_detail.html", {"post": post})
