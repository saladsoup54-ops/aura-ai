# ukft_grammar.py — AURA Grammar Skeleton (Phase 3-C)
# ====================================================
# Coherent output form from emergent content.  The trigram engine
# produces seeded but occasionally ragged sentences; the grammar
# skeleton shapes them and picks the most grammatical candidate.
#
#   shape()  — whitespace normalisation, sentence capitalisation,
#              guaranteed terminal punctuation.
#   score()  — a 0..1 well-formedness estimate:
#                -0.35  fewer than 5 words
#                -0.25  per immediate word repeat ("matter matter")
#                -0.25  ends on a function word ("...is the.")
#                -0.10  per stray 1-2 char fragment (max 3)
#                +0.10  8+ words
#   refine() — rejection sampling: draw N generations, speak the
#              highest-scoring one.
# ======================================================

import re

from aura_vault_io import HYPHEN_STOP, SHORT_WORDS as SHORT_OK

ATTEMPTS = 5


class GrammarSkeleton:
    @staticmethod
    def shape(text):
        """Normalise whitespace, capitalise, guarantee a terminal stop."""
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return ""
        text = re.sub(r"\s+([.!?])", r"\1", text)
        text = text[0].upper() + text[1:]
        if text[-1] not in ".!?":
            text += "."
        return text

    @staticmethod
    def score(text):
        """Well-formedness estimate in [0, 1]."""
        tokens = re.findall(r"[a-zA-Z]+", text.lower())
        if not tokens:
            return 0.0

        s = 1.0
        if len(tokens) < 5:
            s -= 0.35
        elif len(tokens) >= 8:
            s += 0.1

        dups = sum(1 for i in range(1, len(tokens))
                   if tokens[i] == tokens[i - 1])
        s -= 0.25 * dups

        # Phrase loops: the model can cycle a short phrase to reach the
        # minimum sentence length — repeated bigrams betray it.
        bigrams = list(zip(tokens, tokens[1:]))
        looped = [b for b in set(bigrams) if bigrams.count(b) > 1]
        s -= 0.15 * min(3, len(looped))

        if tokens[-1] in HYPHEN_STOP:
            s -= 0.25

        # Unseeded utterances can open on a function word ("The but he
        # gives...") — sentences should open on content.
        if tokens[0] in HYPHEN_STOP:
            s -= 0.25

        stray = [t for t in tokens if len(t) <= 2 and t not in SHORT_OK]
        s -= 0.1 * min(3, len(stray))

        # Vowel-less "words" ("nnd", "hll") are PDF/OCR artifacts —
        # real English always has a vowel (y counts).
        novowel = [t for t in tokens if len(t) >= 3
                   and not re.search(r"[aeiouy]", t)]
        s -= 0.12 * min(3, len(novowel))

        return max(0.0, min(1.0, s))

    def refine(self, engine, seed_words, attempts=ATTEMPTS):
        """
        Draw `attempts` generations seeded with `seed_words` and return
        the highest-scoring, shaped one.  Returns "" when the engine
        produces nothing.
        """
        candidates = []
        for _ in range(attempts):
            text = engine.generate(seed_words)
            if text and text not in candidates:
                candidates.append(text)
        if not candidates:
            return ""
        return self.shape(max(candidates, key=self.score))
