from pathlib import Path
import json
import re
import sys
import time
import subprocess
from collections import defaultdict

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".webp",
    ".webm",
    ".flv",
    ".ts",
    ".m2ts",
}

# Case-insensitive
EXCLUDE_KEYWORDS = [
    "_av1",
    # "_x265",
    # "_hevc",
]

APP_TITLE = "VidFFmpeg - Queue tool v1.01 Rev.260809"

BASE_DIR = Path(__file__).parent

PROFILE_DIR = BASE_DIR / "profiles"
QUEUE_FILE = BASE_DIR / "queue.json"
FFPROBE = r"D:\0.Software\Video&Music-Mux\FFQueue\bin\ffprobe.exe"
# FFPROBE = r"D:\__VPS\ffmpeg-py\ffprobe.exe"


# ==========================
# 0. Queue statistics
# ==========================
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


def get_video_duration(file):
    try:
        result = subprocess.run(
            [
                str(FFPROBE),
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                file,
            ],
            capture_output=True,
            text=True,
        )
        return float(result.stdout.strip())
    except:
        return 0


def show_queue_stats():
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
            total_seconds += time_to_seconds(end) - time_to_seconds(start)
        elif end:
            total_seconds += time_to_seconds(end)
        else:
            ffprobe_count += 1
            print(f"\rffprobe processed: {ffprobe_count}", end="", flush=True)
            duration = get_video_duration(item["file"])
            if start:
                total_seconds += duration - time_to_seconds(start)
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
        print(f"  {profile} : {profile_count[profile]}")

    print()
    print(f"Statistics time   : {elapsed:.2f} s")
    input("\nPress Enter to return to menu...")


# ==========================
# Exit Handling
# ==========================


def wait_exit():
    try:
        input("\nPress Enter to exit...")

    except KeyboardInterrupt:
        print()
        print("User cancelled exit")


def exit_program():
    print()
    print("==============================")
    print("Script exited")
    print("==============================")

    sys.exit(0)


# ==========================
# profile
# ==========================


def load_profiles():
    profiles = []
    if not PROFILE_DIR.exists():
        PROFILE_DIR.mkdir()

    for file in PROFILE_DIR.glob("*.json"):
        try:
            with file.open("r", encoding="utf-8") as f:
                json.load(f)
            profiles.append(file.name)
        except Exception:
            print(f"Failed to read profile: {file.name}")
    return profiles


def choose_profile():
    profiles = load_profiles()
    if not profiles:
        print("Profiles folder is empty.")
        wait_exit()
        sys.exit()

    print()
    print("==============================")
    print("Select conversion profile")
    print("==============================")

    print("0. Queue statistics")
    print("a. Check missing files")

    for i, p in enumerate(profiles, 1):
        print(f"{i}. {p}")

    while True:
        # A -> a
        cmd = input("\nEnter number: ").strip().lower()
        if cmd == "0":
            show_queue_stats()
            print()
            print("==============================")
            print("Select conversion profile")
            print("==============================")
            print()

            print("0. Queue statistics")
            print("a. Check missing files")

            for i, p in enumerate(profiles, 1):
                print(f"{i}. {p}")
            continue
        
        if cmd == "a":
            check_missing_files()
            print()
            print("==============================")
            print("Select conversion profile")
            print("==============================")
            print()

            print("0. Queue statistics")
            print("a. Check missing files")

            for i, p in enumerate(profiles, 1):
                print(f"{i}. {p}")
            continue

        if cmd.isdigit():
            num = int(cmd)
            if 1 <= num <= len(profiles):
                return profiles[num - 1]
        print("Invalid input")






def check_missing_files():
    queue = load_queue()
    missing = []

    for item in queue:
        if not Path(item["file"]).exists():
            missing.append(item)

    print()

    if not missing:
        print("All video files exist.")
        input("\nPress Enter to return to menu...")
        return

    print(f"Found {len(missing)} missing video files:")
    print()

    for item in missing:
        print(item["file"])

    print()
    answer = input("Remove missing files from queue? [y/N]: ").strip().lower()

    if answer == "y":
        missing_files = {item["file"] for item in missing}
        queue = [
            item
            for item in queue
            if item["file"] not in missing_files
        ]

        save_queue(queue)

        print()
        print(f"Removed {len(missing)} missing files.")
        print(f"Current queue: {len(queue)}")
    else:
        print("No files were removed.")

    input("\nPress Enter to return to menu...")




