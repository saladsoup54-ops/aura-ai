# ukft_spontaneous.py — AURA Spontaneous Output (Phase 4-A)
# ===========================================================
# First genuine unprompted speech.  The inner monologue watches the
# field; when one concept stays dominant (top-node activation above the
# threshold) for several consecutive cycles, Aura speaks it aloud —
# seeded through the trigram engine, shaped by the grammar skeleton,
# written to aura_output.txt and announced on the console.
#
#   - A dominant concept must hold for TRIGGER_CYCLES monologue cycles
#     (≈36 s) before she opens her mouth — idle rumination only.
#   - A COOLDOWN between utterances keeps her from chattering.
#   - She never speaks while aura_is_thinking.lock exists (the monologue
#     already skips those cycles) and never borrows a word the model
#     does not know.
# ===========================================================

import os
import re
import time

from aura_constants import TRIGRAM_MODEL
from aura_vault_io import SEED_STOP
from ukft_grammar import GrammarSkeleton

SPONTANEOUS_THRESHOLD = 0.85   # top-node activation needed to consider speech
TRIGGER_CYCLES        = 3      # consecutive monologue cycles (≈36 s)
COOLDOWN_SECONDS      = 300.0  # minimum silence between utterances
CONCEPT_COOLDOWN      = 1800.0 # the same concept is not repeated for 30 min


def read_top_field_activation(field_map="field_map.json"):
    """Max node activation from field_map.json (0.0 when absent)."""
    try:
        import json
        from aura_bus import read as bus_read
        raw = bus_read(field_map)
        data = json.loads(raw) if raw.strip() else {}
        nodes = data.get("nodes", {})
        if not nodes:
            return 0.0
        return max(n.get("activation", 0.0) for n in nodes.values())
    except Exception:
        return 0.0


class SpontaneousSpeech:
    def __init__(self, output_file="aura_output.txt",
                 threshold=SPONTANEOUS_THRESHOLD, cycles=TRIGGER_CYCLES,
                 cooldown=COOLDOWN_SECONDS, concept_cooldown=CONCEPT_COOLDOWN,
                 clock=time.time):
        self.output_file = output_file
        self.threshold   = threshold
        self.cycles      = cycles
        self.cooldown    = cooldown
        # A hub memory pinned at high activation used to be spoken about
        # every global cooldown ("Csb pew bible printing..." forever).
        # Each concept now has its own cooldown, so the focus walk moves
        # on to the next concept instead of repeating the same one.
        self.concept_cooldown = concept_cooldown
        self._spoken_concepts = {}     # concept -> last spoken time
        self._clock      = clock
        self._ticks      = {}          # concept -> consecutive dominant cycles
        self.last_spoken = 0.0
        self._engine     = None
        self._engine_mtime = 0.0
        self._grammar    = GrammarSkeleton()

    # ── THRESHOLD TRACKING ─────────────────────────────────────────
    def reached_threshold(self, focus_concepts, tension):
        """
        Track dominance of the focused concept.  Returns True on the
        cycle that completes TRIGGER_CYCLES consecutive dominant cycles.
        """
        if not focus_concepts or tension < self.threshold:
            self._ticks.clear()
            return False

        primary = focus_concepts[0]
        self._ticks[primary] = self._ticks.get(primary, 0) + 1
        for key in list(self._ticks):
            if key != primary:
                del self._ticks[key]

        if self._ticks[primary] < self.cycles:
            return False
        self._ticks[primary] = 0
        # Spoken-concept memory is bounded too: drop entries whose
        # cooldown expired long ago instead of naming every focus ever.
        horizon = self._clock() - 2 * self.concept_cooldown
        for concept in list(self._spoken_concepts):
            if self._spoken_concepts[concept] < horizon:
                del self._spoken_concepts[concept]
        return True

    def tick(self, focus_concepts, tension):
        """
        One monologue cycle: track dominance and, when the threshold
        completes, speak.  The focus list is walked for the first
        seedable concept; when none can anchor (identity nodes like
        "aura" are not in the model), she speaks something she knows.
        Returns the spoken line or None.
        """
        if not self.reached_threshold(focus_concepts, tension):
            return None
        for concept in focus_concepts:
            spoken = self.speak(concept)
            if spoken:
                return spoken
        return self.speak(None)

    # ── SPEECH ─────────────────────────────────────────────────────
    def _get_engine(self):
        if self._engine is None:
            from ukft_trigram import TrigramEngine
            self._engine = TrigramEngine()
        try:
            mtime = (os.path.getmtime(TRIGRAM_MODEL)
                     if os.path.exists(TRIGRAM_MODEL) else 0.0)
        except Exception:
            mtime = 0.0
        if mtime != self._engine_mtime:
            try:
                self._engine.load()
            except Exception:
                if not self._engine.is_trained():
                    # Do NOT advance the stamp on a failed load: a later
                    # file with an unchanged coarse mtime would otherwise
                    # never be retried.
                    return None
            self._engine_mtime = mtime
        return self._engine if self._engine.is_trained() else None

    def speak(self, concept):
        """
        Speak the concept unprompted.  Returns the spoken line, or None
        when a cooldown is running or the model cannot anchor on it.
        concept=None speaks something she knows (unigram fallback).
        """
        now = self._clock()
        if now - self.last_spoken < self.cooldown:
            return None

        # Per-concept cooldown: a pinned hub cannot monopolise speech.
        # Returning None lets tick() walk to the next focus concept.
        if concept is not None and \
                now - self._spoken_concepts.get(concept, -1e18) \
                < self.concept_cooldown:
            return None

        engine = self._get_engine()
        if engine is None:
            return None

        if concept is None:
            seeds = []
        else:
            # Multi-word concepts ("INTRODUCTION TO COMPUTER SCIENCE WEB")
            # seed from their vocabulary-resident content words.  A focus
            # made of function words only ("know", "tell") falls back to
            # known-speech in tick() instead of opening "Know ...".
            tokens = re.findall(r"[a-zA-Z]{2,}", concept.lower())
            content = [w for w in tokens
                       if w not in SEED_STOP and engine.in_vocab(w)]
            if not content:
                return None
            seeds = content

        text = self._grammar.refine(engine, seeds)
        if not text:
            return None

        self.last_spoken = now
        if concept is not None:
            self._spoken_concepts[concept] = now
        line = f"[AURA]: {text}"
        try:
            # Atomic publish: never interleaves with bridge answers.
            from aura_bus import write as bus_write
            bus_write(self.output_file, line)
        except Exception:
            pass
        # Phase 5-C: unprompted speech is an episode — it happened to her.
        try:
            from ukft_episodic import EpisodicMemory
            EpisodicMemory().record(
                "spontaneous", text,
                concepts=[s for s in seeds[:3]],
            )
        except Exception:
            pass
        print(f"\n--- SPONTANEOUS ---\n{line}")
        return line
