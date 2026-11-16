# ukft_console_log.py — AURA Console Mirror
# ==================================================
# The organism's console (every lobe's prints: thalamus hearings,
# cortex judgements, forgetting trims, saturation pauses, reasoning
# cycles) used to exist only in the terminal window — unreadable to
# anyone not watching that screen.  install_mirror() tees stdout and
# stderr to aura_console.log as well as the screen, so the log can be
# read from disk at any time.
#
#   - The console behaves exactly as before (same stream, same Ctrl+C).
#   - The file is capped (default 1 MB, keeps the newest half) so a
#     chattery lobe can never fill the disk.
#   - Thread-safe: all lobes print concurrently; one lock serialises
#     the file side.  The mirror never raises — a logging failure
#     must never take down a lobe.
# ==================================================

import os
import sys
import threading

from aura_constants import CONSOLE_LOG

MIRROR_MAX_BYTES = 1000000  # cap the mirror; keep the newest half past it

_lock = threading.Lock()


class _Tee:
    """A stream wrapper that copies everything to the mirror file."""

    def __init__(self, stream, path):
        self._stream = stream
        self._path = path

    def write(self, text):
        try:
            self._stream.write(text)
        except Exception:
            pass
        if text:
            try:
                with _lock:
                    with open(self._path, "a", encoding="utf-8",
                              errors="replace") as f:
                        f.write(text)
                    try:
                        if os.path.getsize(self._path) > MIRROR_MAX_BYTES:
                            with open(self._path, "r", encoding="utf-8",
                                      errors="replace") as f:
                                lines = f.readlines()
                            with open(self._path, "w", encoding="utf-8",
                                      errors="replace") as f:
                                f.writelines(lines[len(lines) // 2:])
                    except Exception:
                        pass
            except Exception:
                pass
        return len(text) if text else 0

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def flush(self):
        try:
            self._stream.flush()
        except Exception:
            pass

    def __getattr__(self, name):
        return getattr(self._stream, name)


def install_mirror(path=CONSOLE_LOG):
    """
    Tee stdout/stderr to `path` (idempotent — a second call is a no-op
    so reboots-in-process and tests can call it freely).  Returns True
    when the mirror is active.
    """
    try:
        if isinstance(sys.stdout, _Tee) or isinstance(sys.stderr, _Tee):
            return True
        sys.stdout = _Tee(sys.stdout, path)
        sys.stderr = _Tee(sys.stderr, path)
        return True
    except Exception:
        return False
