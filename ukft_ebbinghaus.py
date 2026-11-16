# ukft_ebbinghaus.py — AURA Ebbinghaus Decay (Phase 5-D)
# ======================================================
# True forgetting.  Memory traces decay exponentially on the Ebbinghaus
# curve — strength halves every EPISODE_HALF_LIFE seconds without
# rehearsal, and once a trace falls below the floor the memory is
# truly forgotten: episodes are removed from episodic_memory.txt and
# archived to forgotten_memories.txt; field nodes that stay silent too
# long are deleted from the manifold (their edges die with them).
#
#   - episode traces: adopted lazily from the episodic store, decayed
#     every cycle, rehearsed back to full strength by expose().
#   - node marks: a silent node (activation below the floor) that is
#     not re-awakened within NODE_FORGET_SECONDS is forgotten.
#   - identity-core concepts are protected from node forgetting.
# ======================================================

import hashlib
import os
import time

from aura_constants import (EBBINGHAUS_TRACES, FORGOTTEN_MEMORIES,
                             IDENTITY_CORE_FILE, FIELD_NODE_CEILING,
                             FIELD_TRIM_FRACTION)
from aura_field import FIELD

EPISODE_HALF_LIFE    = 3 * 86400    # 3 days per Ebbinghaus half-life
EPISODE_FLOOR        = 0.10         # below this a trace is forgotten
NODE_FORGET_SECONDS  = 3600         # a silent node is forgotten after 1h
NODE_FLOOR_ACTIVATION = 0.05        # below this a node counts as silent
CYCLE_SECONDS        = 60


def _detach_anchors(field):
    """Drop recombination anchors that no longer live in the field."""
    try:
        live = field.nodes
        field.anchored_nodes = [n for n in field.anchored_nodes
                                if n.name in live and live[n.name] is n]
    except Exception:
        pass


