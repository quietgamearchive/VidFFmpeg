import platform
from pathlib import Path
from .msgbox import show_message


def check_environment(
    root,
    ffmpeg_win,
    ffprobe_win,
    ffmpeg_linux,
    ffprobe_linux
):
    """
    Check the required FFmpeg and FFprobe files
    according to the current operating system.

    Returns:
        True  - all required files exist
        False - one or more files are missing
    """

    system = platform.system()

    if system == "Windows":
        ffmpeg = Path(ffmpeg_win)
        ffprobe = Path(ffprobe_win)

    elif system == "Linux":
        ffmpeg = Path(ffmpeg_linux)
        ffprobe = Path(ffprobe_linux)

    else:
        show_message(
            root,
            "Error",
            f"Unsupported operating system:\n{system}",
            icon="error",
            buttons="ok"
        )
        return False

    missing = []

    if not ffmpeg.is_file():
        missing.append(
            f"FFmpeg:\n{ffmpeg}"
        )

    if not ffprobe.is_file():
        missing.append(
            f"FFprobe:\n{ffprobe}"
        )

    if missing:
        message = (
            "The following required files are missing:\n\n"
            + "\n\n".join(missing)
        )

        show_message(
            root,
            "Initialization Error",
            message,
            icon="error",
            buttons="ok"
        )

        return False

    return True