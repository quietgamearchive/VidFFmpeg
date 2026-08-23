import json
import os
import re
import signal
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path


def format_size(size):
    size = float(size)

    for unit in (
        "B",
        "KB",
        "MB",
        "GB",
        "TB"
    ):
        if size < 1024:
            return f"{size:.2f}{unit}"

        size /= 1024

    return f"{size:.2f}PB"


def format_time(seconds):
    seconds = max(0, int(seconds))

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    if hours:
        return (
            f"{hours:02}:"
            f"{minutes:02}:"
            f"{seconds:02}"
        )

    return (
        f"{minutes:02}:"
        f"{seconds:02}"
    )


def time_to_seconds(value):
    if not value:
        return 0

    try:
        parts = value.split(":")

        if len(parts) != 3:
            return 0

        return (
            int(parts[0]) * 3600
            + int(parts[1]) * 60
            + int(parts[2])
        )

    except Exception:
        return 0


def calc_duration(start, end):
    start_seconds = time_to_seconds(start)
    end_seconds = time_to_seconds(end)

    seconds = end_seconds - start_seconds

    if seconds <= 0:
        raise ValueError(
            "End time must be greater than start time."
        )

    return seconds


def validate_trim_times(start, end, duration):
    start_seconds = time_to_seconds(start)
    end_seconds = time_to_seconds(end)

    if start and start_seconds > duration:
        raise ValueError(
            "Start time must not be greater than the video duration."
        )

    if end and end_seconds > duration:
        raise ValueError(
            "End time must not be greater than the video duration."
        )


def make_output(source, profile):
    source = Path(source)

    output = profile.get(
        "output",
        {}
    )

    directory = output.get(
        "directory",
        ""
    )

    if directory:
        folder = Path(directory)
    else:
        folder = source.parent

    filename = output.get(
        "filename",
        "{source}"
    )

    filename = filename.replace(
        "{source}",
        source.stem
    )

    extension = output.get(
        "extension",
        ".mp4"
    )

    return folder / (
        filename + extension
    )


