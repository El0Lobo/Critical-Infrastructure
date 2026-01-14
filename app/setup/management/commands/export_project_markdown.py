# yourapp/management/commands/export_project_markdown.py
import inspect
import json
from collections import OrderedDict, defaultdict
from collections.abc import Iterable
from datetime import date, datetime
from typing import Any

from django.apps import apps
from django.core.management.base import BaseCommand, CommandParser
from django.db import DEFAULT_DB_ALIAS, connections, models
from django.urls import URLPattern, URLResolver, get_resolver


def md_escape(text: Any) -> str:
    """Escape markdown table special chars minimally."""
    if text is None:
        return ""
    s = str(text)
    # pipe and backtick inside tables
    return s.replace("|", r"\|").replace("`", r"\`")


def fmt_code(s: Any) -> str:
    return f"`{md_escape(s)}`" if s is not None else ""


def fmt_bool(b: bool | None) -> str:
    return "✅" if b else ("❌" if b is False else "")


def fmt_default(val: Any) -> str:
    if val is models.NOT_PROVIDED or val is None:
        return ""
    try:
        if callable(val):
            mod = val.__module__
            name = getattr(val, "__name__", repr(val))
            return fmt_code(f"{mod}.{name}()")
        if isinstance(val, datetime | date):
            return fmt_code(val.isoformat())
        json.dumps(val)  # if serializable, show as code
        return fmt_code(val)
    except Exception:
        return fmt_code(repr(val))


def field_db_type(field: models.Field) -> str | None:
    try:
        conn = connections[DEFAULT_DB_ALIAS]
        return field.db_type(connection=conn)
    except Exception:
        return None


def field_info(field: models.Field) -> dict[str, Any]:
    base: dict[str, Any] = OrderedDict()
    base["name"] = field.name
    base["attname"] = getattr(field, "attname", field.name)
    base["type"] = f"{field.__class__.__module__}.{field.__class__.__name__}"
    base["db_type"] = field_db_type(field)
    base["null"] = getattr(field, "null", None)
    base["blank"] = getattr(field, "blank", None)
    base["primary_key"] = getattr(field, "primary_key", False)
    base["unique"] = getattr(field, "unique", False)
    base["db_index"] = getattr(field, "db_index", False)
    base["editable"] = getattr(field, "editable", True)
    base["db_column"] = getattr(field, "db_column", None)
    base["default"] = getattr(field, "default", models.NOT_PROVIDED)

    # Size/precision
    if hasattr(field, "max_length") and field.max_length is not None:
        base["max_length"] = field.max_length
    if hasattr(field, "decimal_places"):
        base["decimal_places"] = field.decimal_places
    if hasattr(field, "max_digits"):
        base["max_digits"] = field.max_digits

    # Choices
    choices = getattr(field, "choices", None)
    if choices:
        flat = []
        for c in choices:
            # (value, label) or grouped
            if isinstance(c, list | tuple) and len(c) == 2 and not isinstance(c[1], list | tuple):
                flat.append({"value": c[0], "label": c[1]})
            else:
                flat.append(repr(c))
        base["choices"] = flat

    # Relations
    rel = getattr(field, "remote_field", None)
    if rel is not None:
        target = rel.model
        if isinstance(target, str):
            base["related_model"] = target
        elif hasattr(target, "_meta"):
            base["related_model"] = f"{target._meta.app_label}.{target.__name__}"
        else:
            base["related_model"] = repr(target)

        base["relation_type"] = rel.__class__.__name__
        if hasattr(rel, "through") and rel.through is not None:
            through = rel.through
            if hasattr(through, "_meta"):
                base["through"] = f"{through._meta.app_label}.{through.__name__}"
            else:
                base["through"] = repr(through)

        if hasattr(field, "on_delete"):
            try:
                base["on_delete"] = field.on_delete.__name__
            except Exception:
                base["on_delete"] = repr(getattr(field, "on_delete", None))

        base["to_field"] = getattr(field, "to_fields", None) or getattr(field, "to_field", None)

    return base


