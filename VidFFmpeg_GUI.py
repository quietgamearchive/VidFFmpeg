import sys
sys.dont_write_bytecode = True




# Detach from the parent console when run by python.exe (dev mode only).
if sys.platform == "win32" and not getattr(sys, "frozen", False):
    import ctypes
    import io

    kernel32 = ctypes.windll.kernel32

    if kernel32.GetConsoleWindow() and kernel32.FreeConsole():
        # Detached from the console: discard stdout/stderr so later
        # print() calls do not raise OSError on the invalid handle.
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()







from tkinterdnd2 import TkinterDnD
import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path
import os
import re
from tkinter import messagebox




if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from gui.menu import create_menu
from gui.treeview import (
    create_treeview,
    update_queue_info
)
from gui.treeview_dragdrop import setup_drag_drop
from gui.btns import create_control_buttons
from gui.debug import update_title
from gui.config import (
    GetWindowPosition,
    LoadConfig,
    SaveConfig
)
from gui.profile_selector import create_profile_selector
from gui.paged_treeview import (
    ErrorTreeview,
    FinishedTreeview,
    create_pages
)


WINDOW_WIDTH = 1500
WINDOW_HEIGHT = 600

DEBUG_POSITION = False
# DEBUG_POSITION = True

WINDOW_TITLE = (
    "VidFFmpeg - GUI "
    + "v0.02 Rev.260823"
)

QUEUE_FILE = "queue.json"
PROFILE_DIR = "profiles"

queue_file = BASE_DIR / QUEUE_FILE
profile_dir = BASE_DIR / PROFILE_DIR


# Kernel-level single-instance lock (no lock file): the returned
# object must stay referenced for the whole process lifetime.
from common.single_instance import acquire_single_instance

_instance_lock = acquire_single_instance("vidffmpeg_gui")

if not _instance_lock:
    messagebox.showwarning(
        "VidFFmpeg",
        "VidFFmpeg is already running.\n"
        "Please use the already opened window."
    )
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
root.withdraw()

# root.iconbitmap(
#     BASE_DIR / "VidFFmpeg.ico"
# )

if getattr(sys, "frozen", False):
    pass  # Packaged build: no icon set here, let the exe icon take over
else:
    root.iconbitmap(BASE_DIR / "VidFFmpeg.ico")  # Dev build only


screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()

x, y = GetWindowPosition(
    config,
    screen_w,
    screen_h,
    WINDOW_WIDTH,
    WINDOW_HEIGHT
)

root.geometry(
    f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}"
)


def save_window_config():
    config["Left"] = root.winfo_x()
    config["Top"] = root.winfo_y()
    SaveConfig(config)


root.save_window_config = save_window_config

root.resizable(
    False,
    False
)






profile_combobox = create_profile_selector(
    root,
    profile_dir,
    config,
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
    wraplength=0,
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
        "Stop After Current Task",
        "Close Application"
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


pages, current_page, finished_page, error_page = create_pages(root)

tree = create_treeview(
    current_page,
    queue_data,
    get_profiles,
    validate_file,
    validate_time,
    save_queue,
    info_label,
    BASE_DIR
)

finished_treeview = FinishedTreeview(
    finished_page,
    BASE_DIR / "finished.txt"
)

root.finished_treeview = finished_treeview

error_treeview = ErrorTreeview(
    error_page,
    BASE_DIR / "error.txt"
)

root.error_treeview = error_treeview

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

root.update_idletasks()
root.deiconify()


root.mainloop()
