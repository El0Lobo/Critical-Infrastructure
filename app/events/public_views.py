from django.shortcuts import render

SAMPLE = [
    {
        "title": "Open Mic Night",
        "slug": "open-mic-night",
        "date": "2025-09-15 20:00",
        "location": "Your Bar",
        "image": None,
    },
    {
        "title": "Trivia Tuesday",
        "slug": "trivia-tuesday",
        "date": "2025-09-16 19:00",
        "location": "Your Bar",
        "image": None,
    },
]


def public_list(request):
    return render(request, "events/public_list.html", {"events": SAMPLE})


def public_detail(request):
    ev = {
        "title": "Sample Event",
        "slug": "sample-event",
        "date": "2025-10-01 21:00",
        "location": "Your Bar",
        "image": None,
        "price": "€10",
    }
    return render(request, "events/public_detail.html", {"event": ev})
