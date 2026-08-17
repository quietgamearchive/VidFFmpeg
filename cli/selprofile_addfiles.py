import re
from pathlib import Path

from .config import (
    LoadConfig,
    PROFILE_DIR,
    QUEUE_FILE,
)
from .queuefile import (
    load_queue,
    save_queue
)


def parse_paths(text):
    result = re.findall(
        r'"([^"]+)"|(\S+)',
        text
    )

    return [
        a if a else b
        for a, b in result
    ]


def is_video(path, video_extensions):
    return (
        path.suffix.lower()
        in video_extensions
    )


def is_excluded(path, exclude_keywords):
    name = path.name.lower()

    for keyword in exclude_keywords:
        if keyword.lower() in name:
            return True

    return False


def natural_sort_key(path):
    return [
        int(x) if x.isdigit() else x.lower()
        for x in re.split(
            r"(\d+)",
            str(path)
        )
    ]


def scan_path(
    path,
    result,
    video_extensions,
    exclude_keywords
):
    path = Path(path)

    if not path.exists():
        print("Not found:", path)
        return

    if path.is_file():
        if (
            is_video(
                path,
                video_extensions
            )
            and not is_excluded(
                path,
                exclude_keywords
            )
        ):
            result.append(path)

        return

    if path.is_dir():
        files = []

        for file in path.rglob("*"):
            if (
                file.is_file()
                and is_video(
                    file,
                    video_extensions
                )
                and not is_excluded(
                    file,
                    exclude_keywords
                )
            ):
                files.append(file)

        files.sort(key=natural_sort_key)

        result.extend(files)


def format_time(value):
    if len(value) == 4:
        return (
            "00:"
            + value[:2]
            + ":"
            + value[2:]
        )

    if len(value) == 6:
        return (
            value[:2]
            + ":"
            + value[2:4]
            + ":"
            + value[4:]
        )

    return ""


def parse_cut(filename):
    start = ""
    end = ""

    # Range:
    # 0101cut~0202cut
    # 011946cut~023903cut
    match = re.search(
        r"(\d{4}|\d{6})cut~"
        r"(\d{4}|\d{6})cut",
        filename
    )

    if match:
        start = format_time(match.group(1))
        end = format_time(match.group(2))

        return start, end

    # Start:
    # 0101cut~
    # 011946cut~
    match = re.search(
        r"(\d{4}|\d{6})cut~",
        filename
    )

    if match:
        start = format_time(
            match.group(1)
        )

        return start, end

    # End:
    # 010102cut
    # 0103cut
    match = re.search(
        r"(\d{4}|\d{6})cut",
        filename
    )

    if match:
        end = format_time(
            match.group(1)
        )

        return start, end

    return start, end


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


def load_profiles():
    profiles = []

    if not PROFILE_DIR.exists():
        PROFILE_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

    for file in PROFILE_DIR.glob("*.json"):
        try:
            with file.open(
                "r",
                encoding="utf-8"
            ) as f:
                import json
                json.load(f)

            profiles.append(file.name)

        except Exception:
            print(
                f"Failed to read profile: "
                f"{file.name}"
            )

    return profiles


def select_profile():
    profiles = load_profiles()

    if not profiles:
        print("Profiles folder is empty.")
        input("\nPress Enter to return to menu...")
        return None

    print()
    print("==============================")
    print("Select conversion profile")
    print("==============================")
    print()

    for i, profile in enumerate(
        profiles,
        1
    ):
        print(
            f"{i}. {profile}"
        )

    while True:
        cmd = input(
            "\nEnter number: "
        ).strip()

        if cmd.isdigit():
            number = int(cmd)

            if 1 <= number <= len(profiles):
                return profiles[number - 1]

        print("Invalid input")


def select_profile_and_add_files():
    config = LoadConfig()

    profile = select_profile()

    if profile is None:
        return

    print()
    print("==============================")
    print("Drag and drop files or folders")
    print("==============================")
    print()

    text = input("> ")

    if not text.strip():
        print("No input")
        input("\nPress Enter to return to menu...")
        return

    paths = parse_paths(text)

    print()
    print("Starting scan...")

    files = []

    video_extensions = {
        ext.lower()
        for ext in config["video_extensions"]
    }

    exclude_keywords = config[
        "exclude_keywords"
    ]

    for path in paths:
        scan_path(
            path,
            files,
            video_extensions,
            exclude_keywords
        )

    print(
        f"Video files found: "
        f"{len(files)}"
    )

    queue = load_queue()

    old_files = {
        path_key(item["file"])
        for item in queue
    }

    add_count = 0

    for file in files:
        file_str = str(file)

        if path_key(file_str) in old_files:
            continue

        start, end = parse_cut(
            file.name
        )

        queue.append({
            "file": file_str,
            "profile": profile,
            "start": start,
            "end": end
        })

        old_files.add(
            path_key(file_str)
        )

        add_count += 1

    save_queue(queue)

    print()
    print("==============================")
    print("Added successfully")
    print("==============================")

    print(
        f"Dropped items   : "
        f"{len(paths)}"
    )

    print(
        f"Videos found    : "
        f"{len(files)}"
    )

    print(
        f"New tasks added : "
        f"{add_count}"
    )

    print(
        f"Current queue   : "
        f"{len(queue)}"
    )

    print()
    print("Saved:")
    print(
        QUEUE_FILE
    )

    input("\nPress Enter to return to menu...")
