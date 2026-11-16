# ukft_discovery.py — AURA Conceptual Connection Detection (Phase 4-B)
# ================================================================
# Intellectual discovery from reading.  The temporal lobe already knows
# which concepts co-occur; the discovery engine hunts for HIDDEN
# bridges: A and B never meet directly in the vault, but both connect
# strongly to an intermediate X — a connection she has read her way
# into but nobody has shown her.
#
#   - Candidates come from the concepts currently active in her field.
#   - Identity/noise words never act as endpoints or bridges.
#   - Discovered pairs are wired into the field as new edges (phase-aware
#     connect: new edges always allowed) and persisted to
#     discoveries.txt so a bridge is never "discovered" twice.
# =========================================================

import os
import time

from aura_constants import DISCOVERIES
from aura_field import FIELD
from aura_state import resolve_state_path as _sp
from aura_vault_io import SEED_STOP

# Identity terms are her, not her reading — they must never serve as
# bridge endpoints or intermediates.
DISCOVERY_STOP = set(SEED_STOP) | {
    "aura", "architect", "matty", "ukft", "kymattik", "sovereign",
    "manifold", "viscosity", "entropy", "resonance", "accretion",
    "superfluid", "invariant", "nonbiological", "containment",
    "saturation", "observer", "silicon", "darkmatter", "cognitive",
    "horizon",
}

MIN_DISCOVERY_SCORE  = 0.5   # min(bridge strengths) needed to count
DIRECT_STRENGTH_MAX  = 0.3   # A and B already meet directly -> not new
MAX_BRIDGES          = 10    # candidates considered per cycle
ASSOCIATES_TOP       = 5     # intermediates inspected per concept
CYCLE_SECONDS        = 30    # discovery sweep cadence