def load_profile(profile_dir, name):
    with open(
        Path(profile_dir) / name,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def get_video_duration(
    path,
    ffprobe_path
):
    command = [
        str(ffprobe_path),
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path)
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if result.returncode != 0:
        return None

    try:
        return float(
            result.stdout.strip()
        )
    except Exception:
        return None


def check_video(
    path,
    ffprobe_path
):
    command = [
        str(ffprobe_path),
        "-v",
        "error",
        "-select_streams",
        "v",
        "-show_entries",
        "stream=index",
        "-of",
        "csv=p=0",
        str(path)
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if result.returncode != 0:
        return False

    if not result.stdout.strip():
        return False

    duration = get_video_duration(
        path,
        ffprobe_path
    )

    return (
        duration is not None
        and duration > 1.0
    )


def append_error(
    error_file,
    path,
    reason
):
    finish_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    with open(
        error_file,
        "a",
        encoding="utf-8"
    ) as f:
        f.write(
            f"{path} | {finish_time} | {reason}\n"
        )


def append_finished(
    finished_file,
    destination,
    duration,
    elapsed,
    finish_time,
    size,
    percent
):
    with open(
        finished_file,
        "a",
        encoding="utf-8"
    ) as f:
        f.write(
            f"{destination} "
            f"({duration}) | "
            f"{elapsed} | "
            f"{finish_time} | "
            f"{size} | "
            f"{percent:.2f}%\n"
        )


class FFmpegProcess:
    def __init__(self):
        self.process = None
        self._suspended = False
        self._stop_requested = False
        self._lock = threading.Lock()

    def start(self, command):
        with self._lock:
            if self._stop_requested:
                return None

            self.process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1
            )

        return self.process

    def pause(self):
        if not self.process:
            return False

        if self.process.poll() is not None:
            return False

        try:
            os.kill(
                self.process.pid,
                signal.SIGSTOP
            )

            self._suspended = True
            return True

        except Exception:
            return False

    def resume(self):
        if not self.process:
            return False

        if self.process.poll() is not None:
            return False

        try:
            os.kill(
                self.process.pid,
                signal.SIGCONT
            )

            self._suspended = False
            return True

        except Exception:
            return False

    def stop(self):
        with self._lock:
            self._stop_requested = True

            if not self.process:
                return

            try:
                if self._suspended:
                    os.kill(
                        self.process.pid,
                        signal.SIGCONT
                    )

                if self.process.poll() is None:
                    self.process.terminate()

                    try:
                        self.process.wait(
                            timeout=5
                        )
                    except subprocess.TimeoutExpired:
                        self.process.kill()

            except Exception:
                pass

            self._suspended = False

    def wait(self):
        if self.process:
            return self.process.wait()

        return -1

    @property
    def paused(self):
        return self._suspended


def convert_task(
    task,
    profile_dir,
    ffmpeg_path,
    ffprobe_path,
    finished_file,
    error_file,
    process_controller,
    progress_callback,
    info_callback,
    stop_event,
    finished_callback=None
):
    source = Path(
        task["file"]
    )

    try:
        profile = load_profile(
            profile_dir,
            task.get("profile", "")
        )
    except Exception as e:
        reason = (
            f"Failed to load profile: {e}"
        )

        append_error(
            error_file,
            source,
            reason
        )

        return False, reason

    if not source.exists():
        reason = "Source file does not exist."

        append_error(
            error_file,
            source,
            reason
        )

        return False, reason

    duration = get_video_duration(
        source,
        ffprobe_path
    )

    if stop_event.is_set():
        return False, "Conversion stopped."

    if duration is None:
        reason = (
            "Unable to read source duration."
        )

        append_error(
            error_file,
            source,
            reason
        )

        return False, reason

    start_time = task.get(
        "start",
        ""
    )

    end_time = task.get(
        "end",
        ""
    )

    try:
        validate_trim_times(
            start_time,
            end_time,
            duration
        )
    except ValueError as e:
        reason = str(e)

        append_error(
            error_file,
            source,
            reason
        )

        return False, reason

    if start_time and end_time:
        try:
            target_duration = calc_duration(
                start_time,
                end_time
            )
        except ValueError as e:
            reason = str(e)

            append_error(
                error_file,
                source,
                reason
            )

            return False, reason

    elif end_time:
        target_duration = time_to_seconds(
            end_time
        )
    elif start_time:
        target_duration = (
            duration
            - time_to_seconds(start_time)
        )
    else:
        target_duration = duration

    target_duration = max(
        target_duration,
        0.001
    )

    original_duration_text = format_time(duration)
    if start_time or end_time:
        original_duration_text += (
            f" ({start_time or 'Start'} - "
            f"{end_time or 'End'})"
        )

    destination = make_output(
        source,
        profile
    )

    temporary = destination.with_name(
        destination.stem
        + "_tmp"
        + destination.suffix
    )

    try:
        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )
    except Exception as e:
        reason = f"Failed to create output directory: {e}"
        append_error(
            error_file,
            source,
            reason
        )
        return False, reason

    command = [
        str(ffmpeg_path),
        "-hide_banner",
        "-loglevel",
        "info",
        "-y"
    ]

    if start_time:
        command += [
            "-ss",
            start_time
        ]

    command += [
        "-i",
        str(source)
    ]

    if end_time:
        if start_time:
            command += [
                "-t",
                format_time(
                    target_duration
                )
            ]
        else:
            command += [
                "-to",
                end_time
            ]

    command += profile.get(
        "ffmpeg_args",
        []
    )

    command.append(
        str(temporary)
    )

    try:
        process_controller.start(
            command
        )
    except Exception as e:
        reason = f"Failed to start FFmpeg: {e}"
        append_error(
            error_file,
            source,
            reason
        )
        return False, reason

    if process_controller.process is None:
        if temporary.exists():
            try:
                temporary.unlink()
            except Exception:
                pass

        return False, "Conversion stopped."

    start_timestamp = time.time()

    last_line = ""

    try:
        for line in process_controller.process.stderr:
            if stop_event.is_set():
                break

            line = line.rstrip()

            if not line:
                continue

            match = re.search(
                r"time=(\d{2}:\d{2}:\d{2}(?:\.\d+)?)",
                line
            )

            if match:
                try:
                    h, m, s = match.group(1).split(
                        ":"
                    )

                    current_seconds = (
                        int(h) * 3600
                        + int(m) * 60
                        + float(s)
                    )

                    percent = min(
                        max(
                            current_seconds
                            / target_duration
                            * 100,
                            0
                        ),
                        100
                    )

                    progress_callback(
                        f"{percent:.2f}%"
                    )

                    speed_match = re.search(
                        r"speed=\s*([\d.]+)x",
                        line
                    )

                    speed = None

                    if speed_match:
                        try:
                            speed = float(
                                speed_match.group(1)
                            )
                        except Exception:
                            pass

                    if speed and speed > 0:
                        remaining = (
                            target_duration
                            - current_seconds
                        ) / speed

                        remaining_text = format_time(
                            remaining
                        )
                    else:
                        remaining_text = "--:--"

                    if start_time or end_time:
                        cut_start = (
                            start_time
                            if start_time
                            else "Start"
                        )

                        cut_end = (
                            end_time
                            if end_time
                            else "End"
                        )

                        time_text = (
                            f"{format_time(duration)} "
                            f"({cut_start} - {cut_end})"
                        )
                    else:
                        time_text = format_time(
                            duration
                        )

                    info_callback(
                        (
                            f"Duration: {time_text} | "
                            f"Estimated remaining: "
                            f"{remaining_text} | "
                            f"Destination: {destination}\n"
                            f"{line}"
                        )
                    )

                except Exception:
                    pass

            last_line = line

        if stop_event.is_set():
            process_controller.stop()

        return_code = process_controller.wait()

        if stop_event.is_set():
            if temporary.exists():
                try:
                    temporary.unlink()
                except Exception:
                    pass

            return False, "Conversion stopped."

        if return_code != 0:
            reason = (
                "FFmpeg returned an error."
            )

            if last_line:
                reason += (
                    f"\n\n{last_line}"
                )

            append_error(
                error_file,
                source,
                reason
            )

            if temporary.exists():
                try:
                    temporary.unlink()
                except Exception:
                    pass

            return False, reason

        if not temporary.exists():
            reason = (
                "FFmpeg completed but "
                "the output file was not created."
            )

            append_error(
                error_file,
                source,
                reason
            )

            return False, reason

        if not check_video(
            temporary,
            ffprobe_path
        ):
            reason = (
                "Output file validation failed."
            )

            append_error(
                error_file,
                source,
                reason
            )

            try:
                temporary.unlink()
            except Exception:
                pass

            return False, reason

        old_size = source.stat().st_size
        new_size = temporary.stat().st_size

        same_file = (
            source.resolve()
            == destination.resolve()
        )

        if same_file and new_size > old_size:
            try:
                temporary.unlink()
            except Exception:
                pass

            reason = (
                "New file is larger than "
                "the original file."
            )

            append_error(
                error_file,
                source,
                reason
            )

            return False, reason

        percent_size = (
            new_size / old_size * 100
            if old_size
            else 0
        )

        if destination.exists():
            destination.unlink()

        temporary.rename(
            destination
        )

        if profile.get(
            "after_finish",
            {}
        ).get(
            "delete_source",
            False
        ):
            if not same_file:
                try:
                    source.unlink()
                except Exception:
                    pass

        elapsed = (
            time.time()
            - start_timestamp
        )

        finished_elapsed = format_time(elapsed)
        finish_time = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        finished_size = format_size(new_size)

        append_finished(
            finished_file,
            destination,
            original_duration_text,
            finished_elapsed,
            finish_time,
            finished_size,
            percent_size
        )

        if finished_callback is not None:
            finished_callback()

        progress_callback(
            "100.00%"
        )

        info_callback(
            (
                f"Duration: {format_time(duration)} | "
                f"Estimated remaining: 00:00 | "
                f"Destination: {destination}\n"
                "Finished."
            )
        )

        return True, ""

    except Exception as e:
        reason = str(e)

        append_error(
            error_file,
            source,
            reason
        )

        try:
            if temporary.exists():
                temporary.unlink()
        except Exception:
            pass

        return False, reason

    finally:
        with process_controller._lock:
            process_controller.process = None
            process_controller._suspended = False
