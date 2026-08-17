import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from collections import defaultdict
import json
import subprocess
import threading
import time

from .msgbox import show_message
from .configwindow import show_config


def update_queue_info(info_label, queue_data):
    total = len(queue_data)
    cut_required = 0

    for item in queue_data:
        if item.get("start") or item.get("end"):
            cut_required += 1

    info_label.config(
        text=(
            f"Total files: {total}\n"
            f"Cut required: {cut_required}"
        )
    )


def format_seconds(seconds):
    seconds = max(0, int(seconds))

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds:02d}"
    )


def time_to_seconds(value):
    if not value:
        return 0

    parts = value.split(":")

    if len(parts) != 3:
        return 0

    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])

    return (
        hours * 3600
        + minutes * 60
        + seconds
    )


def get_video_duration(
    file_path,
    ffprobe_path,
    cancel_event=None
):
    command = [
        str(ffprobe_path),
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    while True:
        if cancel_event and cancel_event.is_set():
            try:
                process.terminate()
            except Exception:
                pass

            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                except Exception:
                    pass

            return None

        result = process.poll()

        if result is not None:
            break

        time.sleep(0.05)

    if result != 0:
        return None

    output = process.stdout.read().strip()

    if not output:
        return None

    try:
        return float(output)
    except ValueError:
        return None


def show_about(
    root,
    window_title
):
    about = tk.Toplevel(root)
    about.withdraw()

    about.title("About")
    about.resizable(False, False)
    about.transient(root)

    info = (
        f"{window_title}\n"
        "\n"
        "VidFFmpeg is a lightweight FFmpeg batch transcoding queue manager.\n"
        # "\n"
        # "Copyright © 2026\n"
        # "All rights reserved."
    )

    label = tk.Label(
        about,
        text=info,
        justify="center"
    )

    label.pack(
        expand=True,
        fill="both",
        padx=20,
        pady=10
    )

    ok_button = tk.Button(
        about,
        text="OK",
        width=10,
        command=about.destroy
    )

    ok_button.pack(
        pady=(0, 15)
    )

    about.protocol(
        "WM_DELETE_WINDOW",
        about.destroy
    )

    about.update_idletasks()
    root.update_idletasks()

    x = root.winfo_x() + (
        root.winfo_width()
        - about.winfo_width()
    ) // 2

    y = root.winfo_y() + (
        root.winfo_height()
        - about.winfo_height()
    ) // 2

    about.geometry(
        f"+{x}+{y}"
    )

    about.deiconify()
    about.grab_set()
    about.focus_set()

    root.wait_window(about)


def show_queue_info(
    root,
    queue_data
):
    total = len(queue_data)
    cut_required = 0
    profiles = defaultdict(int)

    for item in queue_data:
        profile = item.get(
            "profile",
            ""
        )

        if profile:
            profiles[profile] += 1

        if (
            item.get("start")
            or item.get("end")
        ):
            cut_required += 1

    text = (
        f"Total files: {total}\n"
        f"Cut required: {cut_required}\n"
    )

    if profiles:
        text += "\nProfile:\n"

        for profile in sorted(profiles):
            text += (
                f"{profile} : "
                f"{profiles[profile]}\n"
            )

    show_message(
        root,
        "Queue Info",
        text,
        icon="information",
        buttons="ok"
    )


def show_queue_statistics(
    root,
    queue_data,
    ffprobe_path,
    config
):
    if not queue_data:
        show_message(
            root,
            "Queue Statistics",
            "The queue is empty.",
            icon="information",
            buttons="ok"
        )
        return

    queue = list(queue_data)

    total = len(queue)

    profile_count = defaultdict(int)

    cut_count = 0
    total_seconds = 0

    probe_items = []

    for item in queue:
        profile = item.get(
            "profile",
            ""
        )

        if profile:
            profile_count[profile] += 1

        start = item.get(
            "start",
            ""
        )

        end = item.get(
            "end",
            ""
        )

        if start or end:
            cut_count += 1

        if start and end:
            total_seconds += (
                time_to_seconds(end)
                - time_to_seconds(start)
            )

        elif end:
            total_seconds += (
                time_to_seconds(end)
            )

        else:
            probe_items.append(item)

    progress_window = tk.Toplevel(root)
    progress_window.withdraw()

    progress_window.title(
        "Queue Statistics"
    )

    progress_window.resizable(
        False,
        False
    )

    progress_window.transient(root)

    progress_window.protocol(
        "WM_DELETE_WINDOW",
        lambda: None
    )

    progress_label = tk.Label(
        progress_window,
        text=f"0 / {len(probe_items)}"
    )

    progress_label.pack(
        padx=40,
        pady=(25, 15)
    )

    cancel_event = threading.Event()

    cancel_button = tk.Button(
        progress_window,
        text="Cancel",
        width=10
    )

    cancel_button.pack(
        pady=(0, 20)
    )

    start_time = time.perf_counter()

    state = {
        "completed": 0,
        "total_seconds": total_seconds,
        "cancelled": False,
        "finished": False
    }

    executor = None

    def cancel():
        if state["finished"]:
            return

        state["cancelled"] = True
        cancel_event.set()

        cancel_button.config(
            state="disabled"
        )

        progress_label.config(
            text="Cancelling..."
        )

    cancel_button.config(
        command=cancel
    )

    root.update_idletasks()
    progress_window.update_idletasks()

    x = root.winfo_x() + (
        root.winfo_width()
        - progress_window.winfo_width()
    ) // 2

    y = root.winfo_y() + (
        root.winfo_height()
        - progress_window.winfo_height()
    ) // 2

    progress_window.geometry(
        f"+{x}+{y}"
    )

    progress_window.deiconify()
    progress_window.grab_set()
    progress_window.focus_set()

    def finish_statistics():
        nonlocal executor

        if state["finished"]:
            return

        state["finished"] = True

        if executor:
            executor.shutdown(
                wait=False,
                cancel_futures=True
            )

        try:
            progress_window.grab_release()
        except Exception:
            pass

        try:
            progress_window.destroy()
        except Exception:
            pass

        if state["cancelled"]:
            return

        elapsed = (
            time.perf_counter()
            - start_time
        )

        text = (
            f"Tasks          : {total}\n"
            f"Cut required   : {cut_count}\n"
            f"Total duration : "
            f"{format_seconds(state['total_seconds'])}\n"
            "\n"
            "Profile:\n"
        )

        for profile in sorted(profile_count):
            text += (
                f"  {profile} : "
                f"{profile_count[profile]}\n"
            )

        text += (
            "\n"
            f"Statistics time : "
            f"{elapsed:.2f} s"
        )

        show_message(
            root,
            "Queue Statistics",
            text,
            icon="information",
            buttons="ok"
        )

    if not probe_items:
        finish_statistics()
        return

    from concurrent.futures import (
        ThreadPoolExecutor
    )

    try:
        ffprobe_threads = int(
            config.get(
                "ffprobe_threads",
                10
            )
        )
    except (
        TypeError,
        ValueError
    ):
        ffprobe_threads = 10

    ffprobe_threads = max(
        1,
        ffprobe_threads
    )

    executor = ThreadPoolExecutor(
        max_workers=ffprobe_threads
    )

    futures = {}

    for item in probe_items:
        if cancel_event.is_set():
            break

        future = executor.submit(
            get_video_duration,
            item["file"],
            ffprobe_path,
            cancel_event
        )

        futures[future] = item

    def monitor():
        if state["finished"]:
            return

        if state["cancelled"]:
            for future in futures:
                if not future.done():
                    future.cancel()

            if all(
                future.done()
                for future in futures
            ):
                finish_statistics()
                return

            root.after(
                50,
                monitor
            )

            return

        completed = 0

        for future in futures:
            if future.done():
                completed += 1

        if completed != state["completed"]:
            state["completed"] = completed

            progress_label.config(
                text=(
                    f"{completed} / "
                    f"{len(probe_items)}"
                )
            )

        if completed == len(probe_items):
            for future, item in futures.items():
                try:
                    duration = future.result()
                except Exception:
                    duration = None

                if duration is None:
                    continue

                start = item.get(
                    "start",
                    ""
                )

                if start:
                    state["total_seconds"] += (
                        duration
                        - time_to_seconds(start)
                    )
                else:
                    state["total_seconds"] += duration

            finish_statistics()
            return

        root.after(
            50,
            monitor
        )

    root.after(
        50,
        monitor
    )


def check_missing_files(
    root,
    queue_data,
    save_queue,
    info_label
):
    missing = []

    for item in queue_data:
        if not Path(
            item["file"]
        ).exists():
            missing.append(item)

    if not missing:
        show_message(
            root,
            "Check Missing Files",
            "All video files exist.",
            icon="information",
            buttons="ok"
        )
        return

    message = (
        f"Found {len(missing)} "
        f"missing video files.\n\n"
        "Remove them from the queue?"
    )

    result = show_message(
        root,
        "Check Missing Files",
        message,
        icon="warning",
        buttons="yesno"
    )

    if result != "yes":
        return

    missing_files = {
        item["file"]
        for item in missing
    }

    queue_data[:] = [
        item
        for item in queue_data
        if item["file"]
        not in missing_files
    ]

    save_queue()

    update_queue_info(
        info_label,
        queue_data
    )

    show_message(
        root,
        "Check Missing Files",
        (
            f"Removed {len(missing)} "
            "missing files.\n\n"
            f"Current queue: {len(queue_data)}"
        ),
        icon="information",
        buttons="ok"
    )


def create_menu(
    root,
    queue_data,
    config,
    save_queue,
    ffprobe_path,
    window_title,
    info_label
):
    menu_bar = tk.Menu(root)

    file_menu = tk.Menu(
        menu_bar,
        tearoff=0
    )

    file_menu.add_command(
        label="Queue Info",
        command=lambda: show_queue_info(
            root,
            queue_data
        )
    )

    file_menu.add_command(
        label="Queue Statistics",
        command=lambda: show_queue_statistics(
            root,
            queue_data,
            ffprobe_path,
            config
        )
    )

    file_menu.add_command(
        label="Check Missing Files",
        command=lambda: check_missing_files(
            root,
            queue_data,
            save_queue,
            info_label
        )
    )

    menu_bar.add_cascade(
        label="File",
        menu=file_menu
    )

    config_menu = tk.Menu(
        menu_bar,
        tearoff=0
    )

    config_menu.add_command(
        label="Config",
        command=lambda: show_config(
            root,
            config
        )
    )

    menu_bar.add_cascade(
        label="Config",
        menu=config_menu
    )

    help_menu = tk.Menu(
        menu_bar,
        tearoff=0
    )

    help_menu.add_command(
        label="About",
        command=lambda: show_about(
            root,
            window_title
        )
    )

    menu_bar.add_cascade(
        label="Help",
        menu=help_menu
    )

    root.config(
        menu=menu_bar
    )