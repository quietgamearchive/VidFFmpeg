import tkinter as tk


def show_message(
    root,
    title,
    message,
    icon="information",
    buttons="ok"
):
    dialog = tk.Toplevel(root)
    dialog.withdraw()
    dialog.title(title)
    dialog.resizable(False, False)
    dialog.transient(root)

    result = {"value": None}

    def close(value):
        result["value"] = value
        dialog.destroy()

    def on_return(event=None):
        close("yes" if buttons == "yesno" else "ok")

    def on_escape(event=None):
        close("ok" if buttons == "ok" else "cancel")

    dialog.bind("<Return>", on_return)
    dialog.bind("<Escape>", on_escape)

    icon_text = {
        "information": "i",
        "warning": "!",
        "error": "x",
        "question": "?",
    }.get(icon, "")

    content_frame = tk.Frame(dialog)
    content_frame.pack(padx=30, pady=(25, 20))

    if icon_text:
        icon_label = tk.Label(
            content_frame,
            text=icon_text,
            font=("Segoe UI", 24, "bold")
        )
        icon_label.pack(side="left", padx=(0, 15))

    message_label = tk.Label(
        content_frame,
        text=message,
        justify="left",
        anchor="w"
    )
    message_label.pack(side="left")

    button_frame = tk.Frame(dialog)
    button_frame.pack(pady=(0, 15))

    def add_button(text, value, side=None):
        button = tk.Button(
            button_frame,
            text=text,
            width=10,
            command=lambda: close(value)
        )
        if side:
            button.pack(side=side, padx=10)
        else:
            button.pack()

    if buttons == "ok":
        add_button("OK", "ok")
    elif buttons == "okcancel":
        add_button("OK", "ok", "left")
        add_button("Cancel", "cancel", "left")
    elif buttons == "yesno":
        add_button("Yes", "yes", "left")
        add_button("No", "no", "left")
    else:
        raise ValueError(f"Unsupported button type: {buttons}")

    dialog.update_idletasks()
    root.update_idletasks()

    x = root.winfo_x() + (
        root.winfo_width() - dialog.winfo_width()
    ) // 2
    y = root.winfo_y() + (
        root.winfo_height() - dialog.winfo_height()
    ) // 2

    dialog.geometry(f"+{x}+{y}")
    dialog.deiconify()
    dialog.grab_set()
    dialog.focus_set()
    root.wait_window(dialog)

    return result["value"]
