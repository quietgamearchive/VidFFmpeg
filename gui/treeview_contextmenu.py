import json
import tkinter as tk
from tkinter import filedialog

from .msgbox import show_message


def get_selected_indexes(tree):
    selected = tree.selection()

    indexes = []

    for item in selected:
        try:
            index = int(tree.item(item, "text"))
            indexes.append(index)
        except (ValueError, TypeError):
            pass

    return sorted(indexes)


def refresh_tree(tree, queue_data):
    tree.delete(*tree.get_children())

    for index, item in enumerate(queue_data):
        tree.insert(
            "",
            "end",
            text=str(index),
            values=(
                item.get("file", ""),
                item.get("profile", ""),
                item.get("start", ""),
                item.get("end", ""),
                item.get("progress", "")
            )
        )


def move_up(
    tree,
    queue_data,
    save_queue,
    update_statistics,
    is_conversion_running
):
    indexes = get_selected_indexes(tree)

    if not indexes:
        return

    if (
        is_conversion_running()
        and indexes[0] <= 1
    ):
        return

    if indexes[0] <= 0:
        return

    for index in indexes:
        queue_data[index - 1], queue_data[index] = (
            queue_data[index],
            queue_data[index - 1]
        )

    save_queue()

    refresh_tree(
        tree,
        queue_data
    )

    new_selection = []

    for index in indexes:
        item = tree.get_children()[index - 1]
        new_selection.append(item)

    tree.selection_set(new_selection)

    update_statistics()


def move_down(
    tree,
    queue_data,
    save_queue,
    update_statistics,
    is_conversion_running
):
    indexes = get_selected_indexes(tree)

    if not indexes:
        return

    if (
        is_conversion_running()
        and 0 in indexes
    ):
        return

    last_index = len(queue_data) - 1

    if indexes[-1] >= last_index:
        return

    for index in reversed(indexes):
        queue_data[index + 1], queue_data[index] = (
            queue_data[index],
            queue_data[index + 1]
        )

    save_queue()

    refresh_tree(
        tree,
        queue_data
    )

    new_selection = []

    for index in indexes:
        item = tree.get_children()[index + 1]
        new_selection.append(item)

    tree.selection_set(new_selection)

    update_statistics()


def move_to_top(
    tree,
    queue_data,
    save_queue,
    update_statistics,
    is_conversion_running
):
    indexes = get_selected_indexes(tree)

    if not indexes:
        return

    if (
        is_conversion_running()
        and any(index != 0 for index in indexes)
    ):
        return

    selected_items = [
        queue_data[index]
        for index in indexes
    ]

    remaining_items = [
        item
        for index, item in enumerate(queue_data)
        if index not in indexes
    ]

    queue_data[:] = selected_items + remaining_items

    save_queue()

    refresh_tree(
        tree,
        queue_data
    )

    new_selection = []

    for index in range(len(selected_items)):
        new_selection.append(
            tree.get_children()[index]
        )

    tree.selection_set(new_selection)

    update_statistics()


def move_to_bottom(
    tree,
    queue_data,
    save_queue,
    update_statistics,
    is_conversion_running
):
    indexes = get_selected_indexes(tree)

    if not indexes:
        return

    if (
        is_conversion_running()
        and 0 in indexes
    ):
        return

    selected_items = [
        queue_data[index]
        for index in indexes
    ]

    remaining_items = [
        item
        for index, item in enumerate(queue_data)
        if index not in indexes
    ]

    queue_data[:] = remaining_items + selected_items

    save_queue()

    refresh_tree(
        tree,
        queue_data
    )

    start_index = len(remaining_items)

    new_selection = []

    for index in range(len(selected_items)):
        new_selection.append(
            tree.get_children()[start_index + index]
        )

    tree.selection_set(new_selection)

    update_statistics()


def delete_selected(
    root,
    tree,
    queue_data,
    save_queue,
    update_statistics,
    is_conversion_running
):
    indexes = get_selected_indexes(tree)

    if not indexes:
        return

    if is_conversion_running():
        indexes = [
            index
            for index in indexes
            if index != 0
        ]

        if not indexes:
            return

    result = show_message(
        root,
        "Confirm Delete",
        "Are you sure you want to delete the selected items?",
        icon="warning",
        buttons="yesno"
    )

    if result != "yes":
        return

    for index in reversed(indexes):
        del queue_data[index]

    save_queue()

    refresh_tree(
        tree,
        queue_data
    )

    update_statistics()


