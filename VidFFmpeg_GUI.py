import sys
sys.dont_write_bytecode = True

from tkinterdnd2 import TkinterDnD
import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path
import os
import re
import atexit
from tkinter import messagebox

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from gui.menu import create_menu
from gui.treeview import (
    create_treeview,
    update_queue_info
)
from gui.treeview_dragdrop import setup_drag_drop
from gui.btns import create_control_buttons
from gui.debug import update_title
from gui.config import LoadConfig, SaveConfig
from gui.profile_selector import create_profile_selector


WINDOW_WIDTH = 1500
WINDOW_HEIGHT = 600

DEBUG_POSITION = False
# DEBUG_POSITION = True

WINDOW_TITLE = (
    "VidFFmpeg - GUI "
    + "v1.00 Rev.260817"
)

QUEUE_FILE = "queue.json"
PROFILE_DIR = "profiles"
LOCK_FILE = "vf_gui.lock"

queue_file = BASE_DIR / QUEUE_FILE
profile_dir = BASE_DIR / PROFILE_DIR
lock_file = BASE_DIR / LOCK_FILE

_instance_handle = None


def acquire_single_instance():
    """Acquire an advisory lock on the lock file."""
    global _instance_handle

    instance_handle = open(lock_file, "a+b")
    try:
        if os.name == "nt":
            import msvcrt

            instance_handle.seek(0)
            if not instance_handle.read(1):
                instance_handle.seek(0)
                instance_handle.write(b" ")
                instance_handle.flush()
            instance_handle.seek(0)
            msvcrt.locking(instance_handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(
                instance_handle.fileno(),
                fcntl.LOCK_EX | fcntl.LOCK_NB
            )
    except OSError:
        instance_handle.close()
        messagebox.showwarning(
            "VidFFmpeg",
            "VidFFmpeg 已经在运行中。\n请使用已经打开的窗口。"
        )
        return False

    _instance_handle = instance_handle
    atexit.register(release_single_instance)
    return True


def release_single_instance():
    """Release the lock and remove the per-process lock file."""
    global _instance_handle

    if _instance_handle is None:
        return

    try:
        if os.name == "nt":
            import msvcrt

            _instance_handle.seek(0)
            msvcrt.locking(_instance_handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(_instance_handle.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass
    finally:
        _instance_handle.close()
        _instance_handle = None


if not acquire_single_instance():
    raise SystemExit(0)


queue_data = []
queue_load_failed = False


def load_queue():
    global queue_data
    global queue_load_failed

    queue_load_failed = False

    if not queue_file.exists():
        queue_data = []
        return

    try:
        with open(
            queue_file,
            "r",
            encoding="utf-8"
        ) as f:
            loaded_data = json.load(f)

        if not isinstance(loaded_data, list):
            raise ValueError("Queue JSON must contain a list.")

        queue_data = loaded_data

    except Exception as e:
        print(e)
        queue_data = []
        queue_load_failed = True


def save_queue(force=False):
    global queue_load_failed

    if queue_load_failed and not force:
        print(
            f"Queue was not saved because it could not be loaded: {queue_file}"
        )
        return False

    temporary = queue_file.with_name(
        queue_file.name + ".tmp"
    )

    try:
        with open(
            temporary,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                queue_data,
                f,
                indent=4,
                ensure_ascii=False
            )
            f.flush()
            os.fsync(f.fileno())

        os.replace(
            temporary,
            queue_file
        )
        queue_load_failed = False
        return True

    except Exception:
        try:
            if temporary.exists():
                temporary.unlink()
        except Exception:
            pass
        raise


def get_profiles():
    if not profile_dir.exists():
        return []

    return sorted(
        [
            p.name
            for p in profile_dir.glob("*.json")
        ]
    )


def validate_file(value):
    return os.path.isfile(value)


def validate_time(value):
    if value == "":
        return True

    return bool(
        re.fullmatch(
            r"\d{2}:\d{2}:\d{2}",
            value
        )
    )


config = LoadConfig()


root = TkinterDnD.Tk()

root.iconbitmap(
    BASE_DIR / "VidFFmpeg.ico"
)


screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()

x = (screen_w - WINDOW_WIDTH) // 2
y = (screen_h - WINDOW_HEIGHT) // 2

root.geometry(
    f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}"
)

root.resizable(
    False,
    False
)






profile_combobox = create_profile_selector(
    root,
    profile_dir,
    config,
    SaveConfig,
    x=1050,
    y=5,
    width=430,
    height=30
)

info_label = tk.Label(
    root,
    text="Statistics\n2222",
    anchor="nw",
    justify="left",
    height=6,
    fg="blue",
    font=("TkDefaultFont", 10, "bold"),
    relief="solid",
    borderwidth=1
)

info_label.place(
    x=5,
    y=540,
    width=1280,
    height=35
)

load_queue()


root.queue_data = queue_data
root.save_queue = save_queue
root.info_label = info_label

buttons = create_control_buttons(
    root,
    config
)

root.protocol(
    "WM_DELETE_WINDOW",
    root.request_close
)

action_combobox = ttk.Combobox(
    root,
    values=(
        "No Action",
        "Stop After Current Task"
    ),
    state="readonly"
)

action_combobox.current(0)

root.action_combobox = action_combobox
root.action_index = action_combobox.current()


def update_action_index(event=None):
    root.action_index = action_combobox.current()


action_combobox.bind(
    "<<ComboboxSelected>>",
    update_action_index
)

action_combobox.place(
    x=1290,
    y=540,
    width=200,
    height=35
)


tree = create_treeview(
    root,
    queue_data,
    get_profiles,
    validate_file,
    validate_time,
    save_queue,
    info_label,
    BASE_DIR
)

setup_drag_drop(
    root,
    tree,
    queue_data,
    profile_combobox,
    info_label,
    config["video_extensions"],
    config["exclude_keywords"],
    save_queue,
    update_queue_info
)

if sys.platform.startswith("win"):
    ffprobe_path = config["ffprobe_win"]
else:
    ffprobe_path = config["ffprobe_linux"]

create_menu(
    root,
    queue_data,
    config,
    save_queue,
    ffprobe_path,
    WINDOW_TITLE,
    info_label
)


update_title(
    root,
    WINDOW_TITLE,
    DEBUG_POSITION
)



root.mainloop()
