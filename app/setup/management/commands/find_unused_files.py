# app/setup/management/commands/find_unused_files.py
import ast
import fnmatch
import os
import re
import shutil
import sys
from collections import defaultdict, deque
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser

# -----------------------------
# Helpers & defaults
# -----------------------------

PY_EXCLUDES = {
    "__pycache__",
}
DIR_EXCLUDES = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "node_modules",
}
FILE_EXCLUDE_GLOBS = [
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.map",
    "*.lock",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
]
DEFAULT_TRASH_ROOT = ".project_trash"

# Regexes for template & static references in files
RE_RENDER_TEMPLATE = re.compile(
    r"""(?:render\s*\(\s*[^,]+,\s*["']([^"']+)["'])|
        (?:get_template\s*\(\s*["']([^"']+)["'])|
        (?:TemplateResponse\s*\(\s*[^,]+,\s*["']([^"']+)["'])""",
    re.VERBOSE,
)
RE_DJANGO_STATIC_TAG = re.compile(r"""{%\s*static\s+['"]([^'"]+)['"]\s*%}""")
RE_DJANGO_STATIC_FUNC = re.compile(r"""static\s*\(\s*['"]([^'"]+)['"]\s*\)""")
RE_TEMPLATE_EXTENDS = re.compile(r"""{%\s*extends\s+['"]([^'"]+)['"]\s*%}""")
RE_TEMPLATE_INCLUDE = re.compile(r"""{%\s*include\s+['"]([^'"]+)['"]\s*%}""")
RE_CSS_URL = re.compile(r"""url\(\s*['"]?([^'")]+)['"]?\s*\)""")


def norm(p: Path) -> Path:
    return p.resolve()


def within(root: Path, p: Path) -> bool:
    try:
        p.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def is_excluded_dir(name: str) -> bool:
    return name in DIR_EXCLUDES or name in PY_EXCLUDES


