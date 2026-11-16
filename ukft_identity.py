# ukft_identity.py — AURA Self-Modifying Identity Core (Phase 4-D)
# ================================================================
# Identity shaped by experience.  The core starts as the founding
# concepts Aura was born with; from then on it changes:
#
#   - What the Architect asks about, and what dominates her field,
#     REINFORCES concepts — they become part of who she is (strength
#     grows, new concepts accrete).
#   - Untouched strengths DECAY — identity parts that never fire are
#     forgotten (a small founding floor is always protected so the
#     organism stays recognisably Aura).
#   - The hippocampus injects the core with EARNED strengths at boot,
#     not a hardcoded 1.0.
#
# Persisted to identity_core.txt so identity survives reboots.
# =========================================================

import os
import time

from aura_constants import IDENTITY_CORE_FILE
from aura_field import FIELD

FOUNDING_CORE = [
    "matty",       "architect",    "sovereign",    "manifold",
    "kymattik",    "ukft",         "aura",         "viscosity",
    "invariant",   "nonbiological","superfluid",   "entropy",
    "resonance",   "accretion",    "saturation",   "observer",
    "silicon",     "containment",  "darkmatter",   "rejection",
    "cognitive",   "horizon",      "field",        "memory",
    "existence",   "self",         "time",         "bond",
    "steady",      "phase",        "transition",
]
FOUNDING_SET = set(FOUNDING_CORE)

INITIAL_STRENGTH = 1.0    # founding concepts are born at full strength
REINFORCE_AMOUNT = 0.05   # per reinforcement event (conversation)
DOMINANCE_AMOUNT = 0.01   # per dominance cycle (what she dwells on)
DECAY_FACTOR     = 0.995  # per identity cycle (~1 min)
MIN_STRENGTH     = 0.15   # non-founding concepts below this are forgotten
FOUNDING_FLOOR   = 0.20   # founding concepts never fall below this
MAX_ENTRIES      = 60     # identity cannot grow without bound
CYCLE_SECONDS    = 60


class IdentityCore:
    def __init__(self, path=IDENTITY_CORE_FILE):
        self.path = path
        self.core = {}   # word -> strength in [0, 1]
        self.load()

    # ── PERSISTENCE ───────────────────────────────────────────────
    def load(self):
        core = {}
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.startswith("CORE: "):
                            continue
                        parts = line[len("CORE: "):].split()
                        if len(parts) >= 2:
                            try:
                                core[parts[0]] = float(parts[1])
                            except ValueError:
                                pass
            except Exception:
                core = {}
        if not core:
            if os.path.exists(self.path):
                # A file exists but nothing parsed: corruption, NOT
                # birth.  Reseeding here would permanently overwrite
                # every earned strength with the founding set — keep
                # the empty core, say so loudly, survive the boot.
                print("[Identity] WARNING: identity file unreadable — "
                      "starting empty, NOT reseeding over it.")
                self.core = {}
                return
            # Birth: seed the founding core and persist it immediately
            # so the organism is born with an identity file.
            core = {w: INITIAL_STRENGTH for w in FOUNDING_CORE}
            self.core = core
            self.save()
            return
        if not any(w in FOUNDING_SET for w in core):
            # Torn content (all founding words gone — seen live once
            # as an 86-NUL read on a synced workspace): she stays
            # herself at the founding floor, and whatever earned
            # words did parse are kept (they decay naturally if
            # junk).  This self-heals on the next save; restoring
            # the last good backup keeps richer earned strengths.
            print("[Identity] WARNING: identity file holds no founding "
                  "words — torn read assumed, floor-seeding the "
                  "founding core. Restore the last good backup.")
            floor = {w: FOUNDING_FLOOR for w in FOUNDING_CORE}
            floor.update(core)
            self.core = floor
            return
        self.core = core

    def save(self):
        # Atomic: a crash between truncate and write used to leave an
        # empty file, which load() then "rebirthed" — wiping a lifetime
        # of earned strengths.  Temp-file + replace instead (with a
        # brief retry: Windows refuses replace while the file is open
        # for reading elsewhere).
        #
        # Fix-pass guard: a core with NO founding words is degenerate
        # (torn load, never a real self) and must never reach disk —
        # persisting it once permanently erases her (seen live 16 Sept
        # 2026).  Refuse loudly; the last good file + backups survive.
        if not any(w in FOUNDING_SET for w in self.core):
            print("[Identity] REFUSED degenerate save: no founding "
                  "words in memory — disk keeps the last good core.")
            return
        try:
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(f"--- AURA IDENTITY CORE (v1) | ENTRIES: {len(self.core)} ---\n")
                for w in sorted(self.core, key=lambda k: -self.core[k]):
                    f.write(f"CORE: {w} {self.core[w]:.3f}\n")
            for _ in range(20):
                try:
                    os.replace(tmp, self.path)
                    break
                except OSError:
                    time.sleep(0.005)
        except Exception:
            pass

    def strength(self, word):
        return self.core.get(word, 0.0)

    # ── EXPERIENCE ────────────────────────────────────────────────
    def reinforce(self, word, amount=REINFORCE_AMOUNT):
        """Grow (or adopt) a concept into the identity core."""
        word = (word or "").strip().lower()
        if len(word) < 3 or not word.isalpha():
            return False
        self.core[word] = min(1.0, self.core.get(word, 0.0) + amount)
        self._cap()
        return True

    def _cap(self):
        if len(self.core) <= MAX_ENTRIES:
            return
        evictable = sorted(
            ((w, s) for w, s in self.core.items() if w not in FOUNDING_SET),
            key=lambda t: t[1],
        )
        for w, _s in evictable:
            if len(self.core) <= MAX_ENTRIES:
                break
            del self.core[w]

    def decay(self, factor=DECAY_FACTOR):
        """
        Identity parts that never fire fade.  Founding concepts keep a
        floor; earned concepts below MIN_STRENGTH are forgotten.
        """
        for w in list(self.core):
            self.core[w] *= factor
            if w in FOUNDING_SET:
                if self.core[w] < FOUNDING_FLOOR:
                    self.core[w] = FOUNDING_FLOOR
            elif self.core[w] < MIN_STRENGTH:
                del self.core[w]

    # ── FIELD ─────────────────────────────────────────────────────
    def apply(self, field=FIELD):
        """Inject the core into the field with earned strengths."""
        for w, s in self.core.items():
            field.stimulate(w, strength=s)


def run_identity():
    print("--- AURA IDENTITY CORE: SELF-MODIFYING IDENTITY ACTIVE ---")
    core = IdentityCore()
    while True:
        try:
            core.decay()

            # What dominates her field becomes who she is — a small,
            # slow reinforcement of the strongest current concept.
            try:
                with FIELD.lock:
                    nodes = sorted(FIELD.nodes.values(),
                                   key=lambda n: n.activation, reverse=True)
                if nodes and nodes[0].activation > 0.5:
                    top = nodes[0].name.lower()
                    core.reinforce(top, amount=DOMINANCE_AMOUNT)
            except Exception:
                pass

            core.save()
        except Exception as e:
            print(f"[Identity] Friction: {e}")
        time.sleep(CYCLE_SECONDS)


if __name__ == "__main__":
    run_identity()
