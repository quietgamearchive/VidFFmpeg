import platform
import subprocess
import time
from collections import defaultdict

from .config import LoadConfig, QUEUE_FILE
from .queuefile import load_queue


def time_to_seconds(text):
    if not text:
        return 0

    h, m, s = map(int, text.split(":"))
    return h * 3600 + m * 60 + s


def format_seconds(seconds):
    seconds = int(seconds)

    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    return f"{h:02}:{m:02}:{s:02}"


def get_video_duration(file, ffprobe):
    try:
        result = subprocess.run(
            [
                str(ffprobe),
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                file,
            ],
            capture_output=True,
            text=True
        )

        return float(result.stdout.strip())

    except Exception:
        return 0


def show_queue_stats():
    config = LoadConfig()

    if platform.system() == "Windows":
        ffprobe = config["ffprobe_win"]
    else:
        ffprobe = config["ffprobe_linux"]

    print("Starting statistics...")

    start_time = time.perf_counter()

    queue = load_queue()

    print(f"Queue loaded: {len(queue)}")

    total_seconds = 0
    cut_count = 0
    profile_count = defaultdict(int)
    ffprobe_count = 0

    for item in queue:
        profile_count[item["profile"]] += 1

        start = item["start"]
        end = item["end"]

        if start or end:
            cut_count += 1

        if start and end:
            total_seconds += (
                time_to_seconds(end)
                - time_to_seconds(start)
            )

        elif end:
            total_seconds += time_to_seconds(end)

        else:
            ffprobe_count += 1

            print(
                f"\rffprobe processed: {ffprobe_count}",
                end="",
                flush=True
            )

            duration = get_video_duration(
                item["file"],
                ffprobe
            )

            if start:
                total_seconds += (
                    duration
                    - time_to_seconds(start)
                )
            else:
                total_seconds += duration

    print()

    elapsed = time.perf_counter() - start_time

    print()
    print("==============================")
    print("Queue Statistics")
    print("==============================")
    print()

    print(f"Tasks          : {len(queue)}")
    print(f"Need cut       : {cut_count}")
    print(f"Total duration : {format_seconds(total_seconds)}")

    print()

    print("Profile:")

    for profile in sorted(profile_count):
        print(
            f"  {profile} : "
            f"{profile_count[profile]}"
        )

    print()
    print(f"Statistics time   : {elapsed:.2f} s")

    input("\nPress Enter to return to menu...")