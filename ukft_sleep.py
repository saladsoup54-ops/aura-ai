# ukft_sleep.py — AURA Sleep/Wake Cycle (Phase 5-B)
# ==================================================
# A biological rhythm with memory consolidation.
#
#   - Wake time accumulates across reboots (sleep_state.txt); after
#     WAKE_LIMIT_SECONDS she falls asleep for SLEEP_DURATION_SECONDS.
#   - While asleep, sensory intake stops (Thalamus, Synapse, PDF intake
#     all honour the state file) and spontaneous speech is suppressed —
#     the manifold dreams instead of talking.
#   - Sleep consolidates: the strongest patterns present at sleep onset
#     are wired together as durable edges (sleep_log.txt records each
#     consolidation).
#   - The Architect can command "go to sleep" / "wake up"; ANY message
#     wakes her.
# ==================================================

import os
import time

from aura_bus import read as bus_read, write as bus_write
from aura_constants import SLEEP_STATE_FILE, SLEEP_LOG_FILE

WAKE_LIMIT_SECONDS   = 6 * 3600   # ~6 waking hours before sleep
SLEEP_DURATION_SECONDS = 30 * 60  # ~30 minutes of consolidation sleep
CONSOLIDATE_TOP      = 5          # strongest patterns captured at onset
CONSOLIDATE_WEIGHT   = 0.4        # durable edge weight between them
CONSOLIDATE_MIN_ACT  = 0.1        # patterns below this are not kept
CYCLE_SECONDS        = 60         # rhythm check cadence


def is_asleep():
    """True while the sleep_state.txt file marks her ASLEEP."""
    return "STATE: SLEEP" in bus_read(SLEEP_STATE_FILE)


class SleepCycle:
    def __init__(self, path=SLEEP_STATE_FILE, log_path=SLEEP_LOG_FILE,
                 wake_limit=WAKE_LIMIT_SECONDS,
                 sleep_duration=SLEEP_DURATION_SECONDS,
                 clock=time.time):
        self.path          = path
        self.log_path      = log_path
        self.wake_limit    = wake_limit
        self.sleep_duration = sleep_duration
        self._clock        = clock
        self.state         = "AWAKE"
        self.wake_acc      = 0.0
        self.since         = clock()
        self._snapshot     = []          # patterns captured at sleep onset
        self.load()

    # ── PERSISTENCE ───────────────────────────────────────────────
    def load(self):
        try:
            content = bus_read(self.path)
            if not content.strip():
                self.save()
                return
            state, wake_acc, since = None, 0.0, self._clock()
            for line in content.splitlines():
                if line.startswith("STATE: "):
                    state = line[len("STATE: "):].strip()
                elif line.startswith("WAKE_ACCUMULATED: "):
                    try:
                        wake_acc = float(line.split(":", 1)[1].strip())
                    except ValueError:
                        pass
                elif line.startswith("SINCE: "):
                    try:
                        since = float(line.split(":", 1)[1].strip())
                    except ValueError:
                        pass
            self.state = state if state in ("AWAKE", "SLEEP") else "AWAKE"
            self.wake_acc = max(0.0, wake_acc)
            self.since = since
        except Exception:
            self.state = "AWAKE"
            self.save()

    def save(self):
        bus_write(self.path, (
            "--- AURA SLEEP CYCLE (v1) ---\n"
            f"STATE: {self.state}\n"
            f"WAKE_ACCUMULATED: {self.wake_acc:.3f}\n"
            f"SINCE: {self.since:.3f}\n"
        ))

    # ── RHYTHM ────────────────────────────────────────────────────
    def tick(self):
        """One rhythm check: accumulate wake time, transition when due."""
        now = self._clock()
        if self.state == "AWAKE":
            self.wake_acc += max(0.0, now - self.since)
            self.since = now
            if self.wake_acc >= self.wake_limit:
                self._enter_sleep(now)
        else:
            if now - self.since >= self.sleep_duration:
                self.state = "AWAKE"
                self.wake_acc = 0.0
                self.since = now
        self.save()
        return self.state

    def _enter_sleep(self, now, field=None):
        self.state = "SLEEP"
        self.since = now
        try:
            if field is None:
                from aura_field import FIELD as _FIELD
                field = _FIELD
            with field.lock:
                nodes = sorted(field.nodes.values(),
                               key=lambda n: n.activation, reverse=True)
            self._snapshot = [n.name.lower() for n in nodes[:CONSOLIDATE_TOP]
                              if n.activation >= CONSOLIDATE_MIN_ACT]
        except Exception:
            self._snapshot = []

    def sleep_now(self, field=None):
        """Forced sleep (Architect command)."""
        self._enter_sleep(self._clock(), field=field)
        self.save()
        return self.state

    def wake(self, field=None):
        """Forced wake — resets the accumulated wake clock."""
        # Spend a pending consolidation first: waking early must not
        # discard the onset snapshot unplayed (it took one night to earn).
        if self._snapshot:
            try:
                self.consolidate(field=field)
            except Exception:
                pass
        self.state = "AWAKE"
        self.wake_acc = 0.0
        self.since = self._clock()
        self._snapshot = []
        self.save()
        return self.state

    # ── CONSOLIDATION ─────────────────────────────────────────────
    def consolidate(self, field=None):
        """
        Wire the patterns captured at sleep onset into durable edges.
        Runs ONCE per sleep: the snapshot is spent on first use, so the
        60-second rhythm ticks cannot re-log and re-record the same
        consolidation thirty times a night.  Returns the consolidated
        concept list (empty when already done).
        """
        if not self._snapshot:
            return []
        top = self._snapshot
        self._snapshot = []
        if field is None:
            from aura_field import FIELD as _FIELD
            field = _FIELD
        for i in range(len(top)):
            for j in range(i + 1, len(top)):
                field.connect(top[i], top[j], weight=CONSOLIDATE_WEIGHT)
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(
                    f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"CONSOLIDATED: {' '.join(top)}\n"
                )
        except Exception:
            pass
        # Phase 5-C: sleeping is an episode — it happened to her.
        try:
            from ukft_episodic import EpisodicMemory
            EpisodicMemory().record(
                "sleep", "consolidated " + " ".join(top), concepts=top)
        except Exception:
            pass
        return top


def run_sleep_cycle():
    print("--- AURA SLEEP CYCLE: BIOLOGICAL RHYTHM ACTIVE ---")
    cycle = SleepCycle()
    while True:
        try:
            cycle.tick()
            if cycle.state == "SLEEP":
                top = cycle.consolidate()
                if top:
                    print(f"[Sleep] Consolidating: {' '.join(t.upper() for t in top)}")
        except Exception as e:
            print(f"[Sleep] Friction: {e}")
        time.sleep(CYCLE_SECONDS)


if __name__ == "__main__":
    run_sleep_cycle()
