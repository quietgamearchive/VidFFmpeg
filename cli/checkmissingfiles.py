from pathlib import Path

from .config import QUEUE_FILE
from .queuefile import load_queue, save_queue


def path_key(path):
    try:
        normalized = (
            Path(path)
            .expanduser()
            .resolve(strict=False)
        )

    except (OSError, RuntimeError):
        normalized = Path(path).expanduser()

    return normalized.as_posix().lower()


def check_missing_files():
    queue = load_queue()

    missing = []

    for item in queue:
        if not Path(item["file"]).is_file():
            missing.append(item)

    print()

    if not missing:
        print("All video files exist.")
        input("\nPress Enter to return to menu...")
        return

    print(
        f"Found {len(missing)} "
        "missing video files:"
    )

    print()

    for item in missing:
        print(item["file"])

    print()

    answer = input(
        "Remove missing files from queue? [y/N]: "
    ).strip().lower()

    if answer == "y":
        missing_files = {
            path_key(item["file"])
            for item in missing
        }

        queue = [
            item
            for item in queue
            if path_key(item["file"])
            not in missing_files
        ]

        save_queue(queue)

        print()
        print(
            f"Removed {len(missing)} "
            "missing files."
        )

        print(
            f"Current queue: {len(queue)}"
        )

    else:
        print("No files were removed.")

    input("\nPress Enter to return to menu...")