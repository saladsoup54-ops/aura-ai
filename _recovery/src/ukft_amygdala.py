import hashlib
import os
import re
import time
from collections import deque

from aura_bus import drain as bus_drain
from aura_constants import SHORT_TERM_MEMORY as MEMORY_PATH, EMOTIONAL_LOG
from aura_field import FIELD

EXCITATORY = {
    "danger", "error", "architect", "help", "hello",
    "unknown", "self", "urgent", "warning", "critical"
}

INHIBITORY = {
    "stable", "calm", "good", "clear", "resolved",
    "complete", "done", "ready", "okay", "fine"
}


class SeenFilter:
    """
    Phase 0.7: real FIFO dedup. The old code called set.pop(), which
    evicts an ARBITRARY hash — recent content could be forgotten while
    stale content stayed. A deque keeps true insertion order.
    """
    def __init__(self, maxlen=1000):
        self.maxlen = maxlen
        self._seen = set()
        self._order = deque()

    def is_new(self, item_hash):
        if item_hash in self._seen:
            return False
        self._seen.add(item_hash)
        self._order.append(item_hash)
        if len(self._order) > self.maxlen:
            old = self._order.popleft()
            self._seen.discard(old)
        return True


def is_experience(line):
    """
    Phase 2 polish: cortex judgement records are system telemetry, not
    experience.  Letting them into the amygdala made every STABLE
    judgement print a calming response and every UNKNOWN judgement print
    a stress spike — the organism was emoting about its own telemetry.
    """
    return not line.startswith("judgement:")


def flush_stale_buffer():
    """
    Discard the unprocessed short-term buffer at boot via an atomic
    drain — never a raw truncate, which would destroy records the
    hippocampus appends in the same moment.  Returns what was dropped.
    """
    from aura_bus import drain as bus_drain
    try:
        return bus_drain(MEMORY_PATH)
    except Exception:
        return []


def run_amygdala():
    print("--- AURA AMYGDALA: EMOTIONAL MONITOR ACTIVE ---")

    # FIX 1: Flush stale memory on startup BEFORE starting the loop
    dropped = flush_stale_buffer()
    if dropped:
        print(f"[Amygdala] Flushed {len(dropped)} stale buffer line(s) on boot.")

    seen = SeenFilter()

    while True:
        lines = []

        # Phase 5-A: read and truncate atomically through the bus
        if os.path.exists(MEMORY_PATH):
            lines = [l.lower() for l in bus_drain(MEMORY_PATH)]

        for line in lines:
            if not is_experience(line):
                continue
            line_hash = hashlib.md5(line.encode()).hexdigest()
            if not seen.is_new(line_hash):
                continue

            # Tokenize like the thalamus does: raw split() kept
            # punctuation ("danger!"), so real triggers never matched.
            words_in_line = set(re.findall(r"[a-z]+", line))

            # Check for excitatory triggers (1 trigger per matching word per line)
            matched_excitatory = EXCITATORY.intersection(words_in_line)
            for word in matched_excitatory:
                FIELD.stimulate(word, strength=0.1)
                try:
                    with open(EMOTIONAL_LOG, "a", encoding="utf-8") as f:
                        f.write(f"STRESS_SPIKE: {word} detected at {time.time()}\n")
                except Exception:
                    pass
                print(f"[Amygdala] Excitatory spike: {word.upper()}")

            # Check for inhibitory triggers
            matched_inhibitory = INHIBITORY.intersection(words_in_line)
            for word in matched_inhibitory:
                with FIELD.lock:
                    for node in FIELD.nodes.values():
                        if node.activation > 0.3:
                            node.velocity *= 0.85
                try:
                    with open(EMOTIONAL_LOG, "a", encoding="utf-8") as f:
                        f.write(f"CALM_RESPONSE: {word} at {time.time()}\n")
                except Exception:
                    pass
                print(f"[Amygdala] Calming response: {word.upper()}")

        time.sleep(1)


if __name__ == "__main__":
    run_amygdala()
