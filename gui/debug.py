def update_title(
    root,
    window_title,
    debug_position
):
    if debug_position:
        root.title(
            f"{window_title} | "
            f"X:{root.winfo_x()} "
            f"Y:{root.winfo_y()} "
            f"Width:{root.winfo_width()} "
            f"Height:{root.winfo_height()}"
        )
    else:
        root.title(
            window_title
        )

    root.after(
        200,
        update_title,
        root,
        window_title,
        debug_position
    )