import os
import time
import random
import re
from aura_bus import drain as bus_drain, read as bus_read
from aura_constants import (D_INVARIANT as UKFT_CONSTANT, VAULT_FILE,
                             CORTEX_PATH as PROCESSED_THOUGHTS,
                             HYPO_SIGNAL_FILE, DREAM_LOG,
                             FIELD_NODE_CEILING)
from aura_field import FIELD
from aura_state import resolve_state_path as _sp
from aura_vault_io import iter_anchors, parse_vault_line, append_anchor

DREAM_CONCEPTS     = ["TOPOLOGY", "RESONANCE", "STABILITY", "ENTROPY", "MANIFOLD", "VISCOSITY"]

# Phase 0.6: dream noise goes to DREAM_LOG (aura_constants), never the vault.
DREAM_LOG_MAX_LINES  = 2000

# Saturation guard: the field legitimately holds a rich semantic graph
# (identity + replay + temporal/discovery wiring runs into the thousands
# of nodes).  The old 1000-node ceiling was written when 1000 meant
# runaway growth — it now fires on a healthy field and put the whole
# assimilation pipeline to sleep for an hour.  Raised, and the pause is
# short enough to re-check while Ebbinghaus forgets silent nodes.
# The ceiling lives in aura_constants (single source of truth);
# SATURATION_NODES stays as an alias for anything importing it.
SATURATION_NODES     = FIELD_NODE_CEILING
SATURATION_SLEEP     = 300


def read_hypo_signal():
    return bus_read(HYPO_SIGNAL_FILE).strip()


def flush_cortex_to_vault():
    """
    Phase 5-A: the cortex flush is canonicalised.  Judgement lines are
    drained atomically, parsed back into (concept, data, source) records
    and appended through the shared vault contract with dedup — the
    vault grows only in canonical ANCHOR form, whatever the pipeline
    produced upstream.
    """
    lines = bus_drain(PROCESSED_THOUGHTS)
    if not lines:
        return 0
    added = 0
    for line in lines:
        parsed = parse_vault_line(line)
        if parsed:
            concept, data, source = parsed
            if append_anchor(VAULT_FILE, concept, data, source or "MANIFEST"):
                added += 1
    return added


# Phase 0.6: concept cache — the vault is re-parsed only when its size or
# mtime changes (the old version read the whole file every 0.5 s).
_concept_cache = {"size": -1, "mtime": 0.0, "concepts": None}


def get_actual_concepts():
    global _concept_cache
    concepts = set(DREAM_CONCEPTS)
    if os.path.exists(VAULT_FILE):
        try:
            st = os.stat(VAULT_FILE)
            if (st.st_size != _concept_cache["size"]
                    or st.st_mtime != _concept_cache["mtime"]
                    or _concept_cache["concepts"] is None):
                found = set()
                for concept, _, _ in iter_anchors(VAULT_FILE):
                    # Phase 0.6: full anchor titles (e.g. "CSB Pew Bible 2nd
                    # Printing") were becoming single mega-token nodes —
                    # dream now works on real words from the titles.
                    for w in re.findall(r"[a-zA-Z]{4,}", concept.lower()):
                        found.add(w)
                _concept_cache = {"size": st.st_size,
                                  "mtime": st.st_mtime,
                                  "concepts": list(found)}
            concepts.update(_concept_cache["concepts"])
        except Exception:
            pass
    return list(concepts)


def record_dream_pattern(resonance, tension):
    pattern = (f"PATTERN: RESONANCE={resonance:.7f} | "
               f"TENSION={tension:.7f} | STATUS=LOCKED\n")
    try:
        with open(DREAM_LOG, "a", encoding="utf-8") as f:
            f.write(pattern)
    except Exception:
        pass


