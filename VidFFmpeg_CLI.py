import sys
sys.dont_write_bytecode = True

from pathlib import Path



if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

# The embedded Python runtime does not always put the script directory on
# sys.path.  ``cli`` is a package inside BASE_DIR, so add BASE_DIR itself.
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from cli.config import LoadConfig
from cli.queuefile import load_queue
from cli.queuestatus import show_queue_stats
from cli.checkmissingfiles import check_missing_files
from cli.selprofile_addfiles import (
    select_profile_and_add_files
)
from cli.convert import convert_videos
from cli.startup_check_ffmpeg import check_ffmpeg_paths


APP_TITLE = (
    "VidFFmpeg - CLI "
    + "v0.02 Rev.260823"
)


def wait_exit():
    try:
        input("\nPress Enter to exit...")

    except KeyboardInterrupt:
        print()


def exit_program():
    print()
    print("==============================")
    print("Script exited")
    print("==============================")

    sys.exit(0)


def show_main_menu():
    queue = load_queue()

    print()
    print("=======================================")
    print(APP_TITLE)
    print("=======================================")
    print()

    print(
        f"Existing tasks: "
        f"{len(queue)}"
    )

    print()
    print("0. Queue statistics")
    print("a. Check missing files")
    print("b. Select profile & Add video files")
    print("c. Convert video")
    print()
    print()
    print("q. Exit")

    return input(
        "\nEnter command: "
    ).strip().lower()


def main():
    if not check_ffmpeg_paths():
        return

    LoadConfig()

    while True:
        command = show_main_menu()

        if command == "0":
            show_queue_stats()

        elif command == "a":
            check_missing_files()

        elif command == "b":
            select_profile_and_add_files()

        elif command == "c":
            convert_videos()

        elif command == "q":
            exit_program()

        else:
            print("Invalid input")


if __name__ == "__main__":
    try:
        main()

    except RuntimeError as e:
        print()
        print(f"Queue error: {e}")
        print("No changes were made to the queue.")
        wait_exit()

    except KeyboardInterrupt:
        print()
        print("==============================")
        print("User pressed Ctrl+C, script exited.")
        print("==============================")