def glob_any(name: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


# -----------------------------
# Project scan
# -----------------------------


class ProjectScanner:
    def __init__(
        self,
        project_root: Path,
        apps_root: Path | None,
        include: list[str],
        exclude: list[str],
    ):
        self.project_root = norm(project_root)
        self.apps_root = norm(apps_root) if apps_root else None
        self.include = include or []
        self.exclude = exclude or []

        # Discover roots
        self.template_dirs: list[Path] = []
        for eng in getattr(settings, "TEMPLATES", []):
            for d in eng.get("DIRS", []):
                self.template_dirs.append(norm(Path(d)))
        # Add app template dirs (app/templates) implicitly by scanning installed apps
        self.app_template_dirs: list[Path] = []
        for app in settings.INSTALLED_APPS:
            try:
                __import__(app.split(".")[0])
            except Exception:
                continue
            # Attempt to locate package path
            try:
                pkg_path = Path(sys.modules[app.split(".")[0]].__file__).parent
            except Exception:
                continue
            tdir = pkg_path / "templates"
            if tdir.exists():
                self.app_template_dirs.append(norm(tdir))

        self.static_dirs: list[Path] = []
        # STATICFILES_DIRS (additional)
        for d in getattr(settings, "STATICFILES_DIRS", []):
            self.static_dirs.append(norm(Path(d)))
        # App static dirs
        self.app_static_dirs: list[Path] = []
        for app in settings.INSTALLED_APPS:
            try:
                __import__(app.split(".")[0])
            except Exception:
                continue
            try:
                pkg_path = Path(sys.modules[app.split(".")[0]].__file__).parent
            except Exception:
                continue
            sdir = pkg_path / "static"
            if sdir.exists():
                self.app_static_dirs.append(norm(sdir))

        # Code roots: either apps_root, or heuristic: folders that contain manage.py siblings: "app", project pkg, etc.
        if self.apps_root:
            self.code_roots = [self.apps_root]
        else:
            guess = []
            for cand in ("app", "apps", "src"):
                p = self.project_root / cand
                if p.exists():
                    guess.append(p)
            # also include sibling packages that hold settings.py
            for child in self.project_root.iterdir():
                if child.is_dir() and (child / "settings.py").exists():
                    guess.append(child)
            self.code_roots = [norm(p) for p in guess if p.exists()]

        # Collected sets
        self.all_py_modules: set[Path] = set()
        self.referenced_modules: set[Path] = set()

        self.all_templates: set[Path] = set()
        self.referenced_templates: set[Path] = set()

        self.all_static_files: set[Path] = set()
        self.referenced_static_files: set[Path] = set()

        # Map logical template name -> file path(s)
        self.template_name_to_paths: dict[str, list[Path]] = defaultdict(list)
        # Common static prefixes to resolve logical path to files
        self.static_roots: list[Path] = list({*self.static_dirs, *self.app_static_dirs})

    # ---------- file collection ----------

    def collect_python_files(self) -> list[Path]:
        files: list[Path] = []
        for root in (self.apps_root or self.project_root,):
            for dpath, dnames, fnames in os.walk(root):
                # prune excluded dirs
                dnames[:] = [d for d in dnames if not is_excluded_dir(d)]
                dpath_p = Path(dpath)
                if not within(self.project_root, dpath_p):
                    continue
                for fn in fnames:
                    if glob_any(fn, FILE_EXCLUDE_GLOBS):
                        continue
                    if not fn.endswith(".py"):
                        continue
                    p = dpath_p / fn
                    if self._included(p):
                        files.append(p)
        self.all_py_modules = set(map(norm, files))
        return files

    def collect_template_files(self) -> list[Path]:
        bases = list({*self.template_dirs, *self.app_template_dirs})
        files: list[Path] = []
        for base in bases:
            if not base.exists():
                continue
            for dpath, dnames, fnames in os.walk(base):
                dnames[:] = [d for d in dnames if not is_excluded_dir(d)]
                dpath_p = Path(dpath)
                for fn in fnames:
                    if glob_any(fn, FILE_EXCLUDE_GLOBS):
                        continue
                    if not fn.endswith((".html", ".txt", ".jinja", ".jinja2")):
                        continue
                    p = dpath_p / fn
                    if self._included(p):
                        files.append(p)
                        # Build logical template name (relative to base)
                        rel = p.relative_to(base).as_posix()
                        self.template_name_to_paths[rel].append(norm(p))
        self.all_templates = set(map(norm, files))
        return files

    def collect_static_files(self) -> list[Path]:
        files: list[Path] = []
        for base in self.static_roots:
            if not base.exists():
                continue
            for dpath, dnames, fnames in os.walk(base):
                dnames[:] = [d for d in dnames if not is_excluded_dir(d)]
                dpath_p = Path(dpath)
                for fn in fnames:
                    if glob_any(fn, FILE_EXCLUDE_GLOBS):
                        continue
                    p = dpath_p / fn
                    if self._included(p):
                        files.append(p)
        self.all_static_files = set(map(norm, files))
        return files

    def _included(self, p: Path) -> bool:
        rel = p.as_posix()
        if self.include and not glob_any(rel, self.include):
            return False
        if self.exclude and glob_any(rel, self.exclude):
            return False
        # Also exclude migrations by default
        return not ("migrations" in rel and rel.endswith(".py"))

    # ---------- reference discovery ----------

    def discover_python_import_graph(self, py_files: Iterable[Path]) -> None:
        """
        Mark referenced Python modules by following imports starting from entry points.
        Entry points:
          - manage.py siblings: project settings, wsgi.py, asgi.py
          - INSTALLED_APPS packages
        """
        # Build map of module name -> file path for your code roots
        module_index: dict[str, Path] = {}
        for f in py_files:
            try:
                pkg_rel = f.relative_to(self.project_root).with_suffix("")
            except Exception:
                continue
            # Turn path to dotted module (rough heuristic)
            parts = list(pkg_rel.parts)
            if parts and parts[-1] == "__init__":
                parts = parts[:-1]
            dotted = ".".join(parts)
            if dotted:
                module_index[dotted] = norm(f)

        # Build reverse index by filename for resolving relative imports
        path_index = {norm(v): k for k, v in module_index.items()}

        def parse_imports(file_path: Path) -> set[str]:
            names: set[str] = set()
            try:
                src = file_path.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(src, filename=str(file_path))
            except Exception:
                return names
            mod_name = path_index.get(norm(file_path), "")
            pkg_base = mod_name.rsplit(".", 1)[0] if "." in mod_name else ""
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for n in node.names:
                        names.add(n.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.level and pkg_base:
                        # relative import: resolve to absolute
                        base_parts = pkg_base.split(".")
                        rel_up = node.level - 1
                        if rel_up > 0:
                            base_parts = base_parts[:-rel_up]
                        target = ".".join([*base_parts, node.module or ""]).strip(".")
                        if target:
                            names.add(target)
                    elif node.module:
                        names.add(node.module)
            return names

        # Entry points: installed apps + project packages near manage.py + wsgi/asgi/settings/urls
        entry_modules: set[str] = set()
        # INSTALLED_APPS (top-level package names)
        for app in settings.INSTALLED_APPS:
            entry_modules.add(app)
        # common project modules
        for name in ("settings", "urls", "wsgi", "asgi"):
            for k in list(module_index.keys()):
                if k.endswith(f".{name}"):
                    entry_modules.add(k.rsplit(f".{name}", 1)[0])
                    entry_modules.add(k)

        # BFS walk imports
        visited: set[str] = set()
        q = deque(entry_modules)

        while q:
            mod = q.popleft()
            if mod in visited:
                continue
            visited.add(mod)

            # Resolve module -> file
            # Try exact; try adding __init__ by probing module_index keys that start with mod
            file = module_index.get(mod)
            if not file:
                # try submodules (we only care about your code graph)
                for k in module_index:
                    if k == mod or k.startswith(mod + "."):
                        file = module_index[k]
                        break
            if not file:
                continue

            self.referenced_modules.add(norm(file))

            # Parse and enqueue imports
            for imp in parse_imports(file):
                # Only follow into your project space
                for k in module_index:
                    if k == imp or k.startswith(imp + "."):
                        q.append(k)

        # Also mark __init__.py next to referenced files to avoid false positives
        for f in list(self.referenced_modules):
            init = f.parent / "__init__.py"
            if init.exists():
                self.referenced_modules.add(norm(init))

    def discover_template_references(
        self, py_files: Iterable[Path], template_files: Iterable[Path]
    ) -> None:
        # from Python: render/get_template/TemplateResponse
        referenced_names: set[str] = set()
        for f in py_files:
            try:
                src = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in RE_RENDER_TEMPLATE.finditer(src):
                for g in m.groups():
                    if g:
                        referenced_names.add(g)

        # resolve names to files via template dirs
        def resolve_template_name(name: str) -> list[Path]:
            hits = []
            for base in [*self.template_dirs, *self.app_template_dirs]:
                p = base / name
                if p.exists():
                    hits.append(norm(p))
            # also see prebuilt index
            hits += self.template_name_to_paths.get(name, [])
            # dedupe
            seen = set()
            uniq = []
            for h in hits:
                if h not in seen:
                    uniq.append(h)
                    seen.add(h)
            return uniq

        # seed queue with directly-referenced templates
        q = deque()
        for name in referenced_names:
            for p in resolve_template_name(name):
                q.append(p)
                self.referenced_templates.add(norm(p))

        # follow extends / include edges
        def template_edges(p: Path) -> list[str]:
            try:
                src = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                return []
            names = []
            for r in (RE_TEMPLATE_EXTENDS, RE_TEMPLATE_INCLUDE):
                names += [m.group(1) for m in r.finditer(src)]
            return names

        while q:
            t = q.popleft()
            for name in template_edges(t):
                for hit in resolve_template_name(name):
                    if hit not in self.referenced_templates:
                        self.referenced_templates.add(hit)
                        q.append(hit)

    def discover_static_references(
        self, py_files: Iterable[Path], template_files: Iterable[Path]
    ) -> None:
        referenced_paths: set[str] = set()

        def scan_text_for_static(src: str):
            for m in RE_DJANGO_STATIC_TAG.finditer(src):
                referenced_paths.add(m.group(1))
            for m in RE_DJANGO_STATIC_FUNC.finditer(src):
                referenced_paths.add(m.group(1))
            # css url()
            for m in RE_CSS_URL.finditer(src):
                url = m.group(1).strip()
                if url.startswith(("data:", "http:", "https:", "//")):
                    continue
                # basic ignore for #hash or ?query
                url = url.split("#", 1)[0].split("?", 1)[0]
                if url:
                    referenced_paths.add(url)

        # templates and css/js
        for f in list(template_files):
            try:
                src = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            scan_text_for_static(src)

        for f in list(py_files):
            if f.suffix != ".py":
                continue
            try:
                src = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            scan_text_for_static(src)

        # resolve referenced logical paths to actual files in static dirs
        for rel in referenced_paths:
            for base in self.static_roots:
                p = base / rel
                if p.exists():
                    self.referenced_static_files.add(norm(p))

    # -----------------------------
    # Report & move
    # -----------------------------

    def compute_unused(self) -> tuple[set[Path], set[Path], set[Path]]:
        unused_py = {norm(p) for p in self.all_py_modules if norm(p) not in self.referenced_modules}
        # Filter out __init__.py files that are often empty yet structurally needed
        unused_py = {p for p in unused_py if p.name != "__init__.py"}

        unused_tpl = {
            norm(p) for p in self.all_templates if norm(p) not in self.referenced_templates
        }
        unused_static = {
            norm(p) for p in self.all_static_files if norm(p) not in self.referenced_static_files
        }
        return unused_py, unused_tpl, unused_static

    def move_to_trash(self, files: Iterable[Path], trash_root: Path) -> list[tuple[Path, Path]]:
        moved: list[tuple[Path, Path]] = []
        for f in files:
            # compute relative to project_root when possible
            try:
                rel = f.resolve().relative_to(self.project_root)
            except Exception:
                rel = f.name
            dst = trash_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                # avoid overwrite by appending counter
                base = dst
                i = 1
                while dst.exists():
                    dst = base.with_name(base.stem + f".{i}" + base.suffix)
                    i += 1
            shutil.move(str(f), str(dst))
            moved.append((f, dst))
        return moved


class Command(BaseCommand):
    help = "Find (and optionally move) project files that appear unused (best-effort)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--apps-root",
            default="",
            help="Limit code scan to this directory (e.g. app/). Defaults to project root.",
        )
        parser.add_argument(
            "--include",
            action="append",
            default=[],
            help="Glob(s) to include (relative paths). Can repeat.",
        )
        parser.add_argument(
            "--exclude", action="append", default=[], help="Glob(s) to exclude. Can repeat."
        )
        parser.add_argument(
            "--move",
            action="store_true",
            help="If set, move unused files into a recycle bin folder.",
        )
        parser.add_argument(
            "--trash-dir",
            default=DEFAULT_TRASH_ROOT,
            help=f"Recycle bin root (default: {DEFAULT_TRASH_ROOT})",
        )

    def handle(self, *args, **opts):
        project_root = Path.cwd()
        apps_root = Path(opts["apps_root"]).resolve() if opts.get("apps_root") else None
        include = opts.get("include") or []
        exclude = opts.get("exclude") or []

        scanner = ProjectScanner(project_root, apps_root, include, exclude)

        self.stdout.write(self.style.HTTP_INFO("Collecting files..."))
        py_files = scanner.collect_python_files()
        tpl_files = scanner.collect_template_files()
        scanner.collect_static_files()

        self.stdout.write(self.style.HTTP_INFO("Discovering references (Python graph)..."))
        scanner.discover_python_import_graph(py_files)
        self.stdout.write(self.style.HTTP_INFO("Discovering references (templates)..."))
        scanner.discover_template_references(py_files, tpl_files)
        self.stdout.write(self.style.HTTP_INFO("Discovering references (static assets)..."))
        scanner.discover_static_references(py_files, tpl_files)

        unused_py, unused_tpl, unused_static = scanner.compute_unused()

        self.stdout.write("")
        self.stdout.write(
            self.style.MIGRATE_HEADING("Possibly unused Python modules: ") + str(len(unused_py))
        )
        for p in sorted(unused_py):
            self.stdout.write(f"  - {p.relative_to(project_root)}")
        self.stdout.write("")
        self.stdout.write(
            self.style.MIGRATE_HEADING("Possibly unused templates: ") + str(len(unused_tpl))
        )
        for p in sorted(unused_tpl):
            self.stdout.write(f"  - {p.relative_to(project_root)}")
        self.stdout.write("")
        self.stdout.write(
            self.style.MIGRATE_HEADING("Possibly unused static files: ") + str(len(unused_static))
        )
        for p in sorted(unused_static):
            self.stdout.write(f"  - {p.relative_to(project_root)}")

        if opts.get("move"):
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            trash_root = (project_root / opts["trash_dir"] / ts).resolve()
            self.stdout.write("")
            self.stdout.write(self.style.WARNING(f"Moving files to: {trash_root}"))
            moved_all: list[tuple[Path, Path]] = []
            moved_all += scanner.move_to_trash(unused_py, trash_root)
            moved_all += scanner.move_to_trash(unused_tpl, trash_root)
            moved_all += scanner.move_to_trash(unused_static, trash_root)
            self.stdout.write(self.style.SUCCESS(f"Moved {len(moved_all)} files into recycle bin"))
            self.stdout.write(
                self.style.HTTP_INFO(
                    "You can restore files by moving them back from the trash directory."
                )
            )
        else:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    "Dry run only. Use --move to actually relocate files into a recycle bin."
                )
            )
            self.stdout.write(
                self.style.HTTP_INFO(
                    "Tip: run your test suite and key pages after a move to catch anything missed."
                )
            )
