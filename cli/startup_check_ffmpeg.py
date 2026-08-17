import platform
from pathlib import Path

from .config import CONFIG_FILE, LoadConfig


def check_ffmpeg_paths():
    """Check that the configured FFmpeg tools are real files."""
    config = LoadConfig()
    is_windows = platform.system() == "Windows"
    ffmpeg_key = "ffmpeg_win" if is_windows else "ffmpeg_linux"
    ffprobe_key = "ffprobe_win" if is_windows else "ffprobe_linux"

    try:
        ffmpeg = config[ffmpeg_key]
        ffprobe = config[ffprobe_key]
    except (KeyError, TypeError):
        ffmpeg = None
        ffprobe = None

    missing = []

    for key, path in (
        (ffmpeg_key, ffmpeg),
        (ffprobe_key, ffprobe),
    ):
        try:
            valid = path is not None and Path(path).is_file()
        except (OSError, TypeError, ValueError):
            valid = False

        if not valid:
            missing.append((key, path))

    if not missing:
        return True

    print()
    print("FFmpeg configuration is invalid.")
    print("The following required binary files were not found:")

    for key, path in missing:
        print(f"  {key}: {path or '<empty>'}")

    print()
    print(f"Please edit {CONFIG_FILE} and set valid paths for these files.")
    input("Press Enter to exit...")
    return False
