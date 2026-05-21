import json
from copy import deepcopy
from pathlib import Path
from typing import Any


DEFAULT_SERVER_SETTINGS: dict[str, Any] = {
    "features": {
        "transform_on": False,
        "skeleton_on": False,
    },
    "skeleton": {
        "connections": (
            "0-1,0-2,1-3,2-4,5-6,5-7,7-9,6-8,8-10,"
            "5-11,6-12,11-12,11-13,13-15,12-14,14-16"
        ),
        "line_color": [0, 255, 0],
        "point_color": [255, 0, 0],
        "point_radius": 4,
    },
    "video": {
        "output_dir": "videos",
        "fps": 30,
        "session_end_timeout_sec": 2.0,
        "monitor_interval_sec": 0.5,
    },
    "accident_filter": {
        "session_timeout_sec": 15.0,
    },
}

SERVER_SETTINGS_PATH = Path(__file__).with_name("Server_Options.json")


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)

    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value

    return merged


def load_server_options() -> dict[str, Any]:
    if not SERVER_SETTINGS_PATH.exists():
        return deepcopy(DEFAULT_SERVER_SETTINGS)

    with SERVER_SETTINGS_PATH.open("r", encoding="utf-8") as file:
        loaded_settings = json.load(file)

    if not isinstance(loaded_settings, dict):
        raise ValueError("Server_Options.json 형식이 올바르지 않습니다.")

    return _deep_merge(DEFAULT_SERVER_SETTINGS, loaded_settings)
