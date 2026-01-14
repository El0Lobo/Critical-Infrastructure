from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .models import Page

if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass
class NavEntry:
    title: str
    slug: str
    url: str
    pretty_slug: str
    pretty_url: str


def get_navigation_entries(*, include_hidden: bool = False) -> list[NavEntry]:
    """Return navigation entries sourced from published Page objects."""

    pages_qs = Page.objects.filter(status=Page.Status.PUBLISHED)
    if not include_hidden:
        pages_qs = pages_qs.filter(is_visible=True)
    pages_qs = pages_qs.order_by("navigation_order", "title")

    entries: list[NavEntry] = []
    for page in pages_qs:
        slug = page.slug
        url = page.get_absolute_url()
        pretty_slug = slug
        pretty_url = "/" if slug == "home" else f"/{slug}/"
        entries.append(
            NavEntry(
                title=page.title,
                slug=slug,
                url=url,
                pretty_slug=pretty_slug,
                pretty_url=pretty_url,
            )
        )

    return entries


def serialize_nav_entries(entries: Iterable[NavEntry]) -> list[dict]:
    serialized: list[dict] = []
    for entry in entries:
        serialized.append(
            {
                "title": entry.title,
                "slug": entry.slug,
                "url": entry.url,
                "pretty_slug": entry.pretty_slug,
                "pretty_url": entry.pretty_url,
            }
        )
    return serialized


def build_nav_payload(slugs: Iterable[str]) -> list[dict]:
    entries = {entry.slug: entry for entry in get_navigation_entries()}
    payload: list[dict] = []
    seen: set[str] = set()

    for slug in slugs:
        if not slug or slug in seen:
            continue
        entry = entries.get(slug)
        if entry:
            payload.append(
                {
                    "title": entry.title,
                    "slug": entry.slug,
                    "url": entry.url,
                    "pretty_slug": entry.pretty_slug,
                    "pretty_url": entry.pretty_url,
                }
            )
            seen.add(slug)
    return payload
