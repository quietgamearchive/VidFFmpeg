import json
import os
import tempfile

from .config import QUEUE_FILE


def load_queue():
    if not QUEUE_FILE.exists():
        return []

    try:
        with QUEUE_FILE.open(
            encoding="utf-8"
        ) as f:
            queue = json.load(f)

        if not isinstance(queue, list):
            raise ValueError(
                "queue root must be a JSON array"
            )

        return queue

    except (OSError, json.JSONDecodeError) as e:
        raise RuntimeError(
            f"Failed to read queue file: "
            f"{QUEUE_FILE}: {e}"
        ) from e

    except ValueError as e:
        raise RuntimeError(
            f"Invalid queue file: "
            f"{QUEUE_FILE}: {e}"
        ) from e


def save_queue(queue):
    temp_name = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=QUEUE_FILE.parent,
            prefix=f".{QUEUE_FILE.stem}-",
            suffix=".tmp",
            delete=False,
        ) as f:
            temp_name = f.name

            json.dump(
                queue,
                f,
                ensure_ascii=False,
                indent=4
            )

            f.flush()
            os.fsync(f.fileno())

        os.replace(
            temp_name,
            QUEUE_FILE
        )

        temp_name = None

    except OSError as e:
        raise RuntimeError(
            f"Failed to save queue file: "
            f"{QUEUE_FILE}: {e}"
        ) from e

    finally:
        if temp_name:
            try:
                os.unlink(temp_name)
            except OSError:
                pass