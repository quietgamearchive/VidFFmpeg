import ctypes
import json
import os
import platform
import re
import select
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from .config import (
    LoadConfig,
    BASE_DIR,
    PROFILE_DIR,
    QUEUE_FILE
)
from .queuefile import load_queue, save_queue
from common.single_instance import acquire_single_instance


FINISHED_FILE = BASE_DIR / "finished.txt"
ERROR_FILE = BASE_DIR / "error.txt"


stop_after_current = False
exit_flag = False
current_ffmpeg_process = None
conversion_active = False

waiting_for_enter = False
pending_enter = False

enter_event = threading.Event()
stdin_state_lock = threading.Lock()

stdin_listener_stop = threading.Event()


# ==========================
# Terminal input listener
# ==========================

def key_listener():
    global stop_after_current
    global pending_enter

    while not stdin_listener_stop.is_set():
        try:
            if platform.system() == "Windows":
                import msvcrt

                if not msvcrt.kbhit():
                    time.sleep(0.05)
                    continue

                key = msvcrt.getwch()

                if key in ("\r", "\n"):
                    with stdin_state_lock:
                        if waiting_for_enter:
                            enter_event.set()
                            continue

                        if not conversion_active:
                            continue

                        stop_after_current = not stop_after_current
                        stop_requested = stop_after_current
                        pending_enter = True

                else:
                    continue

            else:
                ready, _, _ = select.select(
                    [sys.stdin],
                    [],
                    [],
                    0.05
                )

                if not ready:
                    continue

                key = sys.stdin.read(1)

                if not key:
                    continue

                if key in ("\n", "\r"):
                    with stdin_state_lock:
                        if waiting_for_enter:
                            enter_event.set()
                            continue

                        if not conversion_active:
                            continue

                        stop_after_current = not stop_after_current
                        stop_requested = stop_after_current
                        pending_enter = True

                else:
                    continue

        except Exception:
            time.sleep(0.05)
            continue

        if stop_requested:
            print(
                "\r\033[K\n"
                "Stop after the current file conversion is complete",
                flush=True
            )

        else:
            print(
                "\r\033[K\n"
                "Stop request cancelled, continuing queue execution",
                flush=True
            )


def start_key_listener():
    stdin_listener_stop.clear()

    thread = threading.Thread(
        target=key_listener,
        daemon=True
    )

    thread.start()

    return thread


def stop_key_listener():
    stdin_listener_stop.set()


def wait_for_enter(prompt="Press Enter to continue..."):
    global waiting_for_enter
    global pending_enter

    with stdin_state_lock:
        if pending_enter:
            pending_enter = False
            immediate = True

        else:
            enter_event.clear()
            waiting_for_enter = True
            immediate = False

    if not immediate:
        print(
            prompt,
            end="",
            flush=True
        )

        enter_event.wait()

        with stdin_state_lock:
            waiting_for_enter = False

        print()


# ==========================
# Formatting
# ==========================

def format_size(size):
    size = float(size)

    for unit in [
        "B",
        "KB",
        "MB",
        "GB",
        "TB"
    ]:
        if size < 1024:
            return f"{size:.2f}{unit}"

        size /= 1024

    return f"{size:.2f}PB"


def format_time(seconds):
    seconds = int(seconds)

    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    if h:
        return f"{h:02}:{m:02}:{s:02}"

    return f"{m:02}:{s:02}"


# ==========================
# Terminal title
# ==========================

def set_terminal_title(title):
    if not sys.stdout.isatty():
        return

    try:
        if platform.system() == "Windows":
            ctypes.windll.kernel32.SetConsoleTitleW(
                str(title)
            )

        else:
            print(
                f"\033]0;{title}\007",
                end="",
                flush=True
            )

    except Exception:
        pass


# ==========================
# Path
# ==========================

def same_path(a, b):
    try:
        a = Path(a).expanduser().resolve()
        b = Path(b).expanduser().resolve()

        try:
            return os.path.samefile(a, b)

        except OSError:
            pass

        if platform.system() == "Windows":
            return str(a).lower() == str(b).lower()

        return a == b

    except Exception:
        return False


# ==========================
# JSON
# ==========================

def load_json(path):
    with open(
        path,
        encoding="utf-8"
    ) as f:
        return json.load(f)


def save_json(path, data):
    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


# ==========================
# Profile
# ==========================

def load_profile(name):
    return load_json(
        PROFILE_DIR / name
    )


# ==========================
# Logs
# ==========================

def append_error(path, reason=None):
    finish_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    with open(
        ERROR_FILE,
        "a",
        encoding="utf-8"
    ) as f:
        f.write(
            f"{path} | {finish_time} | {reason}\n"
        )


def append_finished(
    dest,
    duration,
    t,
    finish_time,
    size,
    percent
):
    with open(
        FINISHED_FILE,
        "a",
        encoding="utf-8"
    ) as f:
        f.write(
            f"{dest} ({duration}) | "
            f"{t} | "
            f"{finish_time} | "
            f"{size} | "
            f"{percent:.2f}%\n"
        )


def pause_error(title, path):
    print()
    print("=" * 70)
    print(title)
    print()
    print(path)
    print("=" * 70)


# ==========================
# Output
# ==========================

def make_output(source, profile):
    source = Path(source)

    out = profile.get(
        "output",
        {}
    )

    folder = (
        Path(out["directory"])
        if out.get("directory")
        else source.parent
    )

    name = out.get(
        "filename",
        "{source}"
    )

    name = name.replace(
        "{source}",
        source.stem
    )

    ext = out.get(
        "extension",
        ".mp4"
    )

    return folder / (name + ext)


# ==========================
# FFmpeg / FFprobe
# ==========================

def get_ffmpeg_paths():
    config = LoadConfig()

    if platform.system() == "Windows":
        ffmpeg = config["ffmpeg_win"]
        ffprobe = config["ffprobe_win"]

    else:
        ffmpeg = config["ffmpeg_linux"]
        ffprobe = config["ffprobe_linux"]

    return ffmpeg, ffprobe


def check_video(path, ffprobe):
    cmd_stream = [
        str(ffprobe),
        "-v",
        "error",
        "-select_streams",
        "v",
        "-show_entries",
        "stream=index",
        "-of",
        "csv=p=0",
        str(path)
    ]

    result = subprocess.run(
        cmd_stream,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if result.returncode != 0:
        return False

    if not result.stdout.strip():
        return False

    cmd_duration = [
        str(ffprobe),
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path)
    ]

    result = subprocess.run(
        cmd_duration,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if result.returncode != 0:
        return False

    try:
        duration = float(
            result.stdout.strip()
        )
    except Exception:
        return False

    return duration > 0


def get_video_duration_seconds(
    path,
    ffprobe
):
    cmd = [
        str(ffprobe),
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path)
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if (
        result.returncode == 0
        and result.stdout.strip()
    ):
        try:
            return float(
                result.stdout.strip()
            )

        except (
            TypeError,
            ValueError
        ):
            pass

    return None


# ==========================
# Time
# ==========================

def time_to_seconds(value):
    h, m, s = value.split(":")

    return (
        int(h) * 3600
        + int(m) * 60
        + float(s)
    )


def calc_duration(start, end):
    def to_seconds(value):
        h, m, s = map(
            int,
            value.split(":")
        )

        return (
            h * 3600
            + m * 60
            + s
        )

    seconds = (
        to_seconds(end)
        - to_seconds(start)
    )

    if seconds <= 0:
        raise ValueError(
            "End time must be greater than start time."
        )

    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    return (
        f"{h:02}:"
        f"{m:02}:"
        f"{s:02}"
    )


def validate_cut_times(queue):
    problems = []

    for item in queue:
        start = item.get(
            "start",
            ""
        )

        end = item.get(
            "end",
            ""
        )

        if start and end:
            try:
                calc_duration(
                    start,
                    end
                )
            except ValueError as e:
                problems.append(
                    (
                        item.get("file", ""),
                        str(e)
                    )
                )

    return problems


# ==========================
# Convert one file
# ==========================

def convert_one(
    task,
    index,
    total,
    ffmpeg,
    ffprobe
):
    global current_ffmpeg_process
    global conversion_active

    source = Path(
        task["file"]
    )

    profile_name = task["profile"]

    profile = load_profile(
        profile_name
    )

    dest = make_output(
        source,
        profile
    )

    tmp = dest.with_name(
        dest.stem
        + "_tmp"
        + dest.suffix
    )

    dest.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    print()
    print("=" * 70)
    print(
        f"[Current {index}, "
        f"{total - 1} Left]"
    )
    print(
        f"Profile: {profile_name}"
    )

    start_time = task.get(
        "start",
        ""
    )

    end_time = task.get(
        "end",
        ""
    )

    source_duration = (
        get_video_duration_seconds(
            source,
            ffprobe
        )
    )

    target_duration = source_duration

    if target_duration is not None:
        if start_time:
            target_duration -= (
                time_to_seconds(
                    start_time
                )
            )

        if end_time:
            target_duration = min(
                target_duration,
                time_to_seconds(
                    end_time
                )
                - time_to_seconds(
                    start_time
                    or "00:00:00"
                )
            )

        target_duration = max(
            target_duration,
            0.001
        )

    duration_text = (
        format_time(
            source_duration
        )
        if source_duration is not None
        else "Unknown"
    )

    if start_time or end_time:
        start_show = (
            start_time
            if start_time
            else "Start"
        )

        end_show = (
            end_time
            if end_time
            else "End"
        )

        duration_text += (
            f" ({start_show} - {end_show})"
        )

    print(
        f"Time: {duration_text}"
    )

    print()
    print(source)
    print("->", dest)
    print("=" * 70)

    if not source.exists():
        append_error(
            source,
            "Source file not found"
        )

        pause_error(
            "Error: Source file does not exist",
            source
        )

        return False

    old_size = source.stat().st_size

    cmd = [
        str(ffmpeg),
        "-hide_banner",
        "-loglevel",
        "info",
        "-y"
    ]

    if task.get("start"):
        cmd += [
            "-ss",
            task["start"]
        ]

    cmd += [
        "-i",
        str(source)
    ]

    if task.get("end"):
        if task.get("start"):
            try:
                cut_duration = calc_duration(
                    task["start"],
                    task["end"]
                )
            except ValueError as e:
                append_error(
                    source,
                    str(e)
                )

                pause_error(
                    "Error: Invalid cut times.",
                    e
                )

                return False

            cmd += [
                "-t",
                cut_duration
            ]

        else:
            cmd += [
                "-to",
                task["end"]
            ]

    cmd += profile.get(
        "ffmpeg_args",
        []
    )

    cmd.append(
        str(tmp)
    )

    start = time.time()

    try:
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )

    except Exception as e:
        append_error(
            source,
            f"Failed to start FFmpeg: {e}"
        )

        pause_error(
            "Error: Failed to start FFmpeg.",
            e
        )

        return False

    current_ffmpeg_process = p

    with stdin_state_lock:
        conversion_active = True

    errors = []
    last_progress_line = ""

    for line in p.stderr:
        line = line.rstrip()

        if "frame=" in line:
            msg = line.strip()

            last_progress_line = msg

            current_seconds = None

            current_match = re.search(
                r"time=(\d{2}:\d{2}:\d{2}(?:\.\d+)?)",
                msg
            )

            if current_match:
                try:
                    current_seconds = (
                        time_to_seconds(
                            current_match.group(1)
                        )
                    )

                except ValueError:
                    pass

            speed = None

            speed_match = re.search(
                r"speed=\s*([\d.]+)x",
                msg
            )

            if speed_match:
                try:
                    speed = float(
                        speed_match.group(1)
                    )

                except ValueError:
                    pass

            remaining_text = "--:--"

            if (
                target_duration is not None
                and current_seconds is not None
                and speed
                and speed > 0
            ):
                remaining = max(
                    0.0,
                    (
                        target_duration
                        - current_seconds
                    ) / speed
                )

                remaining_text = (
                    format_time(
                        remaining
                    )
                )

            set_terminal_title(
                f"ETA: {remaining_text}"
            )

            print(
                "\r\033[K" + msg,
                end="",
                flush=True
            )

        elif any(
            x in line.lower()
            for x in [
                "error",
                "warning",
                "failed"
            ]
        ):
            if last_progress_line:
                print(
                    "\r\033[K"
                    + last_progress_line
                )

                last_progress_line = ""

            print(line)
            errors.append(line)

    if last_progress_line:
        print(
            "\r\033[K"
            + last_progress_line
        )

    p.wait()

    current_ffmpeg_process = None

    with stdin_state_lock:
        conversion_active = False

    elapsed = time.time() - start

    print()

    if p.returncode != 0:
        append_error(
            source,
            "FFmpeg failed"
        )

        if tmp.exists():
            tmp.unlink()

        pause_error(
            "Error: FFmpeg conversion failed.",
            "\n".join(errors)
            if errors
            else source
        )

        return False

    if (
        not tmp.exists()
        or not check_video(
            tmp,
            ffprobe
        )
    ):
        append_error(
            source,
            "ffprobe validation failed"
        )

        if tmp.exists():
            tmp.unlink()

        pause_error(
            "Error: Output file validation failed.",
            tmp
        )

        return False

    new_size = tmp.stat().st_size

    same_file = same_path(
        source,
        dest
    )

    if (
        same_file
        and new_size > old_size
    ):
        tmp.unlink()

        append_error(
            source,
            "New file bigger than old"
        )

        print(
            "Overwrite mode: "
            "New file is larger, "
            "keeping original file."
        )

        return False

    percent = (
        new_size
        / old_size
        * 100
        if old_size
        else 0
    )

    if dest.exists():
        dest.unlink()

    tmp.rename(dest)

    delete_source = (
        profile
        .get(
            "after_finish",
            {}
        )
        .get(
            "delete_source",
            False
        )
    )

    if delete_source:
        if same_file:
            print(
                "Source file and output file "
                "are the same, skipping "
                "source deletion"
            )

        else:
            source.unlink()

            print(
                "Source file deleted:",
                source
            )

    finish_time = (
        datetime.now()
        .strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    append_finished(
        str(dest),
        duration_text,
        format_time(elapsed),
        finish_time,
        format_size(new_size),
        percent
    )

    print(
        f"\033[34mFinished: "
        f"{format_size(old_size)} -> "
        f"{format_size(new_size)} "
        f"({percent:.2f}%) | "
        f"{finish_time}\033[0m"
    )

    return True


# ==========================
# Convert videos
# ==========================

def convert_videos():
    global exit_flag
    global stop_after_current
    global current_ffmpeg_process
    global conversion_active

    # Kernel-level single-instance lock (no lock file): the local
    # variable holds it for the whole conversion; when this function
    # returns (or raises) the lock is released automatically.
    conversion_lock = acquire_single_instance("vidffmpeg_cli")

    if not conversion_lock:
        print()
        print("=" * 70)
        print("Convert video")
        print("=" * 70)
        print()
        print(
            "Conversion is already in progress."
        )
        print(
            "Another VidFFmpeg conversion "
            "process is running."
        )
        print()
        input(
            "Press Enter to return to menu..."
        )
        return

    stop_after_current = False
    exit_flag = False
    current_ffmpeg_process = None

    with stdin_state_lock:
        conversion_active = False

    ffmpeg, ffprobe = (
        get_ffmpeg_paths()
    )

    listener = start_key_listener()

    index = 1

    try:
        while True:
            if not QUEUE_FILE.exists():
                print()
                print(
                    "Queue file queue.json "
                    "not found, waiting..."
                )

                time.sleep(1)
                continue

            try:
                queue = load_queue()

            except Exception as e:
                print()
                print(
                    f"Failed to read queue.json: "
                    f"{e}, waiting to retry..."
                )

                time.sleep(1)
                continue

            if not queue:
                set_terminal_title(
                    "VidFFmpeg"
                )

                print()
                print(
                    "All queue conversions completed."
                )

                print()
                print("=" * 70)
                print(
                    "Press Enter to return to menu..."
                )
                print("=" * 70)

                wait_for_enter()

                return

            total = len(queue)

            problems = validate_cut_times(
                queue
            )

            if problems:
                for path, reason in problems:
                    append_error(
                        path,
                        reason
                    )

                print()
                print("=" * 70)
                print(
                    "Invalid cut times detected "
                    "in the queue."
                )
                print(
                    "Conversion stopped."
                )
                print()

                for path, reason in problems:
                    print(
                        f"{path}: {reason}"
                    )

                print("=" * 70)

                wait_for_enter(
                    "Press Enter to return to menu..."
                )

                return

            current_task = queue[0]

            success = convert_one(
                current_task,
                index,
                total,
                ffmpeg,
                ffprobe
            )

            if not success:
                print()
                print("=" * 70)
                print(
                    "Current task failed, "
                    "stopping queue."
                )
                print(
                    "Please check error.txt"
                )
                print("=" * 70)

                wait_for_enter(
                    "Press Enter to return to menu..."
                )

                return

            try:
                queue = load_queue()

                removed = False

                for i, task in enumerate(
                    queue
                ):
                    if same_path(
                        task.get("file", ""),
                        current_task.get("file", "")
                    ):
                        queue.pop(i)

                        removed = True

                        print(
                            "Removed from queue:",
                            task.get("file")
                        )

                        break

                if removed:
                    save_queue(queue)

                else:
                    print(
                        "Warning: Completed task "
                        "not found in queue.json:",
                        current_task.get("file")
                    )

            except Exception as e:
                print(
                    f"Failed to update queue file: "
                    f"{e}"
                )

            if stop_after_current:
                set_terminal_title(
                    "VidFFmpeg"
                )

                print()
                print("=" * 70)
                print(
                    "Current file conversion completed, "
                    "stopped continuing conversion."
                )
                print(
                    "Press Enter to return to menu..."
                )
                print("=" * 70)

                wait_for_enter()

                return

            index += 1

    except KeyboardInterrupt:
        print(
            "\n\nExit signal received, "
            "terminating conversion "
            "and cleaning up..."
        )

        exit_flag = True

        if current_ffmpeg_process is not None:
            try:
                current_ffmpeg_process.terminate()

                current_ffmpeg_process.wait(
                    timeout=5
                )

            except Exception:
                pass

        try:
            if QUEUE_FILE.exists():
                queue = load_queue()

                if queue:
                    current_task = queue[0]

                    source = Path(
                        current_task["file"]
                    )

                    profile = load_profile(
                        current_task["profile"]
                    )

                    dest = make_output(
                        source,
                        profile
                    )

                    tmp = dest.with_name(
                        dest.stem
                        + "_tmp"
                        + dest.suffix
                    )

                    if tmp.exists():
                        tmp.unlink()

                        print(
                            "Leftover temporary "
                            "files cleaned up:",
                            tmp.name
                        )

        except Exception:
            pass

    finally:
        exit_flag = True

        current_ffmpeg_process = None

        with stdin_state_lock:
            conversion_active = False
            waiting_for_enter = False
            pending_enter = False

        set_terminal_title(
            "VidFFmpeg"
        )

        stop_key_listener()

    # conversion_lock is released when it goes out of scope
