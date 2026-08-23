import tkinter as tk
from tkinter import ttk

from .treeview_contextmenu import create_context_menu
from .paged_treeview import (
    NUM_COLUMN_STRETCH,
    NUM_COLUMN_WIDTH,
)


tree = None
editor = None
editor_item = None
editor_column = None
tree_scroll_position = None

conversion_running = False


def is_conversion_running():
    return conversion_running


def set_conversion_running(value):
    global conversion_running

    conversion_running = bool(value)

    hide_editor()


def refresh_tree(queue_data):
    if tree is None:
        return

    tree.delete(
        *tree.get_children()
    )

    for index, item in enumerate(queue_data):
        tree.insert(
            "",
            "end",
            text=str(index),
            values=(
                index + 1,
                item.get("file", ""),
                item.get("profile", ""),
                item.get("start", ""),
                item.get("end", ""),
                item.get("progress", "")
            )
        )


def update_queue_info(
    info_label,
    queue_data
):
    total = len(queue_data)

    cut_required = 0

    for item in queue_data:
        if (
            item.get("start")
            or item.get("end")
        ):
            cut_required += 1

    info_label.config(
        text=(
            f"Total files: {total}\n"
            f"Cut required: {cut_required}"
        )
    )


def update_conversion_info(
    info_label,
    text
):
    info_label.config(
        text=text
    )


def update_progress(
    value
):
    if tree is None:
        return

    children = tree.get_children()

    if not children:
        return

    first_item = children[0]

    tree.set(
        first_item,
        "progress",
        value
    )


def clear_first_progress():
    if tree is None:
        return

    children = tree.get_children()

    if not children:
        return

    tree.set(
        children[0],
        "progress",
        ""
    )


def hide_editor():
    global editor
    global editor_item
    global editor_column

    if editor:
        try:
            editor.destroy()
        except Exception:
            pass

    editor = None
    editor_item = None
    editor_column = None


def cancel_editor(
    event=None
):
    hide_editor()


def ignore_middle_click(event):
    return "break"


def save_editor(
    event,
    queue_data,
    validate_file,
    validate_time,
    save_queue,
    info_label
):
    global editor
    global editor_item
    global editor_column

    if not editor:
        return

    value = editor.get()

    row = int(
        tree.item(
            editor_item,
            "text"
        )
    )

    if conversion_running and row == 0:
        hide_editor()
        return

    key = {
        "#2": "file",
        "#3": "profile",
        "#4": "start",
        "#5": "end"
    }[editor_column]

    if key == "file":
        if not validate_file(value):
            hide_editor()
            return

    if key in (
        "start",
        "end"
    ):
        if not validate_time(value):
            hide_editor()
            return

    queue_data[row][key] = value

    tree.set(
        editor_item,
        editor_column,
        value
    )

    save_queue()

    update_queue_info(
        info_label,
        queue_data
    )

    hide_editor()


def lock_tree_position(
    root
):
    if tree_scroll_position:
        tree.yview_moveto(
            tree_scroll_position[0]
        )

    if editor:
        root.after(
            50,
            lambda: lock_tree_position(
                root
            )
        )


def click_outside(
    event
):
    if editor and event.widget != editor:
        hide_editor()


def clear_selection_on_blank(event):
    if tree.identify_region(
        event.x,
        event.y
    ) == "nothing":
        tree.selection_remove(
            tree.selection()
        )


def start_edit(
    event,
    queue_data,
    get_profiles,
    validate_file,
    validate_time,
    save_queue,
    info_label,
    root
):
    global tree_scroll_position
    global editor
    global editor_item
    global editor_column

    hide_editor()

    tree.selection_remove(
        tree.selection()
    )

    tree_scroll_position = tree.yview()

    item = tree.identify_row(
        event.y
    )

    column = tree.identify_column(
        event.x
    )

    if not item:
        return

    row = int(
        tree.item(
            item,
            "text"
        )
    )

    if conversion_running and row == 0:
        return

    if column not in (
        "#2",
        "#3",
        "#4",
        "#5"
    ):
        return

    bbox = tree.bbox(
        item,
        column
    )

    if not bbox:
        return

    x, y, width, height = bbox

    editor_item = item
    editor_column = column

    old_value = tree.set(
        item,
        column
    )

    if column == "#3":
        editor = ttk.Combobox(
            tree,
            values=get_profiles(),
            state="readonly"
        )

        editor.set(
            old_value
        )

    else:
        editor = tk.Entry(
            tree
        )

        editor.insert(
            0,
            old_value
        )

        editor.select_range(
            0,
            tk.END
        )

    editor.place(
        x=x,
        y=y,
        width=width,
        height=height
    )

    editor.focus_set()

    for sequence in (
        "<Button-2>",
        "<B2-Motion>",
        "<ButtonRelease-2>",
        "<<PasteSelection>>",
    ):
        editor.bind(
            sequence,
            ignore_middle_click,
        )

    lock_tree_position(
        root
    )

    editor.bind(
        "<Return>",
        lambda event: save_editor(
            event,
            queue_data,
            validate_file,
            validate_time,
            save_queue,
            info_label
        )
    )

    editor.bind(
        "<Escape>",
        cancel_editor
    )

def create_treeview(
    parent,
    queue_data,
    get_profiles,
    validate_file,
    validate_time,
    save_queue,
    info_label,
    base_dir
):
    global tree

    tree = ttk.Treeview(
        parent,
        columns=(
            "num",
            "file",
            "profile",
            "start",
            "end",
            "progress"
        ),
        show="headings",
        selectmode="extended"
    )

    tree.heading(
        "num",
        text="Num"
    )

    tree.heading(
        "file",
        text="File"
    )

    tree.heading(
        "profile",
        text="Profile"
    )

    tree.heading(
        "start",
        text="Start"
    )

    tree.heading(
        "end",
        text="End"
    )

    tree.heading(
        "progress",
        text="Progress"
    )

    tree.column(
        "num",
        width=NUM_COLUMN_WIDTH,
        anchor="center",
        stretch=NUM_COLUMN_STRETCH
    )

    tree.column(
        "file",
        width=850
    )

    tree.column(
        "profile",
        width=200
    )

    tree.column(
        "start",
        width=30,
        anchor="center"
    )

    tree.column(
        "end",
        width=30,
        anchor="center"
    )

    tree.column(
        "progress",
        width=70,
        anchor="center"
    )

    scroll = ttk.Scrollbar(
        parent,
        orient="vertical",
        command=tree.yview
    )

    tree.pack(
        side=tk.LEFT,
        fill=tk.BOTH,
        expand=True
    )

    scroll.pack(
        side=tk.RIGHT,
        fill=tk.Y
    )

    tree.configure(
        yscrollcommand=scroll.set
    )

    refresh_tree(
        queue_data
    )

    tree.bind(
        "<Button-2>",
        lambda event: start_edit(
            event,
            queue_data,
            get_profiles,
            validate_file,
            validate_time,
            save_queue,
            info_label,
            parent
        )
    )

    tree.bind(
        "<Button-1>",
        clear_selection_on_blank
    )

    tree.bind(
        "<Button-1>",
        click_outside,
        add="+"
    )

    create_context_menu(
        parent.winfo_toplevel(),
        tree,
        queue_data,
        save_queue,
        lambda: update_queue_info(
            info_label,
            queue_data
        ),
        base_dir,
        is_conversion_running
    )

    update_queue_info(
        info_label,
        queue_data
    )

    return tree
