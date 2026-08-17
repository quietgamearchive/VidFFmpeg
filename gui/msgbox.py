import tkinter as tk


def show_message(
    root,
    title,
    message,
    icon="information",
    buttons="ok"
):
    """
    Show a modal message box centered on the main window.

    icon:
        "information"
        "warning"
        "error"

    buttons:
        "ok"
        "okcancel"
        "yesno"

    Returns:
        "ok"
        "cancel"
        "yes"
        "no"
    """

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
        if buttons == "yesno":
            close("yes")
        else:
            close("ok")

    def on_escape(event=None):
        if buttons == "ok":
            close("ok")
        else:
            close("cancel")

    dialog.bind("<Return>", on_return)
    dialog.bind("<Escape>", on_escape)

    # Select the icon
    icon_text = {
        "information": "ⓘ",
        "warning": "⚠",
        "error": "✕"
    }.get(icon, "")

    content_frame = tk.Frame(dialog)
    content_frame.pack(
        padx=30,
        pady=(25, 20)
    )

    if icon_text:
        icon_label = tk.Label(
            content_frame,
            text=icon_text,
            font=("Segoe UI", 24)
        )
        icon_label.pack(
            side="left",
            padx=(0, 15)
        )

    message_label = tk.Label(
        content_frame,
        text=message,
        justify="left",
        anchor="w"
    )
    message_label.pack(
        side="left"
    )

    # Create buttons
    btn_frame = tk.Frame(dialog)
    btn_frame.pack(
        pady=(0, 15)
    )

    if buttons == "ok":
        tk.Button(
            btn_frame,
            text="OK",
            width=10,
            command=lambda: close("ok")
        ).pack()

    elif buttons == "okcancel":
        tk.Button(
            btn_frame,
            text="OK",
            width=10,
            command=lambda: close("ok")
        ).pack(
            side="left",
            padx=10
        )

        tk.Button(
            btn_frame,
            text="Cancel",
            width=10,
            command=lambda: close("cancel")
        ).pack(
            side="left",
            padx=10
        )

    elif buttons == "yesno":
        tk.Button(
            btn_frame,
            text="Yes",
            width=10,
            command=lambda: close("yes")
        ).pack(
            side="left",
            padx=10
        )

        tk.Button(
            btn_frame,
            text="No",
            width=10,
            command=lambda: close("no")
        ).pack(
            side="left",
            padx=10
        )

    else:
        raise ValueError(
            f"Unsupported button type: {buttons}"
        )

    # Calculate the actual window size
    dialog.update_idletasks()

    # Center the dialog on the main window
    root.update_idletasks()

    x = root.winfo_x() + (
        root.winfo_width() - dialog.winfo_width()
    ) // 2

    y = root.winfo_y() + (
        root.winfo_height() - dialog.winfo_height()
    ) // 2

    dialog.geometry(
        f"+{x}+{y}"
    )

    # Show the dialog
    dialog.deiconify()
    dialog.grab_set()
    dialog.focus_set()

    # Wait until the dialog is closed
    root.wait_window(dialog)

    return result["value"]






#from gui.msgbox import show_message

#Information + OK：

#show_message(
#    root,
#    "Information",
#    "Conversion completed successfully.",
#    icon="information",
#    buttons="ok"
#)

#Warning + OK：

#show_message(
#    root,
#    "Warning",
#    "Some files could not be found.",
#    icon="warning",
#    buttons="ok"
#)

#Error + OK：

#show_message(
#    root,
#    "Error",
#    "Failed to load queue.json.",
#    icon="error",
#    buttons="ok"
#)

#Question + Yes/No：

#result = show_message(
#    root,
#    "Confirm",
#    "Are you sure you want to delete this file?",
#    icon="question",
#    buttons="yesno"
#)


#if result == "yes":
#    print("User selected Yes")
#else:
#    print("User selected No")

#Warning + OK/Cancel：

#result = show_message(
#    root,
#    "Confirm",
#    "Do you want to continue?",
#    icon="warning",
#    buttons="okcancel"
#)


#if result == "ok":
#    print("User selected OK")
#else:
#    print("User selected Cancel")

#keyboard：

#OK
#    Enter → ok
#    Esc   → ok


#OK / Cancel
#    Enter → ok
#    Esc   → cancel


#Yes / No
#    Enter → yes
#    Esc   → no



#show_message(root, "Error", "Something went wrong.", "error")