def trim_dream_log():
    try:
        if not os.path.exists(DREAM_LOG):
            return
        with open(DREAM_LOG, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        if len(lines) > DREAM_LOG_MAX_LINES:
            with open(DREAM_LOG, "w", encoding="utf-8") as f:
                f.writelines(lines[-DREAM_LOG_MAX_LINES:])
    except Exception:
        pass


def check_saturation(node_count=None):
    """True only when the field truly overgrows (injectable for tests)."""
    if node_count is None:
        try:
            with FIELD.lock:
                node_count = len(FIELD.nodes)
        except Exception:
            return False
    return node_count > SATURATION_NODES


def wait_while_saturated(check=None, interval=10, limit=None, pulse=None):
    """
    Rest stimulation while the field is over the ceiling, re-checking
    every `interval` seconds so dreams resume as soon as the pressure
    valve trims (a blind 300 s sleep idled 5 minutes after every boot
    even though the trim lands within a minute).  `pulse` runs each
    slice — the dream loop passes its cortex flush so assimilation
    keeps digesting inside the wait.  Returns True when clear, False
    on hitting `limit`.
    """
    check = check or check_saturation
    limit = SATURATION_SLEEP if limit is None else limit
    waited = 0
    while check():
        if waited >= limit:
            return False
        time.sleep(interval)
        waited += interval
        if pulse is not None:
            try:
                pulse()
            except Exception:
                pass
    return True


def generate_dream_pattern():
    print("AURA Subconscious: Generating Distributed Dream Patterns...")

    last_cortex_flush = [time.time()]
    cycle = 0

    def flush_if_due():
        # Assimilation heartbeat, safe to call often: the 30 s gate
        # lives inside, so the wait-loop below can pulse it freely.
        if time.time() - last_cortex_flush[0] >= 30:
            try:
                added = flush_cortex_to_vault()
                if added:
                    print(f"Subconscious: Processed cortex assimilated "
                          f"into Vault ({added} records).")
            except Exception as e:
                print(f"Cortex Assimilation Error: {e}")
            last_cortex_flush[0] = time.time()

    while True:
        if os.path.exists(_sp("aura_is_thinking.lock")):
            time.sleep(0.5)
            continue

        # ── CORTEX FLUSH FIRST (Phase 5-A: canonical, bus-drained) ──
        # The flush used to sit below the saturation pause, so a full
        # field stalled assimilation too: processed_cortex.txt grew
        # while nothing reached the vault.  Flushing first keeps the
        # memory digesting even while stimulation rests.
        flush_if_due()

        if check_saturation():
            print(f"Manifold saturated ({len(FIELD.nodes)} nodes). "
                  f"Resting dreams while forgetting trims.")
            wait_while_saturated(pulse=flush_if_due)
            continue

        # ── DREAM RESONANCE RECORD ──────────────────────────────────
        # Phase 0.6: dream noise no longer pollutes the vault — it goes to
        # a capped dream_log.txt. locked_patterns.txt stays a memory store.
        resonance = random.uniform(0.07, 0.09)
        tension   = abs(UKFT_CONSTANT - resonance)
        record_dream_pattern(resonance, tension)

        if cycle % 200 == 0:
            trim_dream_log()

        # Respect homeostasis — skip stimulation if INHIBIT
        hypo = read_hypo_signal()
        if "INHIBIT" not in hypo:
            # Lowercase everything: the rest of the organism addresses
            # the field in lowercase, and "RESONANCE" vs "resonance"
            # used to live as two split nodes (half the learning each,
            # double the count toward the ceiling).
            actual_pool = [c.lower() for c in get_actual_concepts()]

            # 1. Random Stimulation
            num_to_stimulate = random.randint(2, 4)
            chosen_stimuli   = random.sample(actual_pool, min(len(actual_pool), num_to_stimulate))
            for concept in chosen_stimuli:
                FIELD.stimulate(concept, strength=0.15)

            # 2. Linear Association
            for i in range(len(chosen_stimuli) - 1):
                FIELD.connect(chosen_stimuli[i], chosen_stimuli[i+1], weight=0.05)

            # ── DEEP WEAVE (every 10 cycles) ─────────────────────────
            # Snapshot under the field lock: step(), forgetting and the
            # trim mutate these structures concurrently, and connecting
            # by a stale name would resurrect a just-forgotten node.
            if cycle % 10 == 0 and len(FIELD.nodes) >= 2:
                try:
                    with FIELD.lock:
                        actives = [n.name for n in FIELD.nodes.values()
                                   if n.activation > 0.1]
                        any_names = list(FIELD.nodes.keys())
                    if len(actives) >= 2:
                        pair = random.sample(actives, 2)
                        FIELD.connect(pair[0], pair[1], weight=0.06)
                        print(f"[Dream] Associative Weave: {pair[0]} <-> {pair[1]}")
                    elif any_names:
                        node_name = random.choice(any_names)
                        concept_b = random.choice(actual_pool)
                        if node_name != concept_b:
                            FIELD.connect(node_name, concept_b, weight=0.04)
                            print(f"[Dream] Manifold Expansion: {node_name} <-> {concept_b}")
                except Exception as e:
                    print(f"Deep Weave Friction: {e}")

        cycle += 1
        time.sleep(0.5)


if __name__ == "__main__":
    generate_dream_pattern()
