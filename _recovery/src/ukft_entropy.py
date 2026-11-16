import os
import time

from aura_constants import SHORT_TERM_MEMORY, EMOTIONAL_LOG, SLEEP_LOG_FILE, ACTION_LOG

# Phase 0.7: per-file retention caps ("forgetting").
# inner_monologue.txt already caps itself at 500 lines inside
# ukft_inner_monologue, so a second trimmer here would only add a
# cross-thread file race for zero benefit.
LOG_FILES = [
    (SHORT_TERM_MEMORY, 50),
    (EMOTIONAL_LOG, 2000),
    # V6 C11: the sleep log appended forever (one line per
    # consolidation) — 5000 lines is years of nights.
    (SLEEP_LOG_FILE, 5000),
    # Audit fix: the tool action log appended forever with no cap.
    (ACTION_LOG, 2000),
]


def trim_logs():
    """Trim overgrown log files. Returns the list of files trimmed."""
    from aura_bus import locked as bus_locked

    trimmed = []
    for file_path, max_lines in LOG_FILES:
        if not os.path.exists(file_path):
            continue
        try:
            # Under the path lock: lines appended between the read and
            # the rewrite used to vanish silently.
            with bus_locked(file_path):
                with open(file_path, "r", encoding="utf-8",
                          errors="ignore") as f:
                    lines = f.readlines()

                if len(lines) > max_lines:
                    # Keep only the newest lines (Simulating 'Forgetting')
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.writelines(lines[-max_lines:])
                    trimmed.append(file_path)
        except Exception:
            # If the file is being used by another part of the brain, just skip it
            pass
    return trimmed


def run_entropy_cycle():
    """Matches the name expected by aura_master.py"""
    print("--- AURA ENTROPY: MANIFOLD DISSIPATION ACTIVE ---")

    while True:
        for path in trim_logs():
            print(f"[Entropy] Dissipated old patterns in {path}")

        time.sleep(15)  # Entropy happens at a slow, steady pace


if __name__ == "__main__":
    run_entropy_cycle()