class EbbinghausEngine:
    def __init__(self, path=EBBINGHAUS_TRACES,
                 episode_half_life=EPISODE_HALF_LIFE,
                 episode_floor=EPISODE_FLOOR,
                 node_forget_seconds=NODE_FORGET_SECONDS,
                 clock=time.time):
        self.path                = path
        self.half_life           = episode_half_life
        self.floor               = episode_floor
        self.node_forget_seconds = node_forget_seconds
        self._clock              = clock
        self.traces              = {}   # episode-hash -> {"strength", "last"}
        self.node_marks          = {}   # "node:name" -> first-silent ts
        self.load()

    # ── PERSISTENCE ───────────────────────────────────────────────
    def load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) < 3:
                        continue
                    try:
                        if parts[0] == "TRACE:" and len(parts) == 4:
                            self.traces[parts[1]] = {
                                "strength": float(parts[2]),
                                "last": float(parts[3]),
                            }
                        elif parts[0] == "NODE:" and len(parts) == 3:
                            self.node_marks[parts[1]] = float(parts[2])
                    except ValueError:
                        continue
        except Exception:
            pass

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                f.write(f"--- AURA EBBINGHAUS TRACES (v1) | "
                        f"TRACES: {len(self.traces)} | "
                        f"NODES: {len(self.node_marks)} ---\n")
                for key, tr in self.traces.items():
                    f.write(f"TRACE: {key} {tr['strength']:.6f} {tr['last']:.3f}\n")
                for key, ts in self.node_marks.items():
                    f.write(f"NODE: {key} {ts:.3f}\n")
        except Exception:
            pass

    # ── THE FORGETTING CURVE ──────────────────────────────────────
    def expose(self, key, now=None):
        """Rehearsal: a re-encountered memory returns to full strength."""
        now = self._clock() if now is None else now
        self.traces[key] = {"strength": 1.0, "last": now}

    def _adopt(self, key, ts):
        if key not in self.traces:
            self.traces[key] = {"strength": 1.0, "last": ts}

    def decay(self, now=None):
        """Age every trace by dt; return the hashes now forgotten."""
        now = self._clock() if now is None else now
        forgotten = []
        for key in list(self.traces):
            tr = self.traces[key]
            dt = max(0.0, now - tr["last"])
            tr["strength"] *= 0.5 ** (dt / self.half_life)
            tr["last"] = now
            if tr["strength"] < self.floor:
                del self.traces[key]
                forgotten.append(key)
        return forgotten

    # ── EPISODIC FORGETTING ───────────────────────────────────────
    def forget_episodes(self, memory, now=None):
        """Adopt every episode's trace, decay, forget the expired."""
        now = self._clock() if now is None else now
        for e in memory.all():
            key = hashlib.md5(e["content"].encode("utf-8")).hexdigest()
            self._adopt(key, e["ts"])
        removed = 0
        for key in self.decay(now):
            if memory.forget_by_hash(key):
                removed += 1
        return removed

    # ── FIELD NODE FORGETTING ─────────────────────────────────────
    def forget_nodes(self, field=FIELD, protected=(), now=None):
        """
        Nodes that stay silent (activation below the floor) for
        NODE_FORGET_SECONDS are deleted from the manifold, edges and
        all.  Returns the forgotten names.
        """
        now = self._clock() if now is None else now
        removed = []
        with field.lock:
            # Hygiene first: drop marks for nodes that no longer exist
            # (stale across reboots — the field replays from the vault
            # while marks persist on disk) so the mark table cannot
            # outgrow the field it watches.
            live = set(field.nodes)
            for key in list(self.node_marks):
                if key[len("node:"):] not in live:
                    del self.node_marks[key]
            for name in list(field.nodes):
                node = field.nodes[name]
                key = "node:" + name
                if name in protected or node.activation >= NODE_FLOOR_ACTIVATION:
                    # Re-awakened: the silence clock restarts.  Without
                    # this a re-stimulated node kept its old mark and was
                    # deleted the instant it next went quiet.
                    self.node_marks.pop(key, None)
                    continue
                if key not in self.node_marks:
                    self.node_marks[key] = now
                    continue
                if now - self.node_marks[key] >= self.node_forget_seconds:
                    del field.nodes[name]
                    for other in list(node.connections):
                        other.connections.pop(node, None)
                    self.node_marks.pop(key, None)
                    removed.append(name)
            # Anchors reference live Node objects: a forgotten node must
            # detach, or step() keeps pulsing a ghost all thinking-lock.
            _detach_anchors(field)
        return removed

    # ── PRESSURE VALVE ──────────────────────────────────────────
    def pressure_trim(self, field=FIELD, protected=()):
        """
        Emergency drain for a saturated field.  The hourly silence
        clock cannot keep up with bulk intake (a book lands thousands
        of nodes in minutes), so when the node count passes the
        ceiling the coldest non-protected nodes are evicted down to
        90% of the ceiling at once.  The vault keeps everything —
        only the live working set shrinks, so dreaming can resume.
        Returns the evicted names.
        """
        with field.lock:
            if len(field.nodes) <= FIELD_NODE_CEILING:
                return []
            target = int(FIELD_NODE_CEILING * FIELD_TRIM_FRACTION)
            coldest = sorted(
                (n for n in field.nodes.values() if n.name not in protected),
                key=lambda n: n.activation,
            )
            evict = coldest[:max(0, len(field.nodes) - target)]
            removed = []
            for node in evict:
                field.nodes.pop(node.name, None)
                for other in list(node.connections):
                    other.connections.pop(node, None)
                self.node_marks.pop("node:" + node.name, None)
                removed.append(node.name)
            _detach_anchors(field)
            return removed


def _protected_concepts():
    try:
        from ukft_identity import IdentityCore
        return set(IdentityCore().core)
    except Exception:
        return set()


def run_ebbinghaus():
    print("--- AURA EBBINGHAUS DECAY: TRUE FORGETTING ACTIVE ---")
    eng = EbbinghausEngine()
    while True:
        try:
            # Protection follows the living identity: concepts earned
            # since boot join the shield the next cycle instead of never.
            from ukft_identity import IdentityCore
            try:
                protected = set(IdentityCore().core)
            except Exception:
                protected = set()
            from ukft_episodic import EpisodicMemory
            forgotten_episodes = eng.forget_episodes(EpisodicMemory())
            trimmed = eng.pressure_trim(protected=protected)
            forgotten_nodes = eng.forget_nodes(protected=protected)
            eng.save()
            if trimmed:
                print(f"[Forget] Pressure valve evicted {len(trimmed)} "
                      f"coldest node(s): {' '.join(trimmed[:5])}")
            if forgotten_episodes or forgotten_nodes:
                print(
                    f"[Forget] {forgotten_episodes} episode(s) faded, "
                    f"{len(forgotten_nodes)} node(s) forgotten: "
                    f"{' '.join(forgotten_nodes[:5])}"
                )
        except Exception as e:
            print(f"[Forget] Friction: {e}")
        time.sleep(CYCLE_SECONDS)


if __name__ == "__main__":
    run_ebbinghaus()