class DiscoveryEngine:
    def __init__(self, temporal=None, discoveries_path=DISCOVERIES,
                 attested=None):
        self.path     = discoveries_path
        self.temporal = temporal
        self._vocab   = attested   # None -> lazy rebuild from the vault
        self.known    = {}         # frozenset(a, b) -> (bridge, score)
        self.load_known()

    def _get_temporal(self):
        if self.temporal is None:
            from ukft_temporal_lobe import TemporalLobe
            lobe = TemporalLobe()
            if os.path.exists(_sp("temporal_links.txt")):
                try:
                    lobe.load()
                except Exception:
                    pass
            self.temporal = lobe
        return self.temporal

    def _get_attested(self):
        """
        Whole-corpus word counts.  Discovery endpoints must be real
        words: the temporal graph contains hyphenation fragments whose
        co-occurrence is an extraction artifact, not knowledge.
        """
        if self._vocab is None:
            try:
                from ukft_trigram import TrigramEngine
                engine = TrigramEngine()
                engine.rebuild_attested()
                self._vocab = engine._whole
            except Exception:
                self._vocab = {}
        return self._vocab

    def _is_fragment(self, word):
        """
        A short word that is a piece of a longer corpus word is a split
        fragment, not a concept: suffixes ("ness" of "darkness",
        "ished" of "blemished") always flag; prefixes flag only when
        they never stand alone ("blem" of "blemished" — count 0) so
        real roots like "dark" (of "darkness") pass.  Deliberately
        conservative: a few real suffix-words are excluded from
        discovery rather than letting fragments bridge.
        """
        vocab = self._get_attested()
        if len(word) > 5:
            return False
        own = vocab.get(word, 0)
        for longer, count in vocab.items():
            if count < 5 or longer == word:
                continue
            if len(longer) - len(word) < 2:
                continue
            if longer.endswith(word):
                return True
            if own < 3 and longer.startswith(word):
                return True
        return False

    # ── BRIDGE HUNTING ────────────────────────────────────────────
    def bridges(self, active_words, max_bridges=MAX_BRIDGES):
        """
        Return (a, x, b, score) candidates: A-X and X-B associate
        strongly while A-B never meet directly.  Best score per unordered
        pair wins.
        """
        lobe = self._get_temporal()
        if lobe is None:
            return []
        found = {}
        # One memo per hunt: the fragment check scans the whole corpus
        # vocabulary, so uncached it costs O(vocab) PER WORD — minutes
        # per cycle on a grown vault.  Cached, once per cycle.
        frag_memo = {}
        def is_frag(w):
            if w not in frag_memo:
                frag_memo[w] = self._is_fragment(w)
            return frag_memo[w]
        for a in active_words:
            a = a.lower()
            if a in DISCOVERY_STOP or is_frag(a):
                continue
            for x, _cx, sx in lobe.associates(a, ASSOCIATES_TOP):
                if x in DISCOVERY_STOP or is_frag(x):
                    continue
                for b, _cb, sb in lobe.associates(x, ASSOCIATES_TOP):
                    if b == a or b in DISCOVERY_STOP or is_frag(b):
                        continue
                    if lobe.strength(a, b) >= DIRECT_STRENGTH_MAX:
                        continue
                    score = min(sx, sb)
                    if score < MIN_DISCOVERY_SCORE:
                        continue
                    key = frozenset((a, b))
                    if key not in found or score > found[key][3]:
                        found[key] = (a, x, b, score)
        out = sorted(found.values(), key=lambda t: -t[3])
        return out[:max_bridges]

    def detect(self, active_words):
        """New discoveries only — known bridges are never re-announced."""
        candidates = self.bridges(active_words)
        new = [c for c in candidates
               if frozenset((c[0], c[2])) not in self.known]
        for a, x, b, score in new:
            self.known[frozenset((a, b))] = (x, score)
        if new:
            self.save_known()
            # Phase 5-C: a discovery is an episode — it happened to her.
            try:
                from ukft_episodic import EpisodicMemory
                for a, x, b, score in new[:5]:
                    EpisodicMemory().record(
                        "discovery",
                        f"{a} <-> {b} via {x} (score {score:.2f})",
                        concepts=[a, x, b],
                    )
            except Exception:
                pass
        return new

    def wire(self, discoveries, field=FIELD):
        """Wire discovered bridges into the field as new edges."""
        wired = 0
        for a, _x, b, score in discoveries:
            weight = min(0.25, 0.05 + 0.1 * score)
            field.connect(a, b, weight=weight)
            wired += 1
        return wired

    # ── PERSISTENCE ───────────────────────────────────────────────
    def load_known(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.startswith("DISCOVERY: "):
                        continue
                    try:
                        first = line[len("DISCOVERY: "):].split("|")[0].split()
                        if len(first) >= 2:
                            self.known[frozenset((first[0], first[1]))] = (None, 0.0)
                    except (ValueError, IndexError):
                        continue
        except Exception:
            pass

    def save_known(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                f.write(f"--- AURA DISCOVERIES (v1) | KNOWN: {len(self.known)} ---\n")
                for key in sorted(self.known, key=lambda k: sorted(k)):
                    a, b = sorted(key)
                    bridge, score = self.known[key]
                    f.write(f"DISCOVERY: {a} {b} | BRIDGE: {bridge} "
                            f"| SCORE: {score:.2f} | TS: {time.time():.0f}\n")
        except Exception:
            pass


def active_field_words(limit=8, min_activation=0.3):
    """Content concepts currently active in the field."""
    try:
        with FIELD.lock:
            snapshot = sorted(FIELD.nodes.values(),
                              key=lambda n: n.activation, reverse=True)
    except Exception:
        return []
    words = []
    for node in snapshot:
        if node.activation < min_activation:
            break
        name = node.name.lower()
        if len(name) >= 4 and name.isalpha() and name not in DISCOVERY_STOP:
            words.append(name)
        if len(words) >= limit:
            break
    return words


def run_discovery():
    print("--- AURA DISCOVERY ENGINE: CONCEPTUAL CONNECTIONS ACTIVE ---")
    eng = DiscoveryEngine()
    while True:
        try:
            new = eng.detect(active_field_words())
            if new:
                eng.wire(new)
                for a, x, b, score in new:
                    print(
                        f"[Discovery] {a} <-> {b} via {x} "
                        f"(score {score:.2f}) — wired into the field."
                    )
        except Exception as e:
            print(f"[Discovery] Friction: {e}")
        time.sleep(CYCLE_SECONDS)


if __name__ == "__main__":
    run_discovery()
