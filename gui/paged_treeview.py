import re
import tkinter as tk
from tkinter import ttk

from .msgbox import show_message


NUM_COLUMN = "num"
NUM_COLUMN_HEADING = "Num"
NUM_COLUMN_WIDTH = 50
NUM_COLUMN_STRETCH = False


def create_pages(parent):
    notebook = ttk.Notebook(parent)
    notebook.place(x=5, y=50, width=1490, height=485)

    current_page = ttk.Frame(notebook)
    finished_page = ttk.Frame(notebook)
    error_page = ttk.Frame(notebook)

    notebook.add(current_page, text="Current")
    notebook.add(finished_page, text="Finished")
    notebook.add(error_page, text="Error")

    return notebook, current_page, finished_page, error_page


class LogTreeview:
    def __init__(self, parent, log_file, columns, headings, widths):
        self.log_file = log_file
        self.root = parent.winfo_toplevel()
        self.row_line_indexes = []
        self.columns = (NUM_COLUMN, *columns)
        headings = {
            NUM_COLUMN: NUM_COLUMN_HEADING,
            **headings,
        }
        widths = {
            NUM_COLUMN: NUM_COLUMN_WIDTH,
            **widths,
        }
        self.tree = ttk.Treeview(
            parent,
            columns=self.columns,
            show="headings",
            selectmode="extended",
        )

        for column in self.columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(
                column,
                width=widths[column],
                anchor="w" if column == self.columns[1] else "center",
                stretch=(
                    NUM_COLUMN_STRETCH
                    if column == NUM_COLUMN
                    else True
                ),
            )

        scroll = ttk.Scrollbar(
            parent,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind(
            "<Button-1>",
            self.clear_selection_on_blank,
        )
        self.tree.bind(
            "<Button-2>",
            self.clear_selection_on_middle_click,
        )

        self.context_menu = tk.Menu(
            self.root,
            tearoff=0,
        )
        self.context_menu.add_command(
            label="Delete selected",
            command=self.delete_selected,
        )
        self.context_menu.add_command(
            label="Delete all",
            command=self.delete_all,
        )
        self.tree.bind(
            "<Button-3>",
            self.show_context_menu,
        )

        self.reload()

    def clear_selection_on_blank(self, event):
        if self.tree.identify_region(event.x, event.y) == "nothing":
            self.tree.selection_remove(self.tree.selection())

    def clear_selection_on_middle_click(self, event):
        self.tree.selection_remove(self.tree.selection())

    def read_values(self):
        raise NotImplementedError

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item and item not in self.tree.selection():
            self.tree.selection_set(item)

        has_rows = bool(self.tree.get_children())
        has_selection = bool(self.tree.selection())
        self.context_menu.entryconfigure(
            "Delete selected",
            state="normal" if has_selection else "disabled",
        )
        self.context_menu.entryconfigure(
            "Delete all",
            state="normal" if has_rows else "disabled",
        )

        self.context_menu.tk_popup(
            event.x_root,
            event.y_root,
        )

    def delete_selected(self):
        items = self.tree.selection()
        if not items:
            return

        result = show_message(
            self.root,
            "Confirm Delete",
            "Are you sure you want to delete the selected items?",
            icon="warning",
            buttons="yesno",
        )
        if result != "yes":
            return

        indexes = sorted(
            self.tree.index(item)
            for item in items
        )
        self._delete_line_indexes(indexes)

    def delete_all(self):
        if not self.tree.get_children():
            return

        result = show_message(
            self.root,
            "Confirm Delete All",
            "Are you sure you want to delete all items?",
            icon="warning",
            buttons="yesno",
        )
        if result != "yes":
            return

        try:
            self.log_file.write_text(
                "",
                encoding="utf-8",
            )
        except (OSError, UnicodeError) as error:
            show_message(
                self.root,
                "Delete Error",
                f"Failed to update the log file:\n\n{error}",
                icon="error",
                buttons="ok",
            )
            return

        self.reload()

    def _delete_line_indexes(self, row_indexes):
        line_indexes = {
            self.row_line_indexes[index]
            for index in row_indexes
            if 0 <= index < len(self.row_line_indexes)
        }

        try:
            with self.log_file.open(
                "r",
                encoding="utf-8",
                newline="",
            ) as file:
                lines = file.readlines()

            with self.log_file.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as file:
                file.writelines(
                    line
                    for index, line in enumerate(lines)
                    if index not in line_indexes
                )
        except (OSError, UnicodeError) as error:
            show_message(
                self.root,
                "Delete Error",
                f"Failed to update the log file:\n\n{error}",
                icon="error",
                buttons="ok",
            )
            return

        self.reload()

    def reload(self):
        try:
            values = self.read_values()
        except (OSError, UnicodeError):
            return

        position = self.tree.yview()
        self.tree.delete(*self.tree.get_children())
        for number, row in enumerate(values, start=1):
            self.tree.insert(
                "",
                "end",
                values=(number, *row),
            )

        if position:
            self.tree.yview_moveto(position[0])


class FinishedTreeview(LogTreeview):
    columns = (
        "target_file",
        "original_duration",
        "conversion_time",
        "finish_time",
        "file_size",
        "percent",
    )

    def __init__(self, parent, finished_file):
        headings = {
            "target_file": "Target File Name",
            "original_duration": "Original Duration",
            "conversion_time": "Conversion Time",
            "finish_time": "Finish Time",
            "file_size": "File Size",
            "percent": "%",
        }

        widths = {
            "target_file": 700,
            "original_duration": 100,
            "conversion_time": 110,
            "finish_time": 150,
            "file_size": 100,
            "percent": 30,
        }
        super().__init__(
            parent,
            finished_file,
            self.columns,
            headings,
            widths,
        )

    @staticmethod
    def parse_line(line):
        line = line.rstrip("\r\n")

        parts = line.rsplit(" | ", 4)

        if len(parts) == 5:
            (
                target_and_duration,
                conversion_time,
                finish_time,
                file_size,
                percent,
            ) = parts
            match = re.match(
                r"^(.*) \((\d{2}:\d{2}(?::\d{2})?"
                r"(?: \([^)]*\))?)\)$",
                target_and_duration,
            )

            if match:
                return (
                    match.group(1),
                    match.group(2),
                    conversion_time,
                    finish_time,
                    file_size,
                    percent,
                )

        return (line, "", "", "", "", "")

    def read_values(self):
        self.row_line_indexes = []
        if not self.log_file.exists():
            return []

        values = []
        with self.log_file.open("r", encoding="utf-8") as file:
            for line_index, line in enumerate(file):
                row = self.parse_line(line)
                if row:
                    values.append(row)
                    self.row_line_indexes.append(line_index)
        return values


class ErrorTreeview(LogTreeview):
    columns = (
        "file_name",
        "finish_time",
        "error_reason",
    )

    def __init__(self, parent, error_file):
        headings = {
            "file_name": "File Name",
            "finish_time": "Finish Time",
            "error_reason": "Error Reason",
        }
        widths = {
            "file_name": 600,
            "finish_time": 150,
            "error_reason": 500,
        }
        super().__init__(
            parent,
            error_file,
            self.columns,
            headings,
            widths,
        )

    def read_values(self):
        self.row_line_indexes = []
        if not self.log_file.exists():
            return []

        values = []
        with self.log_file.open("r", encoding="utf-8") as file:
            for line_index, line in enumerate(file):
                raw_line = line.rstrip("\r\n")
                parts = raw_line.rsplit(" | ", 2)
                if len(parts) == 3:
                    values.append((parts[0], parts[1], parts[2]))
                else:
                    values.append((raw_line, "", ""))
                self.row_line_indexes.append(line_index)
        return values
