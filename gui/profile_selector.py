import tkinter as tk
from tkinter import ttk
import json

from .msgbox import show_message


profile_combobox = None


def get_profiles(profile_dir):
    if not profile_dir.exists():
        return []

    return sorted(
        [
            p.name
            for p in profile_dir.glob("*.json")
        ]
    )


def validate_profile(
    profile_dir,
    profile_name
):
    profile_file = profile_dir / profile_name

    try:
        with open(
            profile_file,
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

    except Exception:
        return False

    if not isinstance(data, dict):
        return False

    required_keys = (
        "name",
        "ffmpeg_args",
        "output",
        "after_finish"
    )

    for key in required_keys:
        if key not in data:
            return False

    return True


def create_profile_selector(
    parent,
    profile_dir,
    config,
    x=1000,
    y=5,
    width=300,
    height=30
):
    global profile_combobox

    label = tk.Label(
        parent,
        text="Profile:",
        anchor="w"
    )

    label.place(
        x=x,
        y=y,
        width=55,
        height=height
    )

    profile_combobox = ttk.Combobox(
        parent,
        state="readonly"
    )

    profile_combobox.place(
        x=x + 60,
        y=y,
        width=width - 60,
        height=height
    )

    def refresh_profiles():
        profiles = get_profiles(
            profile_dir
        )

        current_value = config.get(
            "current_profile",
            ""
        )

        profile_combobox["values"] = profiles

        if not profiles:
            profile_combobox.set("")

            if current_value != "":
                config["current_profile"] = ""

            return

        if current_value in profiles:
            profile_combobox.current(
                profiles.index(
                    current_value
                )
            )

        else:
            profile_combobox.current(0)

            if current_value != "":
                config["current_profile"] = ""

    def profile_selected(event=None):
        new_profile = profile_combobox.get()

        if not new_profile:
            return

        old_profile = config.get(
            "current_profile",
            ""
        )

        if not validate_profile(
            profile_dir,
            new_profile
        ):
            show_message(
                parent,
                "Invalid Profile",
                "This is not a valid profile.",
                icon="error",
                buttons="ok"
            )

            profiles = get_profiles(
                profile_dir
            )

            if old_profile in profiles:
                profile_combobox.current(
                    profiles.index(
                        old_profile
                    )
                )

            else:
                if profiles:
                    profile_combobox.current(0)
                else:
                    profile_combobox.set("")

            return

        config["current_profile"] = new_profile

    profile_combobox.configure(
        postcommand=refresh_profiles
    )

    profile_combobox.bind(
        "<<ComboboxSelected>>",
        profile_selected
    )

    refresh_profiles()

    return profile_combobox