import collections
import os
import time

from aura_bus import read as bus_read, write as bus_write
from aura_constants import (VAULT_FILE, PFC_SIGNAL_FILE, PFC_FOCUS_FILE,
                             HYPO_SIGNAL_FILE)
from aura_state import resolve_state_path as _sp

FOCUS_DURATION   = 300.0   # seconds a focus directive is held
FOCUS_STRENGTH   = 0.15    # per-cycle boost to the focused concept
ASSOCIATE_STRENGTH = 0.05  # per-cycle boost to its top associates


class PrefrontalCortex:
    """
    Executive function — fast burst suppression.

    Phase 0.7: judges a rolling 30-second growth average with a
    3-window debounce instead of one noisy 5-second sample (dream-state
    noise used to trip THROTTLE constantly, which starved the Thalamus
    and Synapse).
    """
    WINDOW_SAMPLES = 6    # 6 x 5s = 30s rolling window
    DEBOUNCE       = 3    # consecutive high-average windows before THROTTLE

    def __init__(self, threshold=1000):
        self.threshold = threshold
        self.last_size = None
        self.recent = collections.deque(maxlen=self.WINDOW_SAMPLES)
        self.high_streak = 0

    def evaluate(self, growth=None):
        """
        Judge vault growth. Accepts an explicit growth value for testing;
        otherwise measures the vault file since the previous call.
        """
        if growth is None:
            if not os.path.exists(VAULT_FILE):
                return "STABLE"
            current_size = os.path.getsize(VAULT_FILE)
            if self.last_size is None:
                self.last_size = current_size
                return "STABLE"
            growth = max(0, current_size - self.last_size)
            self.last_size = current_size

        self.recent.append(growth)

        # Need at least two samples before a meaningful average exists
        if len(self.recent) < 2:
            return "STABLE"

        avg = sum(self.recent) / len(self.recent)

        if avg > self.threshold:
            self.high_streak += 1
            if self.high_streak >= self.DEBOUNCE:
                return "THROTTLE: HIGH NOISE DETECTED"
            return "STABLE"

        self.high_streak = 0
        return "STABLE"

    def write_signal(self, directive):
        bus_write(PFC_SIGNAL_FILE, directive)


# ── Phase 4-C: ATTENTION DIRECTOR ─────────────────────────────────
# Voluntary sustained focus.  The Architect says "focus on dark matter"
# and the PFC holds that concept in attention: a per-cycle stabilising
# pulse keeps it from decaying, its temporal-lobe associates receive a
# smaller pulse, and the DMN/monologue naturally follow the boosted
# node to the top of the field.

def set_focus(word, seconds=FOCUS_DURATION):
    """Direct attention at `word` for `seconds`."""
    parts = (word or "").strip().lower().split()
    if not parts:
        return False
    word = parts[0]
    try:
        # Through the bus: readers poll this file while writers
        # (bridge, curiosity) update it — no half-written directives.
        bus_write(PFC_FOCUS_FILE,
                  f"FOCUS: {word} | UNTIL: {time.time() + seconds:.0f}\n")
        return True
    except Exception:
        return False


def clear_focus():
    try:
        bus_write(PFC_FOCUS_FILE, "")
    except Exception:
        pass


def read_focus():
    """
    Returns (word, until) when a live focus directive is active,
    else None.  Expired directives are cleared in place.
    """
    try:
        raw = bus_read(PFC_FOCUS_FILE).strip()
        if not raw.startswith("FOCUS: "):
            return None
        word = raw[len("FOCUS: "):].split("|")[0].strip().lower()
        until = 0.0
        if "UNTIL:" in raw:
            try:
                until = float(raw.split("UNTIL:")[1].strip())
            except ValueError:
                until = 0.0
        if not word:
            return None
        if until and time.time() > until:
            clear_focus()
            return None
        return word, until
    except Exception:
        return None


def _links_stamp():
    """(mtime, size) identity of the temporal link file."""
    try:
        st = os.stat("temporal_links.txt")
        return (st.st_mtime, st.st_size)
    except OSError:
        return (0.0, -1)


def attention_cycle(field=None, temporal=None):
    """
    One attention pass: pulse the focused concept and its top temporal
    associates.  Returns the focused word, or None when idle.
    Homeostasis outranks held attention: under INHIBIT the pulse is
    skipped (the focus directive stays, excitation waits until the
    field recovers) — a held focus must not pin the field into
    chronic over-tension.
    """
    current = read_focus()
    if current is None:
        return None

    word, _until = current

    try:
        if "INHIBIT" in bus_read(HYPO_SIGNAL_FILE):
            return word
    except Exception:
        pass

    if field is None:
        from aura_field import FIELD as _FIELD
        field = _FIELD

    field.stimulate(word, strength=FOCUS_STRENGTH)

    if temporal is None:
        try:
            from ukft_temporal_lobe import TemporalLobe
            if not hasattr(attention_cycle, "_lobe"):
                lobe = TemporalLobe()
                if os.path.exists(_sp("temporal_links.txt")):
                    try:
                        lobe.load()
                    except Exception:
                        pass
                attention_cycle._lobe = lobe
                attention_cycle._links_stamp = _links_stamp()
            else:
                # The associate map grows as she reads — re-read it when
                # the file moved on, so focus boosts fresh associates.
                # Stamp is (mtime, size): same-tick rewrites and silent
                # failures must neither slip through nor poison the mark.
                stamp = _links_stamp()
                if stamp != attention_cycle._links_stamp:
                    try:
                        attention_cycle._lobe.load()
                    except Exception:
                        pass
                    else:
                        attention_cycle._links_stamp = stamp
            temporal = attention_cycle._lobe
        except Exception:
            temporal = None

    if temporal is not None:
        for other, _count, strength in temporal.associates(word, 3):
            if strength > 0:
                field.stimulate(other, strength=ASSOCIATE_STRENGTH)

    return word


def run_pfc():
    print("--- AURA PFC: EXECUTIVE FUNCTION ACTIVE ---")

    # Ensure the signal file exists on boot
    bus_write(PFC_SIGNAL_FILE, "STABLE")

    pfc = PrefrontalCortex()
    last_focus_print = None

    while True:
        directive = pfc.evaluate()
        pfc.write_signal(directive)

        # Phase 4-C: voluntary sustained focus
        try:
            focused = attention_cycle()
            # Report focus acquisition, not every pulse — a held
            # directive must not flood the console for its whole
            # duration.
            if focused and focused != last_focus_print:
                print(f"[PFC] Attention held on: {focused.upper()}")
            last_focus_print = focused
        except Exception as e:
            print(f"[PFC] Attention friction: {e}")

        time.sleep(5)


if __name__ == "__main__":
    run_pfc()