def model_info(model: models.Model) -> dict[str, Any]:
    meta = model._meta
    info: dict[str, Any] = OrderedDict()
    info["app_label"] = meta.app_label
    info["object_name"] = meta.object_name
    info["db_table"] = meta.db_table
    info["managed"] = meta.managed
    info["proxy"] = meta.proxy
    info["abstract"] = meta.abstract
    info["pk"] = getattr(meta.pk, "name", None)

    fields = []
    for f in meta.get_fields():
        try:
            fields.append(field_info(f))
        except Exception as e:
            fields.append({"name": getattr(f, "name", repr(f)), "error": repr(e)})
    info["fields"] = fields
    return info


def callback_import_path(cb) -> str:
    try:
        # class-based view
        if hasattr(cb, "view_class"):
            vc = cb.view_class
            return f"{vc.__module__}.{vc.__name__}"
        # bound/unbound method
        if inspect.ismethod(cb):
            fn = cb.__func__
            return f"{fn.__module__}.{fn.__qualname__}"
        # function or callable object
        return f"{cb.__module__}.{getattr(cb, '__qualname__', getattr(cb, '__name__', repr(cb)))}"
    except Exception:
        return repr(cb)


def pattern_text(p) -> str:
    try:
        if hasattr(p, "pattern") and hasattr(p.pattern, "_route"):
            return p.pattern._route  # path()
        return str(p.pattern)  # re_path or fallback
    except Exception:
        return repr(getattr(p, "pattern", p))


def collect_urls(resolver=None) -> list[dict[str, Any]]:
    if resolver is None:
        resolver = get_resolver()

    collected: list[dict[str, Any]] = []
    for entry in resolver.url_patterns:
        if isinstance(entry, URLPattern):
            cb = getattr(entry, "callback", None)
            collected.append(
                OrderedDict(
                    pattern=pattern_text(entry),
                    name=entry.name,
                    callback=callback_import_path(cb) if cb else "",
                )
            )
        elif isinstance(entry, URLResolver):
            nested = collect_urls(entry)
            collected.extend(nested)
        else:
            collected.append({"unknown_entry": repr(entry)})
    # de-duplicate while preserving order
    seen = set()
    uniq = []
    for u in collected:
        tup = (u.get("pattern"), u.get("name"), u.get("callback"))
        if tup not in seen:
            uniq.append(u)
            seen.add(tup)
    return uniq


def render_urls_md(urls: list[dict[str, Any]]) -> str:
    lines = []
    lines.append("## URL Patterns\n")
    lines.append(f"Total: **{len(urls)}**\n")
    lines.append("| Pattern | Name | Callback |\n|---|---|---|")
    for u in urls:
        lines.append(
            f"| {md_escape(u.get('pattern'))} | {fmt_code(u.get('name'))} | {fmt_code(u.get('callback'))} |"
        )
    lines.append("")  # blank line
    return "\n".join(lines)


