import json
import sys
from pathlib import Path


if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.parent


CONFIG_FILE = BASE_DIR / "config.json"

PROFILE_DIR = BASE_DIR / "profiles"
QUEUE_FILE = BASE_DIR / "queue.json"


DEFAULT_CONFIG = {
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


def resolve_path(value):
    path = Path(value)

    if isinstance(value, str) and value.startswith("$"):
        return BASE_DIR / value[1:].lstrip("/\\")

    if path.is_absolute():
        return path

    return BASE_DIR / path


def _save_default_config():
    with open(
        CONFIG_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            DEFAULT_CONFIG,
            f,
            indent=4,
            ensure_ascii=False
        )


def LoadConfig():
    if not CONFIG_FILE.exists():
        _save_default_config()
        config = DEFAULT_CONFIG.copy()
    else:
        try:
            with open(
                CONFIG_FILE,
                "r",
                encoding="utf-8"
            ) as f:
                config = json.load(f)

        except Exception:
            config = DEFAULT_CONFIG.copy()

    if not isinstance(config, dict):
        config = DEFAULT_CONFIG.copy()

    path_keys = {
        "ffmpeg_win",
        "ffprobe_win",
        "ffmpeg_linux",
        "ffprobe_linux"
    }

    return {
        key: resolve_path(value)
        if key in path_keys
        else value
        for key, value in config.items()
    }