# ==========================
# Path Handling
# ==========================


def parse_paths(text):
    result = re.findall(r'"([^"]+)"|(\S+)', text)
    return [a if a else b for a, b in result]


def is_video(path):
    return path.suffix.lower() in VIDEO_EXTENSIONS


def is_excluded(path):
    name = path.name.lower()
    for keyword in EXCLUDE_KEYWORDS:
        if keyword.lower() in name:
            return True
    return False


def scan_path(path, result):
    path = Path(path)
    if not path.exists():
        print("Not found:", path)
        return
    if path.is_file():
        if is_video(path) and not is_excluded(path):
            result.append(path)
        return
    if path.is_dir():
        files = []
        for file in path.rglob("*"):
            if file.is_file() and is_video(file) and not is_excluded(file):
                files.append(file)

        def natural_sort_key(p):
            return [
                int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", str(p))
            ]

    files.sort(key=natural_sort_key)
    result.extend(files)


# ==========================
# cut Parsing
# ==========================


def format_time(value):
    if len(value) == 4:
        return "00:" + value[:2] + ":" + value[2:]
    if len(value) == 6:
        return value[:2] + ":" + value[2:4] + ":" + value[4:]
    return ""


def parse_cut(filename):
    start = ""
    end = ""

    # Range: 0101cut~0202cut
    # Range: 011946cut~023903cut
    m = re.search(r"(\d{4}|\d{6})cut~(\d{4}|\d{6})cut", filename)

    if m:
        start = format_time(m.group(1))
        end = format_time(m.group(2))
        return start, end

    # Start time: 0101cut~
    # Start time: 011946cut~
    m = re.search(r"(\d{4}|\d{6})cut~", filename)

    if m:
        start = format_time(m.group(1))
        return start, end

    # End time: 010102cut
    # End time: 0103cut
    m = re.search(r"(\d{4}|\d{6})cut", filename)

    if m:
        end = format_time(m.group(1))
        return start, end
    return start, end


# ==========================
# queue
# ==========================


def load_queue():
    if not QUEUE_FILE.exists():
        return []
    try:
        with QUEUE_FILE.open(encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_queue(queue):
    with QUEUE_FILE.open("w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=4)


# ==========================
# main
# ==========================


def main():
    queue = load_queue()
    print()
    print("==============================")
    print(APP_TITLE)
    #print("Current queue:")
    print("==============================")
    print(f"Existing tasks: {len(queue)}")

    profile = choose_profile()

    print()
    print("==============================")
    print("Drag and drop files or folders")
    print("==============================")
    print()

    text = input("> ")

    if not text.strip():
        print("No input")
        wait_exit()
        return

    paths = parse_paths(text)

    print()
    print("Starting scan...")

    files = []

    for p in paths:
        scan_path(p, files)

    print(f"Video files found: {len(files)}")

    queue = load_queue()
    old_files = {item["file"] for item in queue}
    add_count = 0

    for file in files:
        file_str = str(file)
        if file_str in old_files:
            continue
        start, end = parse_cut(file.name)
        queue.append({"file": file_str, "profile": profile, "start": start, "end": end})
        add_count += 1

    save_queue(queue)

    print()
    print("==============================")
    print("Added successfully")
    print("==============================")
    print(f"Dropped items   : {len(paths)}")
    print(f"Videos found    : {len(files)}")
    print(f"New tasks added : {add_count}")
    print(f"Current queue   : {len(queue)}")
    print()
    print("Saved:")
    print(QUEUE_FILE)

    wait_exit()


# ==========================
# Launch
# ==========================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("==============================")
        print("User pressed Ctrl+C, script exited.")
        print("==============================")
