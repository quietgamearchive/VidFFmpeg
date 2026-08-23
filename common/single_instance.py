# ============================================================
# Cross-platform kernel-level single-instance lock
#
#   Windows  -> named mutex (kernel object, no file)
#   Linux    -> abstract unix socket (kernel namespace, no file)
#   macOS    -> flock on a lock file (kernel-managed advisory
#               lock, auto-released on process death; the file
#               stays on disk but can never be left "locked")
#
# Every variant releases itself automatically when the process
# exits or crashes, so a stale lock can never block startup.
#
# The returned _Lock object keeps the kernel handle alive; the
# lock is held while that object is referenced.  Dropping the
# last reference (or calling .release()) frees the kernel
# object immediately, so a short-lived lock (e.g. one held only
# for the duration of a function) works on every platform.
#
# Usage:
#   lock = acquire_single_instance("vidffmpeg_gui")
#   if not lock:
#       ... already running ...
# ============================================================

import hashlib
import os
import sys


class _Lock:
    # Wraps a platform lock handle so that dropping the last
    # reference reliably releases the kernel object.  Raw
    # handles (ctypes HANDLE, os.open fd) are NOT closed by
    # garbage collection on their own, hence this wrapper.
    def __init__(self, release):
        self._release = release

    def release(self):
        release, self._release = self._release, None

        if release:
            try:
                release()
            except Exception:
                pass

    def __del__(self):
        self.release()


def acquire_single_instance(name):
    # `name` only needs to be unique within this application:
    # each caller passes its own scope ("vidffmpeg_gui",
    # "vidffmpeg_cli", ...), so GUI and CLI locks never collide.
    key = hashlib.sha1(name.encode("utf-8")).hexdigest()

    if sys.platform == "win32":
        return _acquire_windows_mutex(key)

    if sys.platform == "linux":
        return _acquire_linux_socket(key)

    return _acquire_posix_flock(key)


def _acquire_windows_mutex(key):
    # Named kernel mutex: the same name always maps to the same
    # object; ERROR_ALREADY_EXISTS (183) means another process
    # already holds it.  The kernel destroys the object when the
    # last handle is closed, i.e. when that process exits.
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    handle = kernel32.CreateMutexW(None, False, "VidFFmpeg_" + key)

    if not handle:
        return None

    if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
        kernel32.CloseHandle(handle)
        return None

    return _Lock(lambda: kernel32.CloseHandle(handle))


def _acquire_linux_socket(key):
    # Abstract unix socket: the leading "\0" puts the address in
    # the kernel's abstract namespace instead of the filesystem,
    # so no file is created.  Binding the same name twice fails
    # with EADDRINUSE; the kernel removes the binding when the
    # owning process dies.
    import socket

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        sock.bind("\0VidFFmpeg_" + key)
    except OSError:
        sock.close()
        return None

    sock.listen(1)
    return _Lock(sock.close)


def _acquire_posix_flock(key):
    # macOS (and any other POSIX system without abstract sockets):
    # advisory flock on a lock file.  The lock itself lives in the
    # kernel and is released automatically when the process dies,
    # so the leftover file can never block startup again.
    import fcntl
    import tempfile

    lock_path = os.path.join(tempfile.gettempdir(), "VidFFmpeg_" + key + ".lock")
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)

    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        return None

    return _Lock(lambda: os.close(fd))
