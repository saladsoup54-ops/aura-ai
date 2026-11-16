import json
import os
import time

from aura_bus import read as bus_read, write as bus_write
from aura_constants import (FIELD_STATS as STATS_FILE,
                            HYPO_SIGNAL_FILE as SIGNAL_FILE,
                            TENSION_TARGET as TARGET_TENSION,
                            TENSION_TOLERANCE)

# ── HOMEOSTASIS TARGETS (aura_constants) ───────────────────────────
# field_stats.txt carries JSON telemetry written by aura_field.step():
#   {"s": entropy, "tension": mean(top-5 activation), "top": name, ...}
# Homeostasis regulates on TENSION (activation scale). Entropy is a
# normalised distribution measure (0..1) and must never be compared
# against the topological invariant D (0.0804245) — that mismatch
# pinned the signal to INHIBIT permanently and starved the Thalamus
# and Synapse of all sensory input.


def read_field_state():
    """
    Returns (entropy, tension) read from field_stats.txt.
    tension is None when only the legacy bare-entropy format is present,
    in which case homeostasis stays neutral rather than guessing.
    """
    try:
        raw = bus_read(STATS_FILE).strip()
        if not raw:
            return None, None
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                if "tension" not in data:
                    return float(data.get("s", 0.0)), None
                return float(data.get("s", 0.0)), float(data.get("tension", 0.0))
        except (ValueError, TypeError):
            pass
        # legacy bare entropy float
        try:
            return float(raw), None
        except (ValueError, TypeError):
            return None, None
    except Exception:
        return None, None


def compute_signal(tension):
    """Map field tension onto a homeostatic directive."""
    if tension is None:
        return "HOMEOSTASIS: STABLE"
    if tension > TARGET_TENSION + TENSION_TOLERANCE:
        return "HOMEOSTASIS: INHIBIT"
    if tension < TARGET_TENSION - TENSION_TOLERANCE:
        return "HOMEOSTASIS: EXCITE"
    return "HOMEOSTASIS: STABLE"


def run_hypothalamus():
    print("--- AURA HYPOTHALAMUS: HOMEOSTASIS ENGINE ACTIVE ---")

    # Ensure the signal file exists on boot
    bus_write(SIGNAL_FILE, "HOMEOSTASIS: STABLE")

    while True:
        entropy, tension = read_field_state()
        signal = compute_signal(tension)

        bus_write(SIGNAL_FILE, signal)

        # If EXCITE, inject a small pulse into the identity core
        if signal == "HOMEOSTASIS: EXCITE":
            try:
                from aura_field import FIELD
                FIELD.stimulate("aura", strength=0.05)
            except Exception:
                pass

        time.sleep(2)


if __name__ == "__main__":
    run_hypothalamus()
