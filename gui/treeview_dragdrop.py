import os
import re
import tkinter as tk
from pathlib import Path

from tkinterdnd2 import DND_FILES


def format_time(value):
    if len(value) == 4:
        return "00:" + value[:2] + ":" + value[2:]

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
        r"(\d{4}|\d{6})cut~(\d{4}|\d{6})cut",
        filename
    )

    if match:
        start = format_time(
            match.group(1)
        )

        end = format_time(
            match.group(2)
        )

        return start, end

    # Start time:
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

    # End time:
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


def setup_drag_drop(
    root,
    tree,
    queue_data,
    profile_combobox,
    info_label,
    video_extensions,
    exclude_keywords,
    save_queue,
    update_queue_info
):
    state = {
        "processing": False,
        "cancelled": False,
        "files": [],
        "index": 0,
        "profile": ""
    }

    processing_frame = None

    def is_video_file(path):
        extensions = {
            str(ext).lower()
            for ext in video_extensions
        }

        if path.suffix.lower() not in extensions:
            return False

        filename = path.name.lower()

        for keyword in exclude_keywords:
            if str(keyword).lower() in filename:
                return False

        return True

    def file_already_exists(path):
        path_string = str(path)

        for item in queue_data:
            if item.get("file", "") == path_string:
                return True

        return False

    def collect_files(paths):
        result = []

        for path_string in paths:
            path = Path(path_string)

            if not path.exists():
                continue

            if path.is_file():
                if is_video_file(path):
                    result.append(path)

                continue

            if path.is_dir():
                for root_dir, dirs, files in os.walk(path):
                    for filename in files:
                        file_path = (
                            Path(root_dir) / filename
                        )

                        if is_video_file(file_path):
                            result.append(file_path)

        return result

    def cancel_processing():
        if not state["processing"]:
            return

        state["cancelled"] = True

    def show_processing():
        nonlocal processing_frame

        processing_frame = tk.Frame(
            root,
            relief="solid",
            borderwidth=1
        )

        processing_frame.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
            width=220,
            height=110
        )

        label = tk.Label(
            processing_frame,
            text="Processing..."
        )

        label.place(
            x=0,
            y=20,
            width=220,
            height=25
        )

        cancel_button = tk.Button(
            processing_frame,
            text="Cancel",
            width=10,
            command=cancel_processing
        )

        cancel_button.place(
            x=70,
            y=60,
            width=80,
            height=30
        )

        tree.state([
            "disabled"
        ])

        profile_combobox.configure(
            state="disabled"
        )

    def hide_processing():
        nonlocal processing_frame

        if processing_frame:
            processing_frame.destroy()

        processing_frame = None

        tree.state([
            "!disabled"
        ])

        profile_combobox.configure(
            state="readonly"
        )

    def finish_processing():
        state["processing"] = False

        hide_processing()

        update_queue_info(
            info_label,
            queue_data
        )

        save_queue()

    def process_next():
        if not state["processing"]:
            return

        if state["cancelled"]:
            finish_processing()
            return

        if state["index"] >= len(state["files"]):
            finish_processing()
            return

        path = state["files"][
            state["index"]
        ]

        state["index"] += 1

        if not file_already_exists(path):
            start, end = parse_cut(
                path.name
            )

            queue_data.append(
                {
                    "file": str(path),
                    "profile": state["profile"],
                    "start": start,
                    "end": end
                }
            )

            tree.insert(
                "",
                "end",
                text=str(
                    len(queue_data) - 1
                ),
                values=(
                    str(path),
                    state["profile"],
                    start,
                    end,
                    ""
                )
            )

            update_queue_info(
                info_label,
                queue_data
            )

        root.after(
            1,
            process_next
        )

    def start_processing(paths):
        if state["processing"]:
            return

        profile = profile_combobox.get()

        if not profile:
            return

        files = collect_files(
            paths
        )

        files = [
            path
            for path in files
            if not file_already_exists(path)
        ]

        if not files:
            return

        state["processing"] = True
        state["cancelled"] = False
        state["files"] = files
        state["index"] = 0
        state["profile"] = profile

        show_processing()

        root.after(
            1,
            process_next
        )

    def on_drop(event):
        if state["processing"]:
            return

        try:
            paths = root.tk.splitlist(
                event.data
            )
        except Exception:
            paths = []

        if not paths:
            return

        start_processing(
            paths
        )

    tree.drop_target_register(
        DND_FILES
    )

    tree.dnd_bind(
        "<<Drop>>",
        on_drop
    )