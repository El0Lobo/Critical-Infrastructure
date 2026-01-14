# app/assets/views.py
import contextlib
import mimetypes
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.http import (
    FileResponse,
    Http404,
    HttpResponseForbidden,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from app.setup.helpers import is_allowed
from app.setup.models import VisibilityRule

from .forms import AssetCreateForm, CollectionForm, TagForm
from .models import VISIBILITY_MODE_CHOICES, Asset, Collection, Tag
from .selectors import (
    filter_assets_for_user,
    filter_assets_with_form,
    user_allowed_for,
    user_can_view_asset,
    user_group_ids,
)

# ---------- index -------------------------------------------------------------


@login_required
def _handle_create_action(request):
    """Handle POST actions for creating assets, collections, or tags."""
    action = (request.POST.get("action") or "create_asset").strip()

    if action == "create_collection":
        if not user_allowed_for(request.user, "cms.assets.add_collection"):
            return None, None, None, HttpResponseForbidden("Not allowed")
        collection_form = CollectionForm(request.POST)
        if collection_form.is_valid():
            collection_form.save()
            return None, None, None, HttpResponseRedirect(reverse("assets:index"))
        return None, collection_form, None, None

    elif action == "create_tag":
        if not user_allowed_for(request.user, "cms.assets.add_tag"):
            return None, None, None, HttpResponseForbidden("Not allowed")
        tag_form = TagForm(request.POST)
        if tag_form.is_valid():
            tag_form.save()
            return None, None, None, HttpResponseRedirect(reverse("assets:index"))
        return None, None, tag_form, None

    else:  # create_asset
        if not user_allowed_for(request.user, "cms.assets.add_asset"):
            return None, None, None, HttpResponseForbidden("Not allowed")
        create_form = AssetCreateForm(request.POST, request.FILES)
        if create_form.is_valid():
            if not create_form.cleaned_data.get("appears_on"):
                create_form.instance.appears_on = request.GET.get("appears_on") or ""
            create_form.save()
            return None, None, None, HttpResponseRedirect(reverse("assets:index"))
        return create_form, None, None, None


def _apply_asset_sorting(queryset, request):
    """Apply sorting to asset queryset based on request parameters."""
    sort = request.GET.get("sort") or "-updated"
    sort_map = {
        "title": "title",
        "-title": "-title",
        "kind": "kind",
        "-kind": "-kind",
        "updated": "updated_at",
        "-updated": "-updated_at",
        "created": "created_at",
        "-created": "-created_at",
    }
    return queryset.order_by(sort_map.get(sort, "-updated_at"))


def _is_any_filter_active(filter_form):
    """Check if any filter is actively applied beyond defaults."""
    if not filter_form.is_valid():
        return False
    cd = filter_form.cleaned_data
    return any(
        [
            bool((cd.get("q") or "").strip()),
            bool(cd.get("kind")),
            bool(cd.get("visibility")),
            bool(cd.get("collection")),
            bool(cd.get("tags") and cd.get("tags").count() > 0),
            bool(cd.get("source")),
            bool(cd.get("referenced")),
        ]
    )


def _build_collection_hierarchy(all_collections, assets_by_col, filter_active):
    """Build parent-child hierarchy maps for collections."""
    by_id = {c.id: c for c in all_collections}
    parent_of = {c.id: (c.parent_id or None) for c in all_collections}
    children_of = {}
    for c in all_collections:
        children_of.setdefault(c.parent_id, []).append(c.id)

    # Determine which collections to include
    include_ids = set()
    if not filter_active:
        include_ids = set(by_id.keys())
    else:
        hit_cols = {col_id for col_id, items in assets_by_col.items() if col_id and items}
        include_ids.update(hit_cols)
        # Add ancestors
        for cid in list(hit_cols):
            p = parent_of.get(cid)
            while p is not None and p not in include_ids:
                include_ids.add(p)
                p = parent_of.get(p)

    return by_id, parent_of, children_of, include_ids


def _prune_collections_for_user(request, by_id, include_ids):
    """Prune collections based on user permissions."""
    if request.user.is_superuser:
        return include_ids

    user_groups = user_group_ids(request.user)

    def col_access(c):
        vm = c.visibility_mode
        if vm == "public":
            return True
        if not request.user.is_authenticated:
            return False
        if vm == "internal":
            return True
        if vm == "groups":
            allowed = set(c.allowed_groups.values_list("id", flat=True))
            return bool(user_groups & allowed)
        return False

    def rule_allows_col(cid):
        try:
            key_base = f"assets.collection.{cid}"
            act_key = f"cms.assets.collection.{cid}.actions"
            tool_key = f"cms.assets.collection.{cid}.toolbar"

            def allowed(key):
                return VisibilityRule.objects.filter(
                    key=key, is_enabled=True
                ).exists() and is_allowed(request.user, key)

            base_exists = VisibilityRule.objects.filter(key=key_base, is_enabled=True).exists()
            if base_exists:
                return is_allowed(request.user, key_base)
            return col_access(by_id[cid]) or allowed(act_key) or allowed(tool_key)
        except Exception:
            return False

    return {cid for cid in include_ids if cid in by_id and rule_allows_col(cid)}


def _build_collection_tree(by_id, parent_of, children_of, include_ids, assets_by_col):
    """Build nested tree structure from collection hierarchy."""

    def build_node(cid):
        c = by_id[cid]
        node = {
            "col": c,
            "assets": assets_by_col.get(c.id, []),
            "children": [],
        }
        for child_id in children_of.get(c.id, []):
            if child_id in include_ids:
                node["children"].append(build_node(child_id))
        return node

    roots = [cid for cid, pid in parent_of.items() if pid is None and cid in include_ids]
    return [build_node(cid) for cid in roots]


def _initialize_asset_forms(request, filter_form, create_form, collection_form, tag_form):
    """Initialize forms for asset creation interface."""
    if create_form is None:
        initial_asset = {}
        if filter_form.is_valid():
            selected_collection = filter_form.cleaned_data.get("collection")
            if selected_collection:
                initial_asset["collection"] = selected_collection
        initial_asset["appears_on"] = request.GET.get("appears_on") or ""
        create_form = AssetCreateForm(initial=initial_asset)

    if collection_form is None:
        initial_col = {}
        if filter_form.is_valid():
            selected_collection = filter_form.cleaned_data.get("collection")
            if selected_collection:
                initial_col["parent"] = selected_collection
        collection_form = CollectionForm(initial=initial_col)

    if tag_form is None:
        tag_form = TagForm()

    return create_form, collection_form, tag_form


def assets_index(request):
    """Display and manage assets with filtering, sorting, and hierarchical organization."""
    # Page-level visibility check
    if not is_allowed(request.user, "cms.assets.page"):
        return HttpResponseForbidden("You do not have access to this page.")

    create_form = collection_form = tag_form = None

    # Handle POST actions
    if request.method == "POST":
        create_form, collection_form, tag_form, response = _handle_create_action(request)
        if response:
            return response

    # Filter and sort assets
    filter_form, qs = filter_assets_with_form(request.GET or None)
    qs = filter_assets_for_user(qs, request.user)
    qs = _apply_asset_sorting(qs, request)

    # Build collection tree
    all_collections = (
        Collection.objects.select_related("parent")
        .prefetch_related("tags", "allowed_groups")
        .order_by("parent__id", "sort_order", "title")
    )

    # Map assets to their collections
    assets_by_col = {}
    for a in qs:
        assets_by_col.setdefault(a.collection_id, []).append(a)

    # Build hierarchy and apply filters
    filter_active = _is_any_filter_active(filter_form)
    by_id, parent_of, children_of, include_ids = _build_collection_hierarchy(
        all_collections, assets_by_col, filter_active
    )
    include_ids = _prune_collections_for_user(request, by_id, include_ids)
    tree = _build_collection_tree(by_id, parent_of, children_of, include_ids, assets_by_col)

    # Initialize forms
    create_form, collection_form, tag_form = _initialize_asset_forms(
        request, filter_form, create_form, collection_form, tag_form
    )

    # Prepare context
    view_mode = request.GET.get("view") or "grid"
    compact = request.GET.get("compact") == "1"
    all_groups = Group.objects.all().order_by("name")

    ctx = {
        "form": filter_form,
        "create_form": create_form,
        "collection_form": collection_form,
        "tag_form": tag_form,
        "tree": tree,
        "all_collections": list(all_collections),
        "view_mode": view_mode,
        "compact": compact,
        "VISIBILITY_MODE_CHOICES": dict(VISIBILITY_MODE_CHOICES),
        "all_groups": all_groups,
    }
    return render(request, "assets/index.html", ctx)


# ---------- Asset inline ops --------------------------------------------------


@login_required
@require_POST
def asset_toggle_visibility(request, pk):
    a = get_object_or_404(Asset, pk=pk)
    if not user_allowed_for(request.user, f"cms.assets.asset.{a.id}.actions"):
        return JsonResponse({"ok": False, "error": "Not allowed"}, status=403)
    a.visibility = "public" if a.effective_visibility in ("internal", "groups") else "internal"
    a.save()
    return JsonResponse({"ok": True, "visibility": a.effective_visibility})


@login_required
@require_POST
def asset_rename(request, pk):
    a = get_object_or_404(Asset, pk=pk)
    if not user_allowed_for(request.user, f"cms.assets.asset.{a.id}.actions"):
        return JsonResponse({"ok": False, "error": "Not allowed"}, status=403)

    new_title = (request.POST.get("title") or "").strip()
    new_slug = (request.POST.get("slug") or "").strip()
    changed = False
    if new_title and new_title != a.title:
        a.title = new_title
        changed = True
    if new_slug and new_slug != a.slug:
        a.slug = new_slug
        changed = True
    if changed:
        a.save()
    return JsonResponse({"ok": True, "title": a.title, "slug": a.slug})


@login_required
def asset_data(request, pk):
    a = get_object_or_404(
        Asset.objects.select_related("collection").prefetch_related("tags"), pk=pk
    )
    if not user_allowed_for(request.user, f"cms.assets.asset.{a.id}.actions"):
        return JsonResponse({"ok": False, "error": "Not allowed"}, status=403)
    data = {
        "id": a.id,
        "title": a.title or "",
        "slug": a.slug or "",
        "visibility": a.visibility,
        "description": a.description or "",
        "collection": a.collection_id,
        "tags": list(a.tags.values_list("id", flat=True)),
        "url": a.url or "",
        "text_content": a.text_content or "",
        "has_file": bool(a.file),
        "file_url": (a.file.url if a.file else ""),
    }
    return JsonResponse({"ok": True, "asset": data})


@login_required
@require_POST
def asset_update(request, pk):
    a = get_object_or_404(Asset, pk=pk)
    if not user_allowed_for(request.user, f"cms.assets.asset.{a.id}.actions"):
        return JsonResponse({"ok": False, "error": "Not allowed"}, status=403)

    a.title = (request.POST.get("title") or a.title).strip()
    slug = (request.POST.get("slug") or "").strip()
    if slug:
        a.slug = slug
    a.visibility = request.POST.get("visibility") or a.visibility
    a.description = request.POST.get("description") or ""

    col_id = request.POST.get("collection")
    if col_id:
        with contextlib.suppress(ValueError):
            a.collection_id = int(col_id)

    tag_ids = request.POST.getlist("tags")
    if tag_ids:
        a.save()
        a.tags.set(Tag.objects.filter(id__in=tag_ids))

    new_file = request.FILES.get("file")
    new_url = (request.POST.get("url") or "").strip()
    new_text = (request.POST.get("text_content") or "").strip()
    provided = sum([1 if new_file else 0, 1 if new_url else 0, 1 if new_text else 0])
    if provided > 1:
        return JsonResponse(
            {"ok": False, "error": "Provide at most one source (file OR url OR text)."}, status=400
        )
    if provided == 1:
        if new_file:
            a.file = new_file
            a.url = ""
            a.text_content = ""
        elif new_url:
            a.url = new_url
            a.file = None
            a.text_content = ""
        else:
            a.text_content = new_text
            a.file = None
            a.url = ""

    a.save()
    if request.headers.get("Hx-Request"):
        return JsonResponse({"ok": True})
    return HttpResponseRedirect(reverse("assets:index"))


@login_required
@require_POST
def asset_delete(request, pk):
    a = get_object_or_404(Asset, pk=pk)
    if not user_allowed_for(request.user, f"cms.assets.asset.{a.id}.actions"):
        return JsonResponse({"ok": False, "error": "Not allowed"}, status=403)
    a.delete()
    return JsonResponse({"ok": True})


# ---------- Collection inline ops --------------------------------------------


@login_required
@require_POST
def collection_toggle_visibility(request, pk):
    c = get_object_or_404(Collection, pk=pk)
    if not user_allowed_for(request.user, f"cms.assets.collection.{c.id}.actions"):
        return JsonResponse({"ok": False, "error": "Not allowed"}, status=403)
    c.visibility_mode = "public" if c.visibility_mode != "public" else "internal"
    c.save()
    return JsonResponse({"ok": True, "visibility": c.visibility_mode})


@login_required
@require_POST
def collection_rename(request, pk):
    c = get_object_or_404(Collection, pk=pk)
    if not user_allowed_for(request.user, f"cms.assets.collection.{c.id}.actions"):
        return JsonResponse({"ok": False, "error": "Not allowed"}, status=403)
    new_title = (request.POST.get("title") or "").strip()
    new_slug = (request.POST.get("slug") or "").strip()
    changed = False
    if new_title and new_title != c.title:
        c.title = new_title
        changed = True
    if new_slug and new_slug != c.slug:
        c.slug = new_slug
        changed = True
    if changed:
        c.save()
    return JsonResponse({"ok": True, "title": c.title, "slug": c.slug})


@login_required
@require_POST
def collection_update(request, pk):
    c = get_object_or_404(Collection, pk=pk)
    if not user_allowed_for(request.user, f"cms.assets.collection.{c.id}.actions"):
        return JsonResponse({"ok": False, "error": "Not allowed"}, status=403)
    form = CollectionForm(request.POST, instance=c)
    if form.is_valid():
        form.save()
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)


