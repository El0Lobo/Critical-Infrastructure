from __future__ import annotations

from html import escape
from html.parser import HTMLParser

ALLOWED_TAGS = {
  "b",
  "strong",
  "i",
  "em",
  "u",
  "s",
  "del",
  "br",
  "a",
  "ul",
  "ol",
  "li",
  "span",
  "p",
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
  "img",
}
ALLOWED_ATTRS = {
  "a": {"href", "target"},
  "span": {"style"},
  "p": {"style"},
  "h1": {"style"},
  "h2": {"style"},
  "h3": {"style"},
  "h4": {"style"},
  "h5": {"style"},
  "h6": {"style"},
  "img": {"src", "alt", "title", "style", "width", "height"},
}
STYLE_TAGS = {"span", "p", "h1", "h2", "h3", "h4", "h5", "h6", "img"}
LENGTH_UNITS = ("px", "em", "rem", "pt", "vw", "vh", "vmin", "vmax", "%")


def _clean_href(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if value.lower().startswith(("http://", "https://", "mailto:", "/", "#")):
        return value
    return None


def _clean_style(value: str | None, tag: str | None = None) -> str | None:
    if not value:
        return None
    parts = []
    tag = (tag or "").lower()
    for chunk in value.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        lower = chunk.lower()
        prop, _, val = chunk.partition(":")
        prop = prop.strip().lower()
        val = val.strip()
        if not prop or not val:
            continue
        if prop == "font-size" and _is_valid_font_size(val):
            parts.append(f"{prop}: {val}")
        elif prop in {"color", "background-color"} and _is_valid_color(val):
            parts.append(f"{prop}: {val}")
        elif prop == "text-decoration" and _is_valid_text_decoration(val):
            parts.append(f"{prop}: {val}")
        elif prop == "font-family" and _is_valid_font_family(val):
            parts.append(f"{prop}: {val}")
        elif tag == "img" and prop in {"width", "height", "max-width", "max-height"}:
            if _is_valid_length(val):
                parts.append(f"{prop}: {val}")
    return "; ".join(parts) or None


def _is_valid_color(value: str) -> bool:
    value = value.strip()
    if not value:
        return False
    if value.startswith("#") and len(value) in {4, 7}:
        try:
            int(value[1:], 16)
            return True
        except ValueError:
            return False
    value_lower = value.lower()
    if value_lower.startswith("rgb(") and value_lower.endswith(")"):
        return True
    if value_lower.startswith("rgba(") and value_lower.endswith(")"):
        return True
    return False


def _is_valid_length(value: str) -> bool:
    value = value.strip().lower()
    if not value:
        return False
    if value == "auto":
        return True
    for unit in LENGTH_UNITS:
        if value.endswith(unit):
            return _is_number(value[: -len(unit)])
    return _is_number(value)


def _is_valid_font_size(value: str) -> bool:
    value = value.strip().lower()
    if value in {
        "xx-small",
        "x-small",
        "small",
        "medium",
        "large",
        "x-large",
        "xx-large",
        "smaller",
        "larger",
    }:
        return True
    return _is_valid_length(value)


def _is_valid_text_decoration(value: str) -> bool:
    value = value.strip().lower()
    return value in {"none", "underline", "line-through", "overline"}

def _is_valid_font_family(value: str) -> bool:
    if not value:
        return False
    cleaned = value.replace("\\", "").strip()
    if not cleaned:
        return False
    # allow comma-separated family names with quotes
    for segment in cleaned.split(","):
        seg = segment.strip().strip('"').strip("'")
        if not seg:
            continue
        for char in seg:
            if char.isalnum() or char in {" ", "-", "_"}:
                continue
            return False
    return True


def _clean_src(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    lower = value.lower()
    if lower.startswith(("http://", "https://", "/", "data:image/")):
        return value
    return None


def _clean_dimension_attr(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if _is_valid_length(value):
        return value
    return None


def _is_number(value: str) -> bool:
    if not value:
        return False
    try:
        float(value)
        return True
    except ValueError:
        return False


class _InlineSanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_starttag(self, tag, attrs):  # noqa: D401
        tag = tag.lower()
        if tag in ALLOWED_TAGS:
            if tag == "br":
                self._parts.append("<br>")
            else:
                attr_bits: list[str] = []
                allowed = ALLOWED_ATTRS.get(tag, set())
                for (name, value) in attrs:
                    name = name.lower()
                    if name not in allowed:
                        continue
                    if tag == "a" and name == "href":
                        clean = _clean_href(value)
                        if clean:
                            attr_bits.append(f' href="{escape(clean)}"')
                    elif tag == "a" and name == "target":
                        if value in {"_blank", "_self"}:
                            attr_bits.append(f' target="{escape(value)}"')
                    elif tag == "img" and name == "src":
                        clean_src = _clean_src(value)
                        if clean_src:
                            attr_bits.append(f' src="{escape(clean_src)}"')
                    elif tag == "img" and name in {"alt", "title"}:
                        attr_bits.append(f' {escape(name)}="{escape(value or "")}"')
                    elif tag == "img" and name in {"width", "height"}:
                        cleaned = _clean_dimension_attr(value)
                        if cleaned:
                            attr_bits.append(f' {escape(name)}="{escape(cleaned)}"')
                    elif name == "style" and tag in STYLE_TAGS:
                        safe = _clean_style(value, tag)
                        if safe:
                            attr_bits.append(f' style="{escape(safe)}"')
                    else:
                        attr_bits.append(f' {escape(name)}="{escape(value or "")}"')
                attr_string = "".join(attr_bits)
                self._parts.append(f"<{tag}{attr_string}>")

    def handle_endtag(self, tag):  # noqa: D401
        tag = tag.lower()
        if tag in ALLOWED_TAGS and tag != "br":
            self._parts.append(f"</{tag}>")

    def handle_startendtag(self, tag, attrs):  # noqa: D401
        tag = tag.lower()
        if tag == "br":
            self._parts.append("<br>")

    def handle_data(self, data):  # noqa: D401
        if data:
            self._parts.append(escape(data))

    def handle_entityref(self, name):  # noqa: D401
        self._parts.append(f"&{name};")

    def handle_charref(self, name):  # noqa: D401
        self._parts.append(f"&#{name};")

    def get_html(self) -> str:
        return "".join(self._parts)


def sanitize_inline_html(value: str | None) -> str:
    if not value:
        return ""
    parser = _InlineSanitizer()
    parser.feed(value)
    parser.close()
    return parser.get_html()
