"""Persists user-facing GUI settings (language, units, IARU region) across restarts.

Stored as JSON in the user's home directory -- not part of the antenna
calculation engine, purely a GUI convenience.
"""

import json
from pathlib import Path

SETTINGS_PATH = Path.home() / ".ham_antenna_designer_settings.json"

# region: IARU band plan, "1" = Europe/Africa/Middle East, "2" = the Americas
DEFAULTS = {"lang": "en", "units": "metric", "region": "1", "drawing_theme": "night"}


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return dict(DEFAULTS)
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULTS)
    settings = dict(DEFAULTS)
    settings.update({k: v for k, v in data.items() if k in DEFAULTS})
    return settings


def save_settings(**kwargs) -> None:
    settings = load_settings()
    settings.update({k: v for k, v in kwargs.items() if k in DEFAULTS})
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f)
    except OSError:
        pass  # GUI convenience only -- never block on a write failure