def delete_all(
    root,
    tree,
    queue_data,
    save_queue,
    update_statistics,
    is_conversion_running
):
    if not queue_data:
        return

    result = show_message(
        root,
        "Confirm Delete All",
        "Are you sure you want to delete all items?",
        icon="warning",
        buttons="yesno"
    )

    if result != "yes":
        return

    if is_conversion_running():
        del queue_data[1:]
    else:
        queue_data.clear()

    save_queue()

    refresh_tree(
        tree,
        queue_data
    )

    update_statistics()


def import_queue(
    root,
    tree,
    queue_data,
    save_queue,
    update_statistics,
    base_dir,
    is_conversion_running
):
    if is_conversion_running():
        return

    path = filedialog.askopenfilename(
        parent=root,
        title="Import Queue",
        initialdir=str(base_dir),
        filetypes=(
            ("JSON files", "*.json"),
            ("All files", "*.*")
        )
    )

    if not path:
        return

    try:
        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:
            imported_data = json.load(f)

    except Exception as e:
        show_message(
            root,
            "Import Error",
            f"Failed to import queue:\n\n{e}",
            icon="error",
            buttons="ok"
        )
        return

    if not isinstance(imported_data, list):
        show_message(
            root,
            "Import Error",
            "The selected file does not contain a valid queue.",
            icon="error",
            buttons="ok"
        )
        return

    queue_data[:] = imported_data

    save_queue(force=True)

    refresh_tree(
        tree,
        queue_data
    )

    update_statistics()


def export_queue(
    root,
    queue_data,
    base_dir,
    is_conversion_running
):
    if is_conversion_running():
        return

    path = filedialog.asksaveasfilename(
        parent=root,
        title="Export Queue",
        initialdir=str(base_dir),
        initialfile="export.json",
        defaultextension=".json",
        filetypes=(
            ("JSON files", "*.json"),
            ("All files", "*.*")
        )
    )

    if not path:
        return

    try:
        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                queue_data,
                f,
                indent=4,
                ensure_ascii=False
            )

    except Exception as e:
        show_message(
            root,
            "Export Error",
            f"Failed to export queue:\n\n{e}",
            icon="error",
            buttons="ok"
        )
        return


def create_context_menu(
    root,
    tree,
    queue_data,
    save_queue,
    update_statistics,
    base_dir,
    is_conversion_running
):
    menu = tk.Menu(
        root,
        tearoff=0
    )

    menu.add_command(
        label="Move Up",
        command=lambda: move_up(
            tree,
            queue_data,
            save_queue,
            update_statistics,
            is_conversion_running
        )
    )

    menu.add_command(
        label="Move Down",
        command=lambda: move_down(
            tree,
            queue_data,
            save_queue,
            update_statistics,
            is_conversion_running
        )
    )

    menu.add_command(
        label="Move to Top",
        command=lambda: move_to_top(
            tree,
            queue_data,
            save_queue,
            update_statistics,
            is_conversion_running
        )
    )

    menu.add_command(
        label="Move to Bottom",
        command=lambda: move_to_bottom(
            tree,
            queue_data,
            save_queue,
            update_statistics,
            is_conversion_running
        )
    )

    menu.add_separator()

    menu.add_command(
        label="Delete Selected",
        command=lambda: delete_selected(
            root,
            tree,
            queue_data,
            save_queue,
            update_statistics,
            is_conversion_running
        )
    )

    menu.add_command(
        label="Delete All",
        command=lambda: delete_all(
            root,
            tree,
            queue_data,
            save_queue,
            update_statistics,
            is_conversion_running
        )
    )

    menu.add_separator()

    menu.add_command(
        label="Import Queue...",
        command=lambda: import_queue(
            root,
            tree,
            queue_data,
            save_queue,
            update_statistics,
            base_dir,
            is_conversion_running
        )
    )

    menu.add_command(
        label="Export Queue...",
        command=lambda: export_queue(
            root,
            queue_data,
            base_dir,
            is_conversion_running
        )
    )

    def show_menu(event):
        selected = tree.selection()
        indexes = get_selected_indexes(tree)
        running = is_conversion_running()

        can_delete_selected = bool(
            selected
            and (
                not running
                or any(index != 0 for index in indexes)
            )
        )

        if can_delete_selected:
            menu.entryconfigure(
                "Delete Selected",
                state="normal"
            )
        else:
            menu.entryconfigure(
                "Delete Selected",
                state="disabled"
            )

        menu.entryconfigure(
            "Import Queue...",
            state=(
                "disabled"
                if running
                else "normal"
            )
        )

        menu.entryconfigure(
            "Export Queue...",
            state=(
                "disabled"
                if running
                else "normal"
            )
        )

        menu.tk_popup(
            event.x_root,
            event.y_root
        )

    tree.bind(
        "<Button-3>",
        show_menu,
        add="+"
    )

    return menu
