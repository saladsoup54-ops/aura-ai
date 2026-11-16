# aura_bus.py — AURA Message Bus (Phase 5-A)
# ===========================================
# One canonical, lock-protected path for every shared file.  All lobes
# are threads of one process, so a per-path re-entrant lock registry is
# enough to eliminate the remaining producer/consumer races:
#
#   append(path, line)    — serialised append of one intact line
#   drain(path)           — atomic read-all + truncate (one consumer)
#   write(path, text)     — serialised whole-file write (signals)
#
# Every shared file contract (sensory_buffer, cortex_inbox,
# processed_cortex, short_term_memory, parietal_inbox, the vault)
# flows through these primitives.
# ===========================================

import os
import threading
from contextlib import contextmanager

from aura_state import deny_live_write

_locks = {}
_locks_guard = threading.Lock()


def _lock_for(path):
    with _locks_guard:
        if path not in _locks:
            _locks[path] = threading.RLock()
        return _locks[path]


@contextmanager
def locked(path):
    """Hold the path lock — for check-then-write transactions."""
    with _lock_for(path):
        yield


def append(path, line, encoding="utf-8"):
    """Append one intact line under the path lock."""
    if not line:
        return False
    deny_live_write(path)
    text = line if line.endswith("\n") else line + "\n"
    try:
        with _lock_for(path):
            with open(path, "a", encoding=encoding) as f:
                f.write(text)
        return True
    except Exception:
        return False


def drain(path, encoding="utf-8"):
    """
    Atomically read every line and truncate the file.  Returns the list
    of non-empty lines; a missing file drains to [].
    """
    deny_live_write(path)
    with _lock_for(path):
        try:
            if not os.path.exists(path):
                return []
            with open(path, "r", encoding=encoding, errors="ignore") as f:
                content = f.read()
            with open(path, "w", encoding=encoding) as f:
                f.truncate()
            return [l for l in content.splitlines() if l.strip()]
        except Exception:
            return []


def write(path, text, encoding="utf-8"):
    """Serialised whole-file write (signals, state files)."""
    deny_live_write(path)
    try:
        with _lock_for(path):
            with open(path, "w", encoding=encoding) as f:
                f.write(text)
        return True
    except Exception:
        return False


def read(path, default="", encoding="utf-8"):
    """Serialised whole-file read."""
    try:
        with _lock_for(path):
            if not os.path.exists(path):
                return default
            with open(path, "r", encoding=encoding, errors="ignore") as f:
                return f.read()
    except Exception:
        return default
