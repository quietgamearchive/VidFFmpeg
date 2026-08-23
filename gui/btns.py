import sys
import threading
from datetime import datetime
from pathlib import Path

import tkinter as tk

from .msgbox import show_message
from . import treeview
from .profile_selector import profile_combobox


def _time_to_seconds(value):
    if not value:
        return 0

    try:
        parts = value.split(":")

        if len(parts) != 3:
            return 0

        return (
            int(parts[0]) * 3600
            + int(parts[1]) * 60
            + int(parts[2])
        )

    except Exception:
        return 0


def check_ffmpeg_environment(
    root,
    ffmpeg,
    ffprobe
):
    if not ffmpeg.is_file():
        show_message(
            root,
            "FFmpeg Error",
            f"ffmpeg was not found:\n\n{ffmpeg}",
            icon="error",
            buttons="ok"
        )

        return False

    if not ffprobe.is_file():
        show_message(
            root,
            "FFprobe Error",
            f"ffprobe was not found:\n\n{ffprobe}",
            icon="error",
            buttons="ok"
        )

        return False

    return True


def create_control_buttons(
    root,
    config
):
    start_button = tk.Button(
        root,
        text="Start",
        height=2
    )

    start_button.place(
        x=5,
        y=5,
        width=100
    )

    stop_button = tk.Button(
        root,
        text="Stop",
        height=2,
        state="disabled"
    )

    stop_button.place(
        x=110,
        y=5,
        width=100
    )

    pause_button = tk.Button(
        root,
        text="Pause",
        height=2,
        state="disabled"
    )

    pause_button.place(
        x=215,
        y=5,
        width=100
    )

    state = {
        "running": False,
        "paused": False,
        "stop_event": threading.Event(),
        "controller": None,
        "thread": None,
        "queue_data": None,
        "save_queue": None,
        "info_label": None,
        "ffprobe_path": None,
        "profile_dir": None,
        "finished_file": None,
        "error_file": None,
        "finished_callback": None,
        "close_requested": False
    }

    def close_root():
        root.save_window_config()
        root.destroy()

    def get_profile_widget():
        try:
            from . import profile_selector

            return (
                profile_selector.profile_combobox
            )
        except Exception:
            return None

    def set_profile_enabled(enabled):
        widget = get_profile_widget()

        if widget is None:
            return

        try:
            widget.configure(
                state=(
                    "readonly"
                    if enabled
                    else "disabled"
                )
            )
        except Exception:
            pass

    def restore_info():
        if (
            state["info_label"] is not None
            and state["queue_data"] is not None
        ):
            treeview.update_queue_info(
                state["info_label"],
                state["queue_data"]
            )

    def finish_ui():
        state["running"] = False
        state["paused"] = False

        start_button.config(
            state="normal"
        )

        stop_button.config(
            state="disabled"
        )

        pause_button.config(
            state="disabled",
            text="Pause"
        )

        set_profile_enabled(
            True
        )

        treeview.set_conversion_running(
            False
        )

        treeview.clear_first_progress()

        restore_info()

        state["controller"] = None
        state["thread"] = None

    def finish_and_close():
        finish_ui()
        close_root()

    def finish_action():
        match root.action_index:
            case 0:
                finish_ui()
            case 1:
                finish_ui()
            case 2:
                finish_and_close()

    def update_progress(value):
        root.after(
            0,
            lambda: treeview.update_progress(
                value
            )
        )

    def update_info(text):
        if state["info_label"] is None:
            return

        root.after(
            0,
            lambda: treeview.update_conversion_info(
                state["info_label"],
                text
            )
        )

    def update_finished():
        finished_treeview = getattr(
            root,
            "finished_treeview",
            None
        )

        if finished_treeview is None:
            return

        root.after(
            0,
            finished_treeview.reload
        )

    def update_error():
        error_treeview = getattr(
            root,
            "error_treeview",
            None
        )

        if error_treeview is None:
            return

        root.after(
            0,
            error_treeview.reload
        )

    def enable_pause_when_ready():
        if not state["running"]:
            return

        controller = state["controller"]

        if controller is not None and controller.process is not None:
            pause_button.config(
                state="normal"
            )
            return

        root.after(
            50,
            enable_pause_when_ready
        )

    def process_queue():
        try:
            run_conversion_loop()

        except Exception as e:
            controller = state[
                "controller"
            ]

            if controller:
                controller.stop()

            if state["stop_event"].is_set():
                root.after(
                    0,
                    finish_ui
                )

                return

            root.after(
                0,
                lambda reason=f"Unexpected conversion thread error: {e}":
                conversion_error(reason)
            )

    def run_conversion_loop():
        if not state["queue_data"]:
            root.after(
                0,
                finish_ui
            )
            return

        system_is_windows = (
            sys.platform.startswith("win")
        )

        if system_is_windows:
            from .convert_win import (
                FFmpegProcess,
                convert_task
            )
        else:
            from .convert_linux import (
                FFmpegProcess,
                convert_task
            )

        controller = FFmpegProcess()

        state["controller"] = controller

        root.after(
            0,
            enable_pause_when_ready
        )

        while (
            state["running"]
            and not state["stop_event"].is_set()
            and state["queue_data"]
        ):
            task = state["queue_data"][0]

            try:
                success, reason = convert_task(
                    task,
                    state["profile_dir"],
                    state["ffmpeg_path"],
                    state["ffprobe_path"],
                    state["finished_file"],
                    state["error_file"],
                    controller,
                    update_progress,
                    update_info,
                    state["stop_event"],
                    state["finished_callback"]
                )
            except Exception as e:
                if state["stop_event"].is_set():
                    root.after(0, finish_ui)
                    return

                root.after(
                    0,
                    lambda reason=f"Unexpected conversion error: {e}":
                    conversion_error(reason)
                )
                return

            if state["stop_event"].is_set():
                root.after(
                    0,
                    finish_ui
                )
                return

            if not success:
                root.after(
                    0,
                    lambda reason=reason: conversion_error(
                        reason
                    )
                )
                return

            # Remove only the task that was
            # actually completed.
            if (
                state["queue_data"]
                and state["queue_data"][0]
                is task
            ):
                state["queue_data"].pop(
                    0
                )

            try:
                state["save_queue"]()

            except Exception as e:
                root.after(
                    0,
                    lambda reason=f"Failed to save queue: {e}":
                    conversion_error(reason)
                )

                return

            root.after(
                0,
                lambda: treeview.refresh_tree(
                    state["queue_data"]
                )
            )

            action_index = root.action_index

            if not state["queue_data"]:
                root.after(
                    0,
                    finish_action
                )
                return

            match action_index:
                case 0:
                    pass
                case 1:
                    root.after(
                        0,
                        finish_ui
                    )
                    return
                case 2:
                    root.after(
                        0,
                        finish_and_close
                    )
                    return

        root.after(
            0,
            finish_ui
        )

    def conversion_error(reason):
        source = ""

        if state["queue_data"]:
            source = state[
                "queue_data"
            ][0].get(
                "file",
                ""
            )

        finish_ui()
        update_error()

        show_message(
            root,
            "Conversion Error",
            (
                f"File:\n{source}\n\n"
                f"Reason:\n{reason}"
            ),
            icon="error",
            buttons="ok"
        )

    def start_queue():
        if state["running"]:
            return

        if sys.platform.startswith("win"):
            ffmpeg = config["ffmpeg_win"]
            ffprobe = config["ffprobe_win"]
        else:
            ffmpeg = config["ffmpeg_linux"]
            ffprobe = config["ffprobe_linux"]

        if not check_ffmpeg_environment(
            root,
            ffmpeg,
            ffprobe
        ):
            return

        # The treeview module contains the
        # current queue reference.
        from . import treeview as treeview_module

        current_tree = (
            treeview_module.tree
        )

        if current_tree is None:
            return

        queue_data = getattr(
            root,
            "queue_data",
            None
        )

        if queue_data is None:
            show_message(
                root,
                "Queue Error",
                "Queue data is not available.",
                icon="error",
                buttons="ok"
            )
            return

        if not queue_data:
            show_message(
                root,
                "Queue",
                "The queue is empty.",
                icon="information",
                buttons="ok"
            )
            return

        profile_dir = (
            Path(__file__).parent.parent
            / "profiles"
        )

        base_dir = (
            Path(__file__).parent.parent
        )

        invalid_items = []

        for item in queue_data:
            start = item.get(
                "start",
                ""
            )

            end = item.get(
                "end",
                ""
            )

            if start and end:
                if (
                    _time_to_seconds(end)
                    <= _time_to_seconds(start)
                ):
                    invalid_items.append(
                        item.get("file", "")
                    )

        if invalid_items:
            finish_time = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            try:
                with open(
                    base_dir / "error.txt",
                    "a",
                    encoding="utf-8"
                ) as f:
                    for file_path in invalid_items:
                        f.write(
                            f"{file_path} | "
                            f"{finish_time} | "
                            "End time must be greater "
                            "than start time.\n"
                        )
            except Exception:
                pass

            show_message(
                root,
                "Invalid Cut Times",
                (
                    "The queue contains tasks with "
                    "invalid cut times "
                    "(end must be greater than start).\n\n"
                    "Conversion will not start."
                ),
                icon="error",
                buttons="ok"
            )

            return

        state["queue_data"] = queue_data
        state["save_queue"] = getattr(
            root,
            "save_queue",
            None
        )

        state["info_label"] = getattr(
            root,
            "info_label",
            None
        )

        if state["save_queue"] is None:
            show_message(
                root,
                "Queue Error",
                "Queue save function is not available.",
                icon="error",
                buttons="ok"
            )
            return

        state["ffmpeg_path"] = ffmpeg
        state["ffprobe_path"] = ffprobe
        state["profile_dir"] = profile_dir
        state["finished_file"] = (
            base_dir / "finished.txt"
        )
        state["error_file"] = (
            base_dir / "error.txt"
        )
        state["finished_callback"] = update_finished

        state["stop_event"].clear()
        state["running"] = True
        state["paused"] = False

        start_button.config(
            state="disabled"
        )

        stop_button.config(
            state="normal"
        )

        pause_button.config(
            state="disabled",
            text="Pause"
        )

        treeview.set_conversion_running(
            True
        )

        state["thread"] = threading.Thread(
            target=process_queue,
            daemon=True
        )

        state["thread"].start()

    def stop_queue():
        if not state["running"]:
            return

        result = show_message(
            root,
            "Stop Conversion",
            "Are you sure you want to stop the conversion?",
            icon="warning",
            buttons="yesno"
        )

        if result != "yes":
            return

        state["stop_event"].set()

        controller = state[
            "controller"
        ]

        if controller:
            controller.stop()

        stop_button.config(
            state="disabled"
        )

        pause_button.config(
            state="disabled",
            text="Pause"
        )

    def request_close():
        if state["close_requested"]:
            return

        if not state["running"]:
            close_root()
            return

        result = show_message(
            root,
            "Close",
            "Conversion is still running. Do you want to stop it and close the window?",
            icon="question",
            buttons="yesno"
        )

        if result != "yes":
            return

        state["close_requested"] = True
        state["stop_event"].set()

        controller = state["controller"]

        if controller:
            controller.stop()

        stop_button.config(
            state="disabled"
        )

        pause_button.config(
            state="disabled",
            text="Pause"
        )

        def wait_for_finish():
            if state["running"]:
                root.after(
                    50,
                    wait_for_finish
                )
                return

            close_root()

        wait_for_finish()

    def pause_queue():
        if not state["running"]:
            return

        controller = state[
            "controller"
        ]

        if controller is None:
            return

        if not state["paused"]:
            if controller.pause():
                state["paused"] = True

                pause_button.config(
                    text="Resume"
                )

        else:
            if controller.resume():
                state["paused"] = False

                pause_button.config(
                    text="Pause"
                )

    start_button.config(
        command=start_queue
    )

    stop_button.config(
        command=stop_queue
    )

    pause_button.config(
        command=pause_queue
    )

    # Expose shared objects to the root window.
    # This avoids changing your existing main
    # program function signatures.
    root.control_buttons = {
        "start": start_button,
        "stop": stop_button,
        "pause": pause_button
    }

    root.request_close = request_close

    return root.control_buttons
