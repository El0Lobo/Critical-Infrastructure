from __future__ import annotations

from copy import deepcopy
from typing import Any

from django.utils.html import strip_tags


def _absolute_url(request, url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith("http://") or url.startswith("https://"):
        return url
    if request:
        try:
            return request.build_absolute_uri(url)
        except Exception:
            return url
    return url


def _build_address(address: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(address, dict):
        return None
    street = " ".join(filter(None, [address.get("street"), address.get("number")])).strip()
    city = (address.get("city") or "").strip()
    postal = (address.get("postal_code") or "").strip()
    state = (address.get("state") or "").strip()
    country = (address.get("country") or "").strip()
    if not any([street, city, postal, state, country]):
        return None
    payload: dict[str, Any] = {"@type": "PostalAddress"}
    if street:
        payload["streetAddress"] = street
    if city:
        payload["addressLocality"] = city
    if postal:
        payload["postalCode"] = postal
    if state:
        payload["addressRegion"] = state
    if country:
        payload["addressCountry"] = country
    return payload


def _build_place(site_context: dict[str, Any]) -> dict[str, Any] | None:
    name = (site_context.get("name") or "").strip()
    address = _build_address(site_context.get("address"))
    geo = site_context.get("geo") or {}
    lat = geo.get("lat")
    lng = geo.get("lng")
    if not any([name, address, lat, lng]):
        return None
    place: dict[str, Any] = {"@type": "Place"}
    if name:
        place["name"] = name
    if address:
        place["address"] = address
    if lat is not None or lng is not None:
        place["geo"] = {"@type": "GeoCoordinates"}
        if lat is not None:
            place["geo"]["latitude"] = lat
        if lng is not None:
            place["geo"]["longitude"] = lng
    contact = site_context.get("contact") or {}
    phone = (contact.get("phone") or "").strip()
    if phone:
        place["telephone"] = phone
    return place


def build_base_structured_data(*, page, request, site_context: dict[str, Any]) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    site_url = _absolute_url(request, site_context.get("contact", {}).get("website")) or (
        request.build_absolute_uri("/") if request else ""
    )
    page_url = _absolute_url(request, page.get_absolute_url()) if request else None
    logo_url = _absolute_url(request, site_context.get("logo"))
    address = _build_address(site_context.get("address"))
    same_as = site_context.get("same_as") or []

    organization: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": site_context.get("name") or page.title,
    }
    if site_url:
        organization["url"] = site_url
    if logo_url:
        organization["logo"] = logo_url
    if address:
        organization["address"] = address
    contact = site_context.get("contact") or {}
    phone = (contact.get("phone") or "").strip()
    email = (contact.get("email") or "").strip()
    if phone or email:
        contact_point = {"@type": "ContactPoint"}
        if phone:
            contact_point["telephone"] = phone
        if email:
            contact_point["email"] = email
        organization["contactPoint"] = [contact_point]
    if same_as:
        organization["sameAs"] = same_as
    payloads.append(organization)

    if site_url:
        payloads.append(
            {
                "@context": "https://schema.org",
                "@type": "WebSite",
                "name": site_context.get("name") or "Website",
                "url": site_url,
            }
        )

    description = page.summary or ""
    if not description and page.body:
        description = strip_tags(page.body)[:400]
    page_ld: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": page.title,
    }
    if page_url:
        page_ld["url"] = page_url
    if description:
        page_ld["description"] = description
    if page.hero_image:
        page_ld["image"] = _absolute_url(request, page.hero_image.url)
    if page.published_at:
        page_ld["datePublished"] = page.published_at.isoformat()
    payloads.append(page_ld)

    place = _build_place(site_context)
    if place:
        place["@context"] = "https://schema.org"
        payloads.append(place)

    return payloads


def build_event_structured_data(
    events: list[dict[str, Any]],
    *,
    site_context: dict[str, Any],
) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    currency = site_context.get("default_currency") or "EUR"
    for event in events:
        data: dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "Event",
            "name": event.get("title") or event.get("name"),
        }
        if event.get("starts_at"):
            data["startDate"] = event["starts_at"]
        if event.get("ends_at"):
            data["endDate"] = event["ends_at"]
        if event.get("url"):
            data["url"] = event["url"]
        if event.get("hero_image"):
            data["image"] = event["hero_image"]
        if event.get("teaser"):
            data["description"] = event["teaser"]
        elif event.get("description"):
            data["description"] = strip_tags(event["description"])[:400]
        location = _build_place(site_context)
        if location:
            data["location"] = location
        offers = {}
        if event.get("ticket_price_from"):
            offers["price"] = event["ticket_price_from"]
        if event.get("ticket_price_to"):
            offers["priceCurrency"] = currency
        if offers:
            offers["@type"] = "Offer"
            if event.get("url"):
                offers["url"] = event["url"]
            data["offers"] = offers
        payloads.append(data)
    return payloads


def build_menu_structured_data(
    categories: list[dict[str, Any]],
    *,
    site_context: dict[str, Any],
    title: str | None = None,
) -> dict[str, Any] | None:
    if not categories:
        return None
    menu: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Menu",
        "name": title or "Menu",
        "hasMenuSection": [],
    }
    currency = site_context.get("default_currency") or "EUR"

    def _serialize_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        serialized = []
        for item in items or []:
            menu_item: dict[str, Any] = {"@type": "MenuItem", "name": item.get("name")}
            if item.get("description"):
                menu_item["description"] = item["description"]
            offers = []
            for variant in item.get("variants") or []:
                if not variant.get("price"):
                    continue
                offer = {"@type": "Offer", "price": variant["price"], "priceCurrency": currency}
                if variant.get("label"):
                    offer["name"] = variant["label"]
                offers.append(offer)
            if offers:
                menu_item["offers"] = offers
            serialized.append(menu_item)
        return serialized

    def _serialize_section(category: dict[str, Any]) -> dict[str, Any]:
        section: dict[str, Any] = {"@type": "MenuSection", "name": category.get("name")}
        items = _serialize_items(category.get("items") or [])
        if items:
            section["hasMenuItem"] = items
        children = category.get("children") or []
        if children:
            section["hasMenuSection"] = [_serialize_section(child) for child in children]
        return section

    menu["hasMenuSection"] = [_serialize_section(cat) for cat in categories]
    return menu


def build_map_structured_data(
    *,
    site_context: dict[str, Any],
    address_override: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    map_url: str | None = None,
) -> dict[str, Any] | None:
    place = {"@context": "https://schema.org", "@type": "Place"}
    name = site_context.get("name")
    if name:
        place["name"] = name
    if address_override:
        place["address"] = {
            "@type": "PostalAddress",
            "streetAddress": address_override,
        }
    else:
        addr = _build_address(site_context.get("address"))
        if addr:
            place["address"] = addr
    geo = {}
    if latitude is not None:
        geo["latitude"] = latitude
    if longitude is not None:
        geo["longitude"] = longitude
    if geo:
        geo["@type"] = "GeoCoordinates"
        place["geo"] = geo
    if map_url:
        place["hasMap"] = map_url
    return place if len(place) > 2 else None
