import logging
import subprocess
import sys
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Case, CharField, F, Q, Value, When
from django.db.models.functions import Substr
from django.db.models.functions.text import StrIndex
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from django.utils.safestring import mark_safe
from django.conf import settings
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db import connections

from .forms import HourFormSet, SettingsForm, VisibilityRuleForm
from .helpers import is_allowed
from .models import OpeningHour, SiteSettings, VisibilityRule
from .icon_pack import IconPackError, import_icon_pack
from .branding_assets import sync_branding_assets
from . import tunnel_manager

logger = logging.getLogger(__name__)

def setup_access_required(u):
    if not getattr(u, "is_authenticated", False):
        return False
    if u.is_superuser:
        return True
    return is_allowed(u, "cms.nav.setup")


def ensure_hours_for(settings_obj):
    """Make sure all 7 weekday rows exist for this settings singleton."""
    existing = set(settings_obj.hours.values_list("weekday", flat=True))
    for wd in range(7):
        if wd not in existing:
            OpeningHour.objects.create(settings=settings_obj, weekday=wd, closed=True)


@login_required
@user_passes_test(setup_access_required)
@transaction.atomic
def setup_view(request):
    """
    CMS Setup: edits SiteSettings + inline formsets.
    """
    settings_obj = SiteSettings.get_solo()
    ensure_hours_for(settings_obj)

    if request.method == "POST":
        op = request.POST.get("op")
        if op == "seed_export":
            return seed_export(request)
        if op == "seed_reset":
            return seed_reset(request)
        if op == "seed_clear":
            return seed_clear(request)
        if op == "tunnel_start":
            return tunnel_start(request)
        if op == "tunnel_stop":
            return tunnel_stop(request)
        scope = request.POST.get("save_scope") or "all"
        logger.info("Setup POST received (scope=%s) by %s", scope, request.user)
        form = SettingsForm(request.POST, request.FILES, instance=settings_obj)
        hours = HourFormSet(request.POST, instance=settings_obj, prefix="hours")

        # Partial-save: save what validates, warn on the rest
        main_ok = form.is_valid()
        hours_ok = hours.is_valid()

        if main_ok:
            address_before = {
                key: getattr(settings_obj, key)
                for key in [
                    "address_street",
                    "address_number",
                    "address_postal_code",
                    "address_city",
                    "address_state",
                    "address_country",
                ]
            }
            address_after = {
                key: form.cleaned_data.get(key)
                for key in [
                    "address_street",
                    "address_number",
                    "address_postal_code",
                    "address_city",
                    "address_state",
                    "address_country",
                ]
            }
            if address_before != address_after:
                logger.info("Address change detected: %s -> %s", address_before, address_after)
            logger.info("Setup settings form valid. Changed fields: %s", form.changed_data)
            settings_saved = form.save()
            sync_branding_assets(
                settings_saved,
                uploads={
                    "logo": request.FILES.get("logo"),
                },
            )

            skipped = []
            icon_msg = None

            icon_pack = form.cleaned_data.get("icon_pack")
            if icon_pack:
                try:
                    import_icon_pack(icon_pack, settings_saved)
                    icon_msg = "Icon pack uploaded."
                    logger.info("Icon pack processed successfully")
                except IconPackError as exc:
                    icon_msg = None
                    messages.error(request, f"Icon pack not processed: {exc}")
                    logger.exception("Icon pack upload failed")

            if hours_ok:
                hours.save()
            else:
                skipped.append("Opening times")
                logger.warning("Opening hours form invalid: %s", hours.errors if hasattr(hours, "errors") else "unknown")

            msg = "Settings saved."
            messages.success(request, msg)
            if icon_msg:
                messages.success(request, icon_msg)

            if skipped:
                messages.warning(
                    request, "Some sections were not saved: " + ", ".join(skipped) + "."
                )

            return redirect("setup:setup")
        else:
            logger.warning("Setup settings form invalid: %s", form.errors)
            # With our permissive form, this should be rare; still show what failed
            messages.error(
                request, "Could not save the core settings. Please review the highlighted fields."
            )
    else:
        form = SettingsForm(instance=settings_obj)
        hours = HourFormSet(instance=settings_obj, prefix="hours")

    return render(
        request,
        "setup/setup.html",
        {
            "form": form,
            "hours": hours,
            "tunnel_url": tunnel_manager.current_url(),
            "tunnel_running": tunnel_manager.is_running(),
        },
    )


def _op_response(request, func):
    seed_path = Path(settings.BASE_DIR) / "seed_full.json"
    try:
        return func()
    except Exception as exc:  # pragma: no cover
        messages.error(request, str(exc))
    return redirect("setup:setup")


