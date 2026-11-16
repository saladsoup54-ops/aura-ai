import heapq
import json
import math
import threading

from aura_bus import write as bus_write
from aura_constants import D_INVARIANT as D, FIELD_ACTIVATION_LEAK

# Governed by Unified Kymattik Field Theory 4.3.2 · D = 0.0804245


class Node:
    def __init__(self, name):
        self.name        = name
        self.activation  = 0.0
        self.velocity    = 0.0
        self.connections = {}
        # Phase 1-B: FLUID / FROZEN state per node
        self.phase       = "FROZEN"


class CognitiveField:
    def __init__(self):
        self.nodes = {}
        self.lock  = threading.Lock()

        # Phase 1-D: CMB viscous anchor
        # When aura_is_thinking.lock is present, the top-5 nodes at that
        # moment are captured here and receive a stabilising pulse each step.
        self.recombination_mode = False
        self.anchored_nodes     = []   # list of Node objects

    def get_node(self, name):
        if name not in self.nodes:
            self.nodes[name] = Node(name)
        return self.nodes[name]

    def add_node(self, name, activation=0.0):
        """Create a node with a pre-set activation level (used by SovereignEgo)."""
        with self.lock:
            node = self.get_node(name)
            node.activation = max(0.0, min(1.0, float(activation)))
            return node

    def connect(self, a, b, weight=0.1):
        """
        Bi-directional connection (lock-protected).
        Phase 0.8: rewrites are phase-aware — if either endpoint is FROZEN,
        an EXISTING edge's weight is never rewritten (consolidated memories
        are immutable, roadmap 1-B). Brand-new edges are always allowed:
        structural growth is not consolidation.  Self-connections are
        refused outright — a node stimulating itself every step is a
        perpetual-motion loop, and Hebbian growth would pin it at 1.0.
        """
        if a == b:
            return None
        with self.lock:
            na = self.get_node(a)
            nb = self.get_node(b)
            if nb in na.connections and (
                    na.phase == "FROZEN" or nb.phase == "FROZEN"):
                return None
            na.connections[nb] = weight
            nb.connections[na] = weight
            return weight

    def stimulate(self, name, strength=1.0):
        with self.lock:
            node = self.get_node(name)
            # Phase 1-D: During recombination, new stimulation arrives at 20% strength
            if self.recombination_mode:
                strength *= 0.2
            node.velocity += strength

    def woods_saxon(self, rho, V0=0.5, delta=0.01):
        try:
            return 1 / (1 + math.exp((rho - V0) / delta))
        except OverflowError:
            return 0.0

    # ── Phase 0-A: Holographic Viscosity Lock ─────────────────────────
    def calculate_field_entropy(self):
        """
        Calculates field entropy (s) as the normalised activation distribution.
        This determines the Viscosity Lock strength.
        """
        activations = [n.activation for n in self.nodes.values()]
        total = sum(activations)

        if total <= 0 or len(activations) < 2:
            return 0.0

        entropy = 0.0
        for a in activations:
            if a > 0:
                p = a / total
                entropy -= p * math.log(p)

        max_entropy = math.log(len(activations))
        return entropy / max_entropy

    def apply_viscosity_lock(self, node, entropy_s):
        """
        PHASE 0-A: Holographic Viscosity Lock
        Formula: ηχ/s = ℏ/4πkB · (1+D)
        Viscosity scales with entropy to resist saturation.
        """
        viscosity = D + (1.0 - D) * entropy_s
        node.velocity *= (1 - viscosity)

    # ── Phase 1-D: CMB anchor management ──────────────────────────────
    def enter_recombination(self):
        """
        Called when aura_is_thinking.lock is written.
        Captures the top-5 active nodes as anchors; they receive a
        continuous stabilising pulse per step so active context can't
        be washed out by incoming stimulation during response generation.
        """
        with self.lock:
            self.recombination_mode = True
            snapshot = heapq.nlargest(5, self.nodes.values(),
                                      key=lambda n: n.activation)
            self.anchored_nodes = [n for n in snapshot if n.activation > 0.05]

    def exit_recombination(self):
        """Called when aura_is_thinking.lock is removed."""
        with self.lock:
            self.recombination_mode = False
            self.anchored_nodes     = []

    # ── Phase 1-C: RAR-style proximity decay helper ────────────────────
    def _rar_decay(self, active_subset):
        """
        Radial Acceleration Relation — adapted for graph distance.

        Nodes directly connected to the active cluster (proximate) decay
        at a gentle rate (velocity *= 0.85).  Nodes with no path to any
        active node (distant) cool 5.7× faster (velocity *= 0.15).

        This gives the field spatial memory: related concepts stay warm,
        unrelated concepts cool quickly.  O(nodes + edges) per step.
        """
        active_set = set(id(n) for n in active_subset)

        # Build the set of proximate nodes: direct neighbours of active nodes
        proximate = set()
        for node in active_subset:
            for neighbour in node.connections:
                if id(neighbour) not in active_set:
                    proximate.add(id(neighbour))

        for node in self.nodes.values():
            nid = id(node)
            if nid in active_set:
                continue   # Active nodes are handled by the main physics loop
            if nid in proximate:
                node.velocity *= 0.85   # Gentle cooling — stay warm
            else:
                node.velocity *= 0.15   # Fast cooling — graph-distant

    def step(self):
        with self.lock:            # ── 0. GLOBAL ENTROPY ──────────────────────────────────────
            s = self.calculate_field_entropy()

            # ── ATTENTION GATE ─────────────────────────────────────────
            sorted_nodes = sorted(self.nodes.values(),
                                  key=lambda n: n.activation, reverse=True)
            active_subset = [n for n in sorted_nodes[:10] if n.activation > 0.1]

            # ── 1. ACTIVATION SPREAD (attended nodes only) ─────────────
            for node in active_subset:
                for target, weight in node.connections.items():
                    target.velocity += node.activation * weight * 0.05

            # ── 2. HEBBIAN LEARNING ────────────────────────────────────
            # Phase 1-B: only runs on FLUID nodes (activation > V0 = 0.5)
            # FROZEN nodes (activation <= 0.5) spread activation but their
            # connection weights are immutable — consolidated memories can't
            # be silently rewritten by strong re-activation.  BOTH ends
            # must be FLUID: strengthening into a FROZEN target rewrote
            # the very edges connect() refuses to touch.
            for node in active_subset:
                if node.phase == "FLUID" and node.activation > 0.6:
                    for target in node.connections.keys():
                        if target.phase == "FLUID" and target.activation > 0.5:
                            node.connections[target] += 0.01
                            node.connections[target] = min(node.connections[target], 1.0)

            # ── 3. RAR PROXIMITY DECAY (Phase 1-C) ────────────────────
            self._rar_decay(active_subset)

            # ── 4. CMB STABILISING PULSE (Phase 1-D) ──────────────────
            if self.recombination_mode:
                for node in self.anchored_nodes:
                    node.velocity += 0.02

            # ── 5. GLOBAL PHYSICS (UKFT) ───────────────────────────────
            for node in self.nodes.values():
                rho  = abs(node.activation)
                gate = self.woods_saxon(rho)

                # Phase 1-B: set node phase from Woods-Saxon threshold
                node.phase = "FLUID" if rho > 0.5 else "FROZEN"

                node.velocity *= gate
                self.apply_viscosity_lock(node, s)
                node.activation += node.velocity
                # Saturation fix: activation used to be monotonic — every
                # term feeding velocity is non-negative, so stimulated
                # nodes ratcheted to 1.0 forever and forgetting (silence
                # below 0.05 for an hour) could never fire on a live
                # field.  The leak lets silent hubs decay (halve in
                # ~12 min) while live stimulation outruns it trivially.
                node.activation *= FIELD_ACTIVATION_LEAK
                node.velocity   *= 0.35
                node.activation  = max(0.0, min(1.0, node.activation))

            # ── Bug A fix: field_stats.txt is owned exclusively by step() ──
            # Phase 0.5: schema upgraded from a bare entropy float to JSON.
            # Homeostasis must regulate on field TENSION (activation scale),
            # not on entropy — comparing s ∈ [0,1] against D = 0.0804245
            # pinned the Hypothalamus to INHIBIT forever.
            # Snapshot under the lock; the file write happens AFTER
            # release — holding the global lock across file I/O stalled
            # every stimulator on every slow disk tick.
            try:
                top5 = heapq.nlargest(5, self.nodes.values(),
                                      key=lambda n: n.activation)
                payload = {
                    "s":              round(s, 6),
                    "tension":        round(
                        (sum(n.activation for n in top5) / len(top5))
                        if top5 else 0.0, 6),
                    "top":            top5[0].name if top5 else "",
                    "top_activation": round(top5[0].activation, 6) if top5 else 0.0,
                    "nodes":          len(self.nodes),
                }
            except Exception:
                payload = None
        # ── lock released here ──
        if payload is not None:
            try:
                # Phase 5-A: telemetry flows through the bus so readers
                # never catch a half-written measurement.
                bus_write("field_stats.txt", json.dumps(payload))
            except Exception:
                pass


# GLOBAL FIELD
FIELD = CognitiveField()
