import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR / "config"
CONFIG_FILE = CONFIG_DIR / "site.json"

DEFAULTS = {
    "profile_type": "venue",  # 'venue' | 'band' | 'news'
    "public_theme": "theme_a",  # 'theme_a' | 'theme_b' | 'theme_c'
    "feature_flags": {
        "news": True,
        "events": True,
        "merch": True,
        "pos": False,
        "inventory": True,
    },
}


def get_config():
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not CONFIG_FILE.exists():
            CONFIG_FILE.write_text(json.dumps(DEFAULTS, indent=2), encoding="utf-8")
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        # backfill defaults
        merged = DEFAULTS.copy()
        merged.update({k: v for k, v in data.items() if k in DEFAULTS})
        # merge nested feature flags
        ff = merged["feature_flags"]
        ff.update(data.get("feature_flags", {}))
        merged["feature_flags"] = ff
        return merged
    except Exception:
        return DEFAULTS


def set_config(data: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
