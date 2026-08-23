import json
import sys
from pathlib import Path


if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.parent


CONFIG_FILE = BASE_DIR / "config.json"


DEFAULT_CONFIG = {
    "Left": None,
    "Top": None,
    "ffmpeg_win": "$/bin/ffmpeg.exe",
    "ffprobe_win": "$/bin/ffprobe.exe",
    "ffmpeg_linux": "$/bin/ffmpeg",
    "ffprobe_linux": "$/bin/ffprobe",
    "video_extensions": [
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".webp",
        ".webm",
        ".flv",
        ".ts",
        ".m2ts"
    ],
    "exclude_keywords": [
        "_av1"
    ],
    "current_profile": "",
    "ffprobe_threads": 10
}


def GetWindowPosition(config, screen_w, screen_h, window_w, window_h):
    default_left = (screen_w - window_w) // 2
    default_top = (screen_h - window_h) // 2

    left = config.get("Left")
    top = config.get("Top")

    if isinstance(left, bool):
        left = None
    else:
        try:
            left = int(left) if left is not None else None
        except (TypeError, ValueError):
            left = None

    if isinstance(top, bool):
        top = None
    else:
        try:
            top = int(top) if top is not None else None
        except (TypeError, ValueError):
            top = None

    return (
        default_left if left is None else left,
        default_top if top is None else top
    )


def resolve_path(value):
    if not isinstance(value, str):
        return None

    path = Path(value)

    if value.startswith("$"):
        return BASE_DIR / value[1:].lstrip("/\\")

    if path.is_absolute():
        return path

    return BASE_DIR / path


def LoadConfig():
    config = None

    if CONFIG_FILE.exists():
        try:
            with open(
                CONFIG_FILE,
                "r",
                encoding="utf-8"
            ) as f:
                config = json.load(f)

        except Exception:
            config = None

    if not isinstance(config, dict):
        config = DEFAULT_CONFIG.copy()
        SaveConfig(config)

    else:
        changed = False

        for key, default_value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = default_value
                changed = True

        if changed:
            SaveConfig(config)

    path_keys = {
        "ffmpeg_win",
        "ffprobe_win",
        "ffmpeg_linux",
        "ffprobe_linux"
    }

    result = {}

    for key, value in config.items():
        if key in path_keys:
            if not isinstance(value, str):
                value = DEFAULT_CONFIG.get(key)

            result[key] = resolve_path(value)

        else:
            result[key] = value

    return result


def SaveConfig(config):
    data = {}

    for key, value in config.items():
        if isinstance(value, Path):
            try:
                relative = value.relative_to(BASE_DIR)
                data[key] = f"$/{relative}"
            except ValueError:
                data[key] = str(value)

        else:
            data[key] = value

    with open(
        CONFIG_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )
