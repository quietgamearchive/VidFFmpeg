import platform
from pathlib import Path
import json
import subprocess
import time
from datetime import datetime
import threading
import sys

# ==================================
# User Settings
# ==================================

APP_TITLE = "VidFFmpeg - Converter " + "v1.00 Rev.260808"

# Define binary file paths for different operating systems
WINDOWS_PATHS = {
    "ffmpeg": r"D:\0.Software\Video&Music-Mux\FFQueue\bin\ffmpeg.exe",
    "ffprobe": r"D:\0.Software\Video&Music-Mux\FFQueue\bin\ffprobe.exe",
    # "ffmpeg": r"D:\__VPS\ffmpeg-py\ffmpeg.exe",
    # "ffprobe": r"D:\__VPS\ffmpeg-py\ffprobe.exe",
}

LINUX_PATHS = {
    "ffmpeg": r"/root/ffmpeg",
    "ffprobe": r"/root/ffprobe",
}

# Automatically select paths based on the current operating system
current_os = platform.system()
if current_os == "Windows":
    FFMPEG = WINDOWS_PATHS["ffmpeg"]
    FFPROBE = WINDOWS_PATHS["ffprobe"]
else:
    # Linux paths are used by default. If you are using macOS or another system, please modify this section or add a new path dictionary.
    FFMPEG = LINUX_PATHS["ffmpeg"]
    FFPROBE = LINUX_PATHS["ffprobe"]

BASE_DIR = Path(__file__).parent

QUEUE_FILE = BASE_DIR / "queue.json"
PROFILE_DIR = BASE_DIR / "profiles"
FINISHED_FILE = BASE_DIR / "finished.txt"
ERROR_FILE = BASE_DIR / "error.txt"


# ==================================
# New: Stop-after-conversion control & global subprocess control
# ==================================

stop_after_current = False
exit_flag = False
current_ffmpeg_process = None  # Used to store the currently running FFmpeg subprocess object


def key_listener():
    global stop_after_current
    while not exit_flag:
        key = sys.stdin.readline()
        if exit_flag:
            break
        if key:
            stop_after_current = not stop_after_current
            if stop_after_current:
                print("\r\033[K\nStop after the current file conversion is complete")
            else:
                print("\r\033[K\nStop request cancelled, continuing queue execution")


threading.Thread(target=key_listener, daemon=True).start()


def format_size(size):
    size = float(size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f}{unit}"
        size /= 1024


def format_time(seconds):
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h:
        return f"{h:02}:{m:02}:{s:02}"
    return f"{m:02}:{s:02}"


def same_path(a, b):
    try:
        a = Path(a).expanduser().resolve()
        b = Path(b).expanduser().resolve()
        # Windows paths are case-insensitive.
        if platform.system() == "Windows":
            return str(a).lower() == str(b).lower()
        else:
            return a == b
    except Exception:
        return False


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_profile(name):
    return load_json(PROFILE_DIR / name)


def append_error(path, reason=None):
    with open(ERROR_FILE, "a", encoding="utf-8") as f:
        if reason:
            f.write(f"{path} | {reason}\n")
        else:
            f.write(f"{path}\n")


def append_finished(dest, duration, t, size, percent):
    with open(FINISHED_FILE, "a", encoding="utf-8") as f:
        f.write(f"{dest} ({duration}) | {t} | {size} | {percent:.2f}%\n")


def pause_error(title, path):
    print()
    print("=" * 70)
    print(title)
    print()
    print(path)
    print("=" * 70)
    input("Press Enter to exit...")


def make_output(source, profile):

    source = Path(source)
    out = profile.get("output", {})
    folder = Path(out["directory"]) if out.get("directory") else source.parent
    name = out.get("filename", "{source}")
    name = name.replace("{source}", source.stem)
    ext = out.get("extension", ".mp4")
    return folder / (name + ext)


def check_video(path):

    # -----------------------------
    # 1. Check if video stream exists
    # -----------------------------
    cmd_stream = [
        FFPROBE,
        "-v",
        "error",
        "-select_streams",
        "v",
        "-show_entries",
        "stream=index",
        "-of",
        "csv=p=0",
        str(path),
    ]

    r = subprocess.run(
        cmd_stream,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if r.returncode != 0:
        return False

    # At least one video stream is required
    if not r.stdout.strip():
        return False

    # -----------------------------
    # 2. Check duration > 1 second
    # -----------------------------
    cmd_duration = [
        FFPROBE,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]

    r = subprocess.run(
        cmd_duration,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if r.returncode != 0:
        return False

    try:
        duration = float(r.stdout.strip())
    except Exception:
        return False

    return duration > 1.0


def get_video_duration(path):

    cmd = [
        FFPROBE,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]

    r = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if r.returncode == 0 and r.stdout.strip():
        try:
            duration = float(r.stdout.strip())
            return format_time(duration)
        except:
            return "Unknown"

    return "Unknown"


def calc_duration(start, end):
    def to_seconds(t):
        h, m, s = map(int, t.split(":"))
        return h * 3600 + m * 60 + s

    sec = to_seconds(end) - to_seconds(start)

    if sec <= 0:
        raise ValueError("End time must be greater than start time.")

    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60

    return f"{h:02}:{m:02}:{s:02}"


def convert_one(task, index, total):
    global current_ffmpeg_process
    source = Path(task["file"])
    profile_name = task["profile"]
    profile = load_profile(profile_name)
    dest = make_output(source, profile)
    tmp = dest.with_name(dest.stem + "_tmp" + dest.suffix)

    print()
    print("=" * 70)
    print(f"[Current {index}, {total - 1} Left]")
    print(f"Profile: {profile_name}")

    duration_text = get_video_duration(source)
    start_time = task.get("start", "")
    end_time = task.get("end", "")
    if start_time or end_time:
        start_show = start_time if start_time else "Start"
        end_show = end_time if end_time else "End"
        duration_text += f" ({start_show} - {end_show})"

    print(f"Time: {duration_text}")
    print()
    print(source)
    print("->", dest)
    print("=" * 70)

    if not source.exists():

        append_error(source, "Source file not found")
        pause_error("Error: Source file does not exist", source)
        input("Press Enter to continue...")
        return False

    old_size = source.stat().st_size
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "info", "-y"]
    if task.get("start"):
        cmd += ["-ss", task["start"]]
    cmd += ["-i", str(source)]
    if task.get("end"):
        if task.get("start"):
            cmd += ["-t", calc_duration(task["start"], task["end"])]
        else:
            cmd += ["-to", task["end"]]
    cmd += profile.get("ffmpeg_args", [])
    cmd.append(str(tmp))
    start = time.time()
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    # Debug: Print the actual FFmpeg command
    # print("FFmpeg CMD:", subprocess.list2cmdline(cmd))

    # Store the currently running subprocess in a global variable so it can be terminated externally at any time
    current_ffmpeg_process = p

    errors = []

    last_progress_line = ""  # Store the previous progress line so it can be displayed completely when an error occurs
    stop_notice_printed = False

    for line in p.stderr:
        line = line.rstrip()
        if "frame=" in line:
            msg = line.strip()
            last_progress_line = msg
            print("\r\033[K" + msg, end="", flush=True)
            if stop_after_current and not stop_notice_printed:
                print("\nStop after the current file conversion is complete")
                last_progress_line = ""
                stop_notice_printed = True
        elif any(x in line.lower() for x in ["error", "warning", "failed"]):
            # If progress output exists, add a newline first to keep it fixed in the terminal
            if last_progress_line:
                print("\r\033[K" + last_progress_line)
                last_progress_line = ""
            print(line)
            errors.append(line)

    # After the loop ends, if the last output was a progress line, keep it fixed in the terminal
    if last_progress_line:
        print("\r\033[K" + last_progress_line)

    p.wait()

    # Clear the global subprocess variable after the task finishes
    current_ffmpeg_process = None
    elapsed = time.time() - start
    print()

    if p.returncode != 0:
        append_error(source, "FFmpeg failed")
        if tmp.exists():
            tmp.unlink()
        pause_error("Error: FFmpeg conversion failed.", "\n".join(errors) if errors else source)
        return False

    if not tmp.exists() or not check_video(tmp):
        append_error(source, "ffprobe validation failed")
        if tmp.exists():
            tmp.unlink()
        pause_error("Error: Output file validation failed.", tmp)
        return False

    new_size = tmp.stat().st_size
    same_file = source.resolve() == dest.resolve()

    if same_file and new_size > old_size:
        tmp.unlink()
        append_error(source, "New file bigger than old")
        print("Overwrite mode: New file is larger, keeping original file.")
        return False

    percent = new_size / old_size * 100

    if dest.exists():
        dest.unlink()
    tmp.rename(dest)
    delete_source = profile.get("after_finish", {}).get("delete_source", False)

    if delete_source:
        if same_file:
            print("Source file and output file are the same, skipping source deletion")
        else:
            source.unlink()
            print("Source file deleted: ", source)

    append_finished(
        str(dest), duration_text, format_time(elapsed), format_size(new_size), percent
    )

    finish_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # print(
    #     f"Finished: {format_size(old_size)} -> {format_size(new_size)} "
    #     f"({percent:.2f}%) | {finish_time}"
    # )
    print(
        f"\033[34mFinished: {format_size(old_size)} -> {format_size(new_size)} "
        f"({percent:.2f}%) | {finish_time}\033[0m"
    )
    return True


def main():
    print("====================================")
    print(APP_TITLE)
    print("====================================")
    global exit_flag, current_ffmpeg_process
    index = 1
    try:
        while True:
            # Dynamically read the queue file to ensure the latest task status
            if not QUEUE_FILE.exists():
                print("Queue file queue.json not found, waiting...")
                time.sleep(1)
                continue
            try:
                queue = load_json(QUEUE_FILE)
            except (json.JSONDecodeError, Exception) as e:
                print(f"Failed to read queue.json: {e}, waiting to retry...")
                time.sleep(1)
                continue
            # If the queue is empty, show a message and exit
            if not queue:
                print("All queue conversions completed.")
                print("Press Enter to exit...")
                print("=" * 70)
                exit_flag = True
                input()
                return
            total = len(queue)
            # Processing the first task in the queue
            current_task = queue[0]
            success = convert_one(current_task, index, total)
            if not success:
                print()
                print("=" * 70)
                print("Current task failed, stopping queue.")
                print("Please check error.txt")
                print("=" * 70)
                exit_flag = True
                input("Press Enter to exit...")
                return

            # After successful conversion, remove the corresponding task from queue.json
            # Reload the queue to avoid overwriting manual changes made during conversion
            try:
                queue = load_json(QUEUE_FILE)
                removed = False
                for i, task in enumerate(queue):

                    if same_path(task.get("file", ""), current_task.get("file", "")):
                        queue.pop(i)
                        removed = True
                        print(f"Removed from queue: {task.get('file')}")
                        break
                if removed:
                    save_json(QUEUE_FILE, queue)
                else:
                    print(
                        "Warning: Completed task not found in queue.json:", current_task.get("file")
                    )

            except Exception as e:
                print(f"Failed to update queue file: {e}")

            if stop_after_current:

                print()
                print("=" * 70)
                print("Current file conversion completed, stopped continuing conversion.")
                print("Press Enter to exit...")
                print("=" * 70)
                exit_flag = True
                input()
                return

            index += 1

    except KeyboardInterrupt:
        # Catch Ctrl+C, exit gracefully and clean up temporary files
        print("\n\nExit signal received, terminating conversion and cleaning up...")
        exit_flag = True

        # 1. Force terminate the currently running FFmpeg subprocess
        if current_ffmpeg_process is not None:
            try:
                current_ffmpeg_process.terminate()
                current_ffmpeg_process.wait(timeout=5)  # Wait up to 5 seconds for the process to fully close
            except Exception:
                pass  # Ignore if the process has already exited or timed out

        # 2. Automatically remove possible leftover temporary files (_tmp)
        try:
            # Reload the queue to get information about the currently processing task
            if QUEUE_FILE.exists():
                try:
                    queue = load_json(QUEUE_FILE)
                    if queue:
                        current_task = queue[0]
                        source = Path(current_task["file"])
                        profile = load_profile(current_task["profile"])
                        dest = make_output(source, profile)
                        tmp = dest.with_name(dest.stem + "_tmp" + dest.suffix)

                        if tmp.exists():
                            tmp.unlink()
                            print(f"Leftover temporary files cleaned up: {tmp.name}")
                except Exception:
                    pass
        except Exception:
            pass

        return


if __name__ == "__main__":

    main()
