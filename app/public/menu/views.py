from django.shortcuts import render

from app.menu.models import Category


def menu_page(request):
    roots = Category.objects.filter(parent__isnull=True).order_by("name")
    return render(
        request,
        "public/menu.html",
        {
            "roots": roots,
        },
    )