def render_model_section_md(mi: dict[str, Any]) -> str:
    hdr = f"### {mi['app_label']}.{mi['object_name']}"
    meta_lines = [
        f"- **DB table:** {fmt_code(mi['db_table'])}",
        f"- **Managed:** {fmt_bool(mi['managed'])}",
        f"- **Proxy:** {fmt_bool(mi['proxy'])}",
        f"- **Abstract:** {fmt_bool(mi['abstract'])}",
        f"- **Primary key field:** {fmt_code(mi['pk']) if mi['pk'] else ''}",
    ]
    tbl_header = (
        "| name | attname | type | db_type | null | blank | pk | unique | index | editable | db_column | "
        "max_len | digits | places | default | relation | related_model | through | on_delete | to_field |\n"
        "|---|---|---|---|:--:|:--:|:--:|:--:|:--:|:--:|---|---|---|---|---|---|---|---|---|---|"
    )

    rows = []
    for f in mi["fields"]:
        if "error" in f:
            rows.append(
                f"| {md_escape(f.get('name'))} |  |  |  |  |  |  |  |  |  |  |  |  |  |  | ⚠️ {md_escape(f['error'])} |  |  |  |  |"
            )
            continue

        rel = f.get("relation_type") or ""
        rows.append(
            "| "
            + " | ".join(
                [
                    md_escape(f.get("name")),
                    md_escape(f.get("attname")),
                    fmt_code(f.get("type")),
                    fmt_code(f.get("db_type")),
                    fmt_bool(f.get("null")),
                    fmt_bool(f.get("blank")),
                    fmt_bool(f.get("primary_key")),
                    fmt_bool(f.get("unique")),
                    fmt_bool(f.get("db_index")),
                    fmt_bool(f.get("editable")),
                    fmt_code(f.get("db_column")),
                    md_escape(f.get("max_length", "")),
                    md_escape(f.get("max_digits", "")),
                    md_escape(f.get("decimal_places", "")),
                    fmt_default(f.get("default")),
                    md_escape(rel),
                    fmt_code(f.get("related_model")),
                    fmt_code(f.get("through")),
                    fmt_code(f.get("on_delete")),
                    md_escape(f.get("to_field", "")),
                ]
            )
            + " |"
        )

        # Choices (if any) as a small block under the table (to keep tables compact)
        choices = f.get("choices")
        if choices:
            ch_lines = []
            for c in choices:
                if isinstance(c, dict):
                    ch_lines.append(f"    - {fmt_code(c['value'])}: {md_escape(c['label'])}")
                else:
                    ch_lines.append(f"    - {md_escape(c)}")
            rows.append(
                "<br/>\n<details><summary>Choices</summary>\n\n"
                + "\n".join(ch_lines)
                + "\n\n</details>"
            )

    section = [
        hdr,
        "",
        *meta_lines,
        "",
        tbl_header,
        *rows,
        "",
    ]
    return "\n".join(section)


def render_models_md(models_info: Iterable[dict[str, Any]]) -> str:
    by_app: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for mi in models_info:
        by_app[mi["app_label"]].append(mi)

    lines = ["## Models\n"]
    for app_label in sorted(by_app.keys()):
        lines.append(f"### App: `{app_label}`\n")
        for mi in sorted(by_app[app_label], key=lambda x: x["object_name"].lower()):
            lines.append(render_model_section_md(mi))
    lines.append("")
    return "\n".join(lines)


class Command(BaseCommand):
    help = "Export all known URL patterns and models/fields into a single Markdown file."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--out",
            dest="out",
            default="PROJECT_METADATA.md",
            help="Output Markdown file path (default: PROJECT_METADATA.md).",
        )
        parser.add_argument(
            "--title",
            dest="title",
            default="Project URL & Model Reference",
            help="Top-level document title.",
        )

    def handle(self, *args, **options):
        out_path: str = options["out"]
        title: str = options["title"]

        # Collect
        try:
            urls = collect_urls()
        except Exception as e:
            urls = []
            urls_error = repr(e)
        else:
            urls_error = None

        models_info = []
        for model in apps.get_models():
            try:
                models_info.append(model_info(model))
            except Exception as e:
                models_info.append(
                    {
                        "app_label": "?",
                        "object_name": repr(model),
                        "fields": [{"name": "?", "error": repr(e)}],
                        "db_table": "?",
                        "managed": None,
                        "proxy": None,
                        "abstract": None,
                        "pk": None,
                    }
                )

        # Render Markdown
        parts = [f"# {md_escape(title)}\n"]
        parts.append("_This file was generated automatically._\n")

        if urls_error:
            parts.append(f"> **URL collection error:** `{md_escape(urls_error)}`\n")

        parts.append(render_urls_md(urls))
        parts.append(render_models_md(models_info))

        md = "\n".join(parts)

        # Always write a file
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)

        self.stdout.write(self.style.SUCCESS(f"Wrote {out_path}"))
