from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from app.events.models import Event
from app.shifts.models import Shift
from app.shifts.services import sync_event_standard_shifts


class Command(BaseCommand):
    help = "Delete generated shifts and rebuild them from standard templates."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-clean",
            action="store_true",
            help="Do not delete existing generated shifts before rebuilding.",
        )
        parser.add_argument(
            "--slug",
            action="append",
            dest="slugs",
            help="Limit resync to these event slugs (can repeat).",
        )
        parser.add_argument(
            "--id",
            action="append",
            dest="ids",
            type=int,
            help="Limit resync to these event IDs (can repeat).",
        )
        parser.add_argument(
            "--occurrences",
            type=int,
            default=4,
            help="Number of upcoming occurrences per recurring event to generate (default: 4).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        slugs = options.get("slugs") or []
        ids = options.get("ids") or []
        clean = not options.get("no_clean")
        occurrences = max(1, options.get("occurrences") or 4)

        events = Event.objects.all()
        if slugs:
            events = events.filter(slug__in=slugs)
        if ids:
            events = events.filter(id__in=ids)

        events = events.order_by("starts_at", "slug")

        if clean:
            deleted, _ = Shift.objects.filter(template__isnull=False).delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} templated shifts."))

        total = 0
        for event in events.iterator():
            sync_event_standard_shifts(event, user=None, max_occurrences=occurrences)
            count = event.shifts.filter(template__isnull=False).count()
            total += count
            self.stdout.write(f"Resynced {event.slug}: {count} shifts")

        self.stdout.write(self.style.SUCCESS(f"Done. Total templated shifts: {total}"))