@login_required
@user_passes_test(setup_access_required)
def seed_export(request):
    def _run():
        seed_path = Path(settings.BASE_DIR) / "seed_full.json"
        with seed_path.open("w", encoding="utf-8") as seed_file:
            call_command(
                "dumpdata",
                use_natural_foreign_keys=True,
                use_natural_primary_keys=True,
                indent=2,
                stdout=seed_file,
            )
        rel = seed_path.relative_to(settings.BASE_DIR)
        messages.success(request, f"Seed written to {rel}.")

    return _op_response(request, _run)


def _run_manage_command(*args):
    """Run a management command in a fresh process so destructive actions work reliably."""

    cmd = [sys.executable, str(Path(settings.BASE_DIR) / "manage.py"), *args]
    result = subprocess.run(cmd, capture_output=True, text=True)  # nosec - dev tool only
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Command failed")
    return result.stdout.strip()


def _sqlite_db_file():
    db = settings.DATABASES.get("default", {})
    if db.get("ENGINE") == "django.db.backends.sqlite3":
        name = db.get("NAME")
        if name and name != ":memory:":
            return Path(name)
    return None


def _reset_sqlite_db(sqlite_path: Path) -> None:
    connections.close_all()
    for suffix in ("", "-wal", "-shm"):
        path = sqlite_path.with_name(sqlite_path.name + suffix)
        if path.exists():
            path.unlink()


def _discard_session(request, response):
    if hasattr(request, "session"):
        request.session = request.session.__class__()
        request.session.accessed = False
        request.session.modified = False
        response.delete_cookie(settings.SESSION_COOKIE_NAME)


def _ensure_dev_admin():
    User = get_user_model()
    if not User.objects.filter(is_superuser=True).exists():
        _run_manage_command("create_dev_admin")


def _normalise_menu_categories():
    """
    Ensure imported seed data leaves menu categories in a usable state.
    """

    try:
        from app.menu.models import Category
    except ImportError:
        return

    Category.objects.filter(kind__isnull=True).update(kind=Category.KIND_GENERIC)
    Category.objects.filter(kind="").update(kind=Category.KIND_GENERIC)


@login_required
@user_passes_test(setup_access_required)
def seed_reset(request):
    seed_path = Path(settings.BASE_DIR) / "seed_full.json"
    if not seed_path.exists():
        messages.error(request, "seed_full.json not found in project root.")
        return redirect("setup:setup")
    try:
        sqlite_path = _sqlite_db_file()
        if sqlite_path and sqlite_path.exists():
            _reset_sqlite_db(sqlite_path)
            _run_manage_command("migrate", "--no-input")
        else:
            _run_manage_command("migrate", "--no-input")
            _run_manage_command("flush", "--no-input")
            _run_manage_command("migrate", "--no-input")
        _run_manage_command("loaddata", str(seed_path))
        _run_manage_command("create_dev_admin")
    except Exception as exc:  # pragma: no cover - operational safeguard
        messages.error(request, f"Reset from seed failed: {exc}")
    else:
        messages.success(request, "Database reset from seed_full.json.")
    response = redirect("setup:setup")
    _discard_session(request, response)
    return response


@login_required
@user_passes_test(setup_access_required)
def seed_clear(request):
    try:
        sqlite_path = _sqlite_db_file()
        if sqlite_path and sqlite_path.exists():
            _reset_sqlite_db(sqlite_path)
            _run_manage_command("migrate", "--no-input")
        else:
            _run_manage_command("migrate", "--no-input")
            _run_manage_command("flush", "--no-input")
            _run_manage_command("migrate", "--no-input")
        _run_manage_command("create_dev_admin")
    except Exception as exc:  # pragma: no cover - operational safeguard
        messages.error(request, f"Database clear failed: {exc}")
    else:
        messages.success(request, "Database cleared. Fresh schema applied (dev admin ensured).")
    response = redirect("setup:setup")
    _discard_session(request, response)
    return response


@login_required
@user_passes_test(setup_access_required)
def tunnel_start(request):
    target = getattr(settings, "CLOUDFLARE_TUNNEL_URL", "http://127.0.0.1:8000")
    try:
        url = tunnel_manager.start_tunnel(target)
    except Exception as exc:  # pragma: no cover - operational safeguard
        messages.error(request, f"Could not start Cloudflare tunnel: {exc}")
    else:
        settings_obj = SiteSettings.get_solo()
        if settings_obj.dev_login_enabled:
            settings_obj.dev_login_enabled = False
            settings_obj.save(update_fields=["dev_login_enabled"])
            messages.info(request, "Dev login shortcut disabled while tunnel is active.")
        messages.success(
            request,
            mark_safe(f'Tunnel ready: <a href="{url}" target="_blank" rel="noopener">{url}</a>'),
        )
    return redirect("setup:setup")