@login_required
@require_POST
def collection_delete(request, pk):
    col = get_object_or_404(Collection, pk=pk)
    if not user_allowed_for(request.user, f"cms.assets.collection.{col.id}.actions"):
        return JsonResponse({"ok": False, "error": "Not allowed"}, status=403)
    col.delete()
    return JsonResponse({"ok": True})


# ---------- PROTECTED FILE SERVING -------------------------------------------


def asset_file(request, pk):
    """
    Gate access to the actual file by visibility + user.
    Use ?dl=1 to force download (attachment); otherwise inline.
    """
    a = get_object_or_404(Asset.objects.select_related("collection"), pk=pk)

    if not a.file:
        raise Http404("No file on this asset.")

    if not user_can_view_asset(request.user, a):
        # If not logged in, send to login page with return
        if not request.user.is_authenticated:
            login_url = settings.LOGIN_URL if hasattr(settings, "LOGIN_URL") else "/accounts/login/"
            next_url = request.get_full_path()
            return HttpResponseRedirect(f"{login_url}?next={next_url}")
        # Logged in but not allowed
        return HttpResponseForbidden("You do not have access to this file.")

    # Serve securely via Django (streaming); for production prefer X-Accel-Redirect / X-Sendfile
    mime, _ = mimetypes.guess_type(a.file.name)
    mime = mime or "application/octet-stream"
    fh = a.file.open("rb")
    resp = FileResponse(fh, content_type=mime)

    filename = os.path.basename(a.file.name)
    download = request.GET.get("dl") in ("1", "true", "yes", "download", "attachment")
    disp = "attachment" if download else "inline"
    resp["Content-Disposition"] = f'{disp}; filename="{filename}"'
    resp["Cache-Control"] = "private, max-age=0, no-cache, no-store"
    return resp
