import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path
import os
import re

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600
DEBUG_POSITION = False
#DEBUG_POSITION = True

WINDOW_TITLE = "VidFFmpeg - GUI Queue Manager " + "v1.00 Rev.260811"

QUEUE_FILE = "queue.json"
PROFILE_DIR = "profiles"

BASE_DIR = Path(__file__).parent
queue_file = BASE_DIR / QUEUE_FILE
profile_dir = BASE_DIR / PROFILE_DIR

tree_scroll_position = None
queue_data = []
editor = None
editor_item = None
editor_column = None

def load_queue():
    global queue_data
    try:
        with open(queue_file, "r", encoding="utf-8") as f:
            queue_data = json.load(f)
    except Exception as e:
        print(e)
        queue_data = []

def save_queue():
    with open(queue_file, "w", encoding="utf-8") as f:
        json.dump(queue_data, f, indent=4, ensure_ascii=False)

def get_profiles():
    if not profile_dir.exists():
        return []
    return sorted([p.name for p in profile_dir.glob("*.json")])

def validate_file(value):
    return os.path.isfile(value)

def validate_time(value):
    if value == "":
        return True
    return bool(re.fullmatch(r"\d{2}:\d{2}:\d{2}", value))

def update_statistics():
    total = len(queue_data)
    need_cut = 0
    profiles = {}

    for item in queue_data:
        if item.get("start") or item.get("end"):
            need_cut += 1

        profile = item.get("profile", "")
        if profile:
            profiles[profile] = profiles.get(profile, 0) + 1

    text = f"Total files: {total}\n"
    text += f"Need cut: {need_cut}\n"

    if profiles:
        text += "\nProfile:\n"
        for name, count in profiles.items():
            if count > 0:
                text += f"{name} : {count}\n"

    info_label.config(text=text)

def hide_editor():
    global editor, editor_item, editor_column
    if editor:
        editor.destroy()
    editor = None
    editor_item = None
    editor_column = None

def cancel_editor(event=None):
    hide_editor()

def save_editor(event=None):
    global editor

    if not editor:
        return

    value = editor.get()

    row = int(tree.item(editor_item, "text"))

    key = {
        "#1": "file",
        "#2": "profile",
        "#3": "start",
        "#4": "end"
    }[editor_column]

    if key == "file":
        if not validate_file(value):
            hide_editor()
            return

    if key in ("start", "end"):
        if not validate_time(value):
            hide_editor()
            return

    queue_data[row][key] = value

    tree.set(editor_item, editor_column, value)

    save_queue()
    update_statistics()

    hide_editor()

def lock_tree_position():
    if tree_scroll_position:
        tree.yview_moveto(
            tree_scroll_position[0]
        )

    if editor:
        root.after(
            50,
            lock_tree_position
        )


def start_edit(event):
    global tree_scroll_position
    global editor, editor_item, editor_column

    hide_editor()
    
    # 取消 Treeview 当前选中
    tree.selection_remove(
        tree.selection()
    )

    tree_scroll_position = tree.yview()

    item = tree.identify_row(event.y)
    column = tree.identify_column(event.x)

    if not item:
        return

    if column not in ("#1", "#2", "#3", "#4"):
        return

    bbox = tree.bbox(item, column)

    if not bbox:
        return

    x, y, width, height = bbox

    editor_item = item
    editor_column = column

    old_value = tree.set(item, column)

    if column == "#2":
        editor = ttk.Combobox(
            tree,
            values=get_profiles(),
            state="readonly"
        )
        editor.set(old_value)
    else:
        editor = tk.Entry(tree)
        editor.insert(0, old_value)
        editor.select_range(0, tk.END)

    editor.place(
        x=x,
        y=y,
        width=width,
        height=height
    )

    editor.focus_set()
    lock_tree_position()

    editor.bind("<Return>", save_editor)
    editor.bind("<Escape>", cancel_editor)

    root.bind("<Button-1>", click_outside, add="+")

def click_outside(event):
    if editor and event.widget != editor:
        hide_editor()

def update_title():
    if DEBUG_POSITION:
        root.title(
            f"{WINDOW_TITLE} | "
            f"X:{root.winfo_x()} Y:{root.winfo_y()} "
            f"Width:{root.winfo_width()} Height:{root.winfo_height()}"
        )
    else:
        root.title(WINDOW_TITLE)

    root.after(200, update_title)

root = tk.Tk()

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()

x = (screen_w - WINDOW_WIDTH) // 2
y = (screen_h - WINDOW_HEIGHT) // 2

root.geometry(
    f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}"
)

main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True)

tree_frame = tk.Frame(main_frame)
tree_frame.pack(
    fill="both",
    expand=True,
    padx=5,
    pady=5
)

tree = ttk.Treeview(
    tree_frame,
    columns=("file", "profile", "start", "end"),
    show="headings"
)

tree.heading("file", text="File")
tree.heading("profile", text="Profile")
tree.heading("start", text="Start")
tree.heading("end", text="End")

tree.column("file", width=500)
tree.column("profile", width=220)
tree.column("start", width=100)
tree.column("end", width=100)

scroll = ttk.Scrollbar(
    tree_frame,
    orient="vertical",
    command=tree.yview
)

tree.configure(
    yscrollcommand=scroll.set
)

tree.pack(
    side="left",
    fill="both",
    expand=True
)

scroll.pack(
    side="right",
    fill="y"
)

info_label = tk.Label(
    main_frame,
    text="Statistics",
    anchor="nw",
    justify="left",
    height=6
)

info_label.pack(
    fill="x",
    padx=10,
    pady=10
)

load_queue()

for index, item in enumerate(queue_data):
    tree.insert(
        "",
        "end",
        text=str(index),
        values=(
            item.get("file", ""),
            item.get("profile", ""),
            item.get("start", ""),
            item.get("end", "")
        )
    )

tree.bind("<Button-2>", start_edit)

update_statistics()
update_title()

root.mainloop()