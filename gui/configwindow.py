import sys
import tkinter as tk
from tkinter import filedialog

from .config import SaveConfig, resolve_path


def show_config(root, config):
    config_window = tk.Toplevel(root)
    config_window.withdraw()

    config_window.title("Config")
    config_window.resizable(False, False)
    config_window.transient(root)

    if sys.platform.startswith("win"):
        ffmpeg_key = "ffmpeg_win"
        ffprobe_key = "ffprobe_win"
    else:
        ffmpeg_key = "ffmpeg_linux"
        ffprobe_key = "ffprobe_linux"

    label_ffmpeg = tk.Label(
        config_window,
        text="ffmpeg Path:",
        anchor="w"
    )

    label_ffmpeg.place(
        x=10,
        y=10,
        width=74,
        height=21
    )

    label_ffprobe = tk.Label(
        config_window,
        text="ffprobe Path:",
        anchor="w"
    )

    label_ffprobe.place(
        x=10,
        y=40,
        width=79,
        height=21
    )

    ffmpeg_entry = tk.Entry(
        config_window
    )

    ffmpeg_entry.place(
        x=90,
        y=10,
        width=424,
        height=24
    )

    ffmpeg_entry.insert(
        0,
        str(config[ffmpeg_key])
    )

    ffprobe_entry = tk.Entry(
        config_window
    )

    ffprobe_entry.place(
        x=90,
        y=40,
        width=424,
        height=24
    )

    ffprobe_entry.insert(
        0,
        str(config[ffprobe_key])
    )

    def browse_ffmpeg():
        path = filedialog.askopenfilename(
            parent=config_window,
            title="Select ffmpeg"
        )

        if path:
            ffmpeg_entry.delete(
                0,
                tk.END
            )

            ffmpeg_entry.insert(
                0,
                path
            )

    def browse_ffprobe():
        path = filedialog.askopenfilename(
            parent=config_window,
            title="Select ffprobe"
        )

        if path:
            ffprobe_entry.delete(
                0,
                tk.END
            )

            ffprobe_entry.insert(
                0,
                path
            )

    label_video_ext = tk.Label(
        config_window,
        text="Video ext:",
        anchor="w"
    )

    label_video_ext.place(
        x=10,
        y=70,
        width=74,
        height=21
    )

    video_ext_entry = tk.Entry(
        config_window
    )

    video_ext_entry.place(
        x=90,
        y=70,
        width=489,
        height=24
    )

    video_ext_entry.insert(
        0,
        ", ".join(
            config.get(
                "video_extensions",
                []
            )
        )
    )

    label_exclude = tk.Label(
        config_window,
        text="Exclude keywords:",
        anchor="w"
    )

    label_exclude.place(
        x=10,
        y=100,
        width=100,
        height=21
    )

    exclude_entry = tk.Entry(
        config_window
    )

    exclude_entry.place(
        x=115,
        y=100,
        width=464,
        height=24
    )

    exclude_entry.insert(
        0,
        ", ".join(
            config.get(
                "exclude_keywords",
                []
            )
        )
    )

    label_threads = tk.Label(
        config_window,
        text="FFprobe threads:",
        anchor="w"
    )

    label_threads.place(
        x=10,
        y=130,
        width=100,
        height=21
    )

    threads_entry = tk.Entry(
        config_window
    )

    threads_entry.place(
        x=115,
        y=130,
        width=100,
        height=24
    )

    threads_entry.insert(
        0,
        str(
            config.get(
                "ffprobe_threads",
                10
            )
        )
    )

    def save_and_close():
        try:
            ffprobe_threads = int(
                threads_entry.get().strip()
            )

            if ffprobe_threads <= 0:
                raise ValueError

        except ValueError:
            from .msgbox import show_message

            show_message(
                config_window,
                "Invalid Value",
                "FFprobe threads must be a positive integer.",
                icon="error",
                buttons="ok"
            )

            return

        video_extensions = [
            item.strip()
            for item in video_ext_entry.get().split(",")
            if item.strip()
        ]

        exclude_keywords = [
            item.strip()
            for item in exclude_entry.get().split(",")
            if item.strip()
        ]

        video_extensions = [
            item if item.startswith(".") else "." + item
            for item in video_extensions
        ]

        video_extensions = [
            item.lower()
            for item in video_extensions
        ]

        exclude_keywords = [
            item.lower()
            for item in exclude_keywords
        ]

        config[ffmpeg_key] = resolve_path(
            ffmpeg_entry.get()
        )

        config[ffprobe_key] = resolve_path(
            ffprobe_entry.get()
        )

        config["video_extensions"] = video_extensions
        config["exclude_keywords"] = exclude_keywords
        config["ffprobe_threads"] = ffprobe_threads

        SaveConfig(
            config
        )

        config_window.destroy()

    def cancel():
        config_window.destroy()

    ffmpeg_browse_button = tk.Button(
        config_window,
        text="Browse",
        command=browse_ffmpeg
    )

    ffmpeg_browse_button.place(
        x=530,
        y=10,
        width=49,
        height=26
    )

    ffprobe_browse_button = tk.Button(
        config_window,
        text="Browse",
        command=browse_ffprobe
    )

    ffprobe_browse_button.place(
        x=530,
        y=40,
        width=49,
        height=26
    )

    ok_button = tk.Button(
        config_window,
        text="OK",
        width=10,
        command=save_and_close
    )

    ok_button.place(
        x=420,
        y=400,
        width=70,
        height=30
    )

    cancel_button = tk.Button(
        config_window,
        text="Cancel",
        width=10,
        command=cancel
    )

    cancel_button.place(
        x=500,
        y=400,
        width=70,
        height=30
    )

    config_window.protocol(
        "WM_DELETE_WINDOW",
        cancel
    )

    config_window.bind(
        "<Return>",
        lambda event: save_and_close()
    )

    config_window.bind(
        "<Escape>",
        lambda event: cancel()
    )

    config_window.update_idletasks()
    root.update_idletasks()

    window_width = 600
    window_height = 450

    x = root.winfo_x() + (
        root.winfo_width()
        - window_width
    ) // 2

    y = root.winfo_y() + (
        root.winfo_height()
        - window_height
    ) // 2

    config_window.geometry(
        f"{window_width}x{window_height}+{x}+{y}"
    )

    config_window.deiconify()
    config_window.grab_set()
    config_window.focus_set()

    root.wait_window(
        config_window
    )