@login_required
@user_passes_test(setup_access_required)
def tunnel_stop(request):
    if tunnel_manager.stop_tunnel():
        messages.success(request, "Cloudflare tunnel stopped.")
    else:
        messages.info(request, "No tunnel was running.")
    return redirect("setup:setup")


@login_required
@user_passes_test(setup_access_required)
def visibility_list(request):
    q = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "key")
    direction = request.GET.get("dir", "asc")

    rules = VisibilityRule.objects.all()

    if q:
        rules = rules.filter(Q(key__icontains=q) | Q(label__icontains=q) | Q(notes__icontains=q))

    rules = rules.annotate(first_dot=StrIndex(F("key"), Value(".")))
    rules = rules.annotate(after_first=Substr(F("key"), F("first_dot") + 1))
    rules = rules.annotate(second_rel=StrIndex(F("after_first"), Value(".")))
    rules = rules.annotate(
        group_name=Case(
            When(second_rel__gt=1, then=Substr(F("key"), F("first_dot") + 1, F("second_rel") - 1)),
            default=Value(""),
            output_field=CharField(),
        )
    )

    allowed_sorts = {"key", "label", "is_enabled", "notes", "group"}  # add "group"

    if sort not in allowed_sorts:
        sort = "key"

    # map "group" to the annotation name "group_name"
    sort_field = "group_name" if sort == "group" else sort
    sort_expr = f"-{sort_field}" if direction == "desc" else sort_field

    rules = rules.order_by(sort_expr, "key")  # stable tiebreak

    ctx = {"rules": rules, "q": q, "sort": sort, "direction": direction}

    if request.headers.get("HX-Request") == "true":
        return render(request, "setup/_visibility_table.html", ctx)

    return render(request, "setup/visibility_list.html", ctx)


@login_required
@user_passes_test(setup_access_required)
def visibility_edit(request):
    key = request.GET.get("key", "")
    label = request.GET.get("label", "")
    instance = VisibilityRule.objects.filter(key=key).first()
    if request.method == "POST":
        form = VisibilityRuleForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Visibility saved.")
            return redirect("setup:visibility_list")
    else:
        form = (
            VisibilityRuleForm(instance=instance)
            if instance
            else VisibilityRuleForm(initial={"key": key, "label": label})
        )
    return render(request, "setup/visibility_edit.html", {"form": form})


@login_required
@user_passes_test(setup_access_required)
def visibility_delete(request, rule_id):
    rule = get_object_or_404(VisibilityRule, id=rule_id)
    rule.delete()
    messages.success(request, "Visibility rule deleted.")
    return redirect("setup:visibility_list")


@login_required
@user_passes_test(setup_access_required)
@require_http_methods(["GET", "POST"])
def visibility_picker(request):
    """
    HTMX popover with role checkboxes for a visibility key.
    - GET: render the popover
    - POST: update allowed_groups, re-render (with 'saved' tick)
    """
    key = (request.GET.get("key") or request.POST.get("key") or "").strip()
    label = (request.GET.get("label") or request.POST.get("label") or "").strip()
    if not key:
        return HttpResponseBadRequest("Missing key")

    rule, _ = VisibilityRule.objects.get_or_create(key=key, defaults={"label": label or key})
    all_groups = Group.objects.all().order_by("name")

    if request.method == "POST":
        selected = request.POST.getlist("groups")
        rule.allowed_groups.set(Group.objects.filter(id__in=selected))
        is_disabled = request.POST.get("is_disabled")
        rule.is_enabled = not bool(is_disabled)
        rule.save()
        saved = True
    else:
        saved = False

    html = render_to_string(
        "setup/visibility_picker.html",
        {
            "rule": rule,
            "all_groups": all_groups,
            "saved": saved,
            "label": rule.label or label or key,
            "key": key,
        },
        request=request,
    )
    return HttpResponse(html)


@login_required
@user_passes_test(setup_access_required)
def visibility_disabled(request):
    """
    List of disabled visibility entries with a quick enable action.
    """
    rules = VisibilityRule.objects.filter(is_enabled=False).order_by("label", "key")
    if request.method == "POST":
        rule_id = request.POST.get("rule_id")
        rule = get_object_or_404(VisibilityRule, id=rule_id)
        rule.is_enabled = True
        rule.save()
        messages.success(request, f"Re-enabled {rule.label or rule.key}.")
        return redirect("setup:visibility_disabled")

    return render(
        request,
        "setup/visibility_disabled.html",
        {"rules": rules},
    )
