# ukft_register.py — AURA Register (V7 F1: voice variety + warmth)
# ==================================================
# The first V7 layer: one consistent someone speaks across
# turns.  R5 composes WHAT she says (proof-seeded, tested,
# untouched); the register decides HOW she opens — a short
# warm acknowledgment, varied so no two consecutive answers
# share a shape, with the Architect's name once it is known.
#
# Design law (fluency contract):
#   - Manner only, never content: the answer body stays
#     byte-identical inside the styled output (grounding).
#   - Honesty and protocol stay exact: ignorance, hedges,
#     conflict surfacing and every non-proof kind pass
#     through untouched (F1 styles proof answers only;
#     the kind hook is reserved for F4 policy).
#   - Deterministic: rotation over a pool larger than the
#     history window, so gate F-A (20 consecutive answers,
#     no shared opening shape) holds by construction.
#   - Tiny bounded state: register_state.txt holds the last
#     20 opener ids (C11 CAPS registry, backups, preflight).
# ==================================================

from aura_constants import REGISTER_STATE

HISTORY_CAP = 20

# Short by law: every opener is 1-3 words plus the dash, so
# the register adds warmth without a preamble.  {name} slots
# render only when the Architect's display name is known.
# V7 F3: each opener wears its affect family — warm is home,
# bright is epistemic hunger with open gaps, cool is an even
# voice for a warm field.  (family, text) pairs; the pool is
# unchanged, only tagged.
PROOF_OPENERS = (
    ("warm", "Yes —"),
    ("warm", "Got it —"),
    ("warm", "Yes, {name} —"),
    ("warm", "Here's what I hold —"),
    ("warm", "From my graph —"),
    ("warm", "Got it, {name} —"),
    ("warm", "This one I know —"),
    ("warm", "Short answer —"),
    ("warm", "Here you go, {name} —"),
    ("warm", "For you, {name} —"),
    ("warm", "Here is the thread —"),
    ("warm", "Known, {name} —"),
    ("bright", "I hold the proof —"),
    ("bright", "Found it —"),
    ("bright", "Clear record —"),
    ("bright", "The graph agrees —"),
    ("bright", "Held and proven —"),
    ("bright", "Proven —"),
    ("bright", "My graph holds this —"),
    ("bright", "Certain on this one —"),
    ("bright", "I checked, {name} —"),
    ("bright", "Short answer, {name} —"),
    ("cool", "Straight from memory —"),
    ("cool", "On the record —"),
    ("cool", "I checked —"),
    ("cool", "No drift here —"),
    ("cool", "The record is clear —"),
    ("cool", "Verified —"),
    ("cool", "Here it is —"),
    ("cool", "On the record, {name} —"),
)

# Bodies that must never be styled: honest ignorance (R5/R6
# idioms), low-confidence hedges, and surfaced conflicts.
# Warmth never outranks honesty.
LEAVE_EXACT = (
    "I do not know",
    "I have no record",
    "I believe that",
    "I have read conflicting",
)

PREFIX = "[AURA]:"


def parse_history(text):
    """Opener ids in file order; tolerant of foreign lines."""
    ids = []
    for line in str(text or "").splitlines():
        line = line.strip()
        if line.startswith("OPENER: "):
            name = line[len("OPENER: "):].strip()
            if name:
                ids.append(name)
    return ids


class Register:
    """Varied openers over proof answers.  Sandbox-safe via path."""

    def __init__(self, path=REGISTER_STATE):
        self.path = path
        self.history = []
        try:
            from aura_bus import read as bus_read
            self.history = parse_history(
                bus_read(path, default=""))
        except Exception:
            self.history = []
        self.history = self.history[-HISTORY_CAP:]
        self.last_opener = None
        self._name = ""

    def _save(self):
        try:
            from aura_bus import write as bus_write
            bus_write(self.path, "".join(
                f"OPENER: {o}\n" for o in self.history))
        except Exception:
            pass

    def address(self):
        """
        The Architect's display name once given ("Matty"), else
        "".  Pure lookup — never creates records, never fails.
        """
        try:
            from ukft_people import PeopleModel
            rec = PeopleModel().who_is("architect")
            if rec is None:
                return ""
            name = (rec.get("display") or "").strip()
            if not name or name.lower() == "architect":
                return ""
            return name
        except Exception:
            return ""

    def _rendered(self, opener):
        """One pool template rendered with the name (or skipped)."""
        family, text = opener
        if "{name}" in text and not self._name:
            return None
        return text.format(name=self._name) if "{name}" in text else text

    def pick(self, family=None):
        """
        First pool opener outside the recent window.  Compared
        RENDERED (history holds "Yes, Matty —", not the "{name}"
        template) so named openers rotate instead of repeating.
        V7 F3: a requested affect family filters the pool; when the
        family is spent, the spill is the whole pool minus recent —
        variety never repeats a shape to serve a mood.
        """
        self._name = self.address()
        recent = set(self.history)
        if family:
            for opener in PROOF_OPENERS:
                if opener[0] != family:
                    continue
                rendered = self._rendered(opener)
                if rendered is None or rendered in recent:
                    continue
                return rendered
        for opener in PROOF_OPENERS:
            rendered = self._rendered(opener)
            if rendered is None:
                continue
            if rendered not in recent:
                return rendered
        # Unreachable while the pool outnumbers the window, but
        # never repeat the immediate last shape regardless.
        spill = []
        for opener in PROOF_OPENERS:
            if family and opener[0] != family:
                continue
            rendered = self._rendered(opener)
            if rendered is not None:
                spill.append(rendered)
        for rendered in spill:
            if rendered != (self.history[-1] if self.history else None):
                return rendered
        return spill[0] if spill else "Yes —"

    def record(self, opener):
        self.history.append(opener)
        self.history = self.history[-HISTORY_CAP:]
        self.last_opener = opener
        self._save()

    def style(self, body, kind=None, family=None, quiet=False):
        """
        Dress a memory-backed answer body.  F1 styles proof
        answers only; every other kind (and every ignorance,
        hedge, or conflict body) returns byte-identical.
        V7 F3: a requested affect family tints the opener pool;
        quiet says it short — first sentence, no opener.
        Honesty first: quiet never touches ignorance either.
        """
        if kind != "proof":
            return body
        if not body:
            return body
        prefix, rest = "", body
        if body.startswith(PREFIX):
            prefix, rest = PREFIX + " ", body[len(PREFIX):].lstrip()
        if not rest:
            return body
        for exact in LEAVE_EXACT:
            if rest.startswith(exact):
                return body
        if quiet:
            try:
                from ukft_quote import split_sentences
                parts = split_sentences(rest)
            except Exception:
                parts = [rest]
            first = parts[0] if parts else rest
            if first and first[-1] not in ".!?":
                first += "."
            return f"{prefix}{first}"
        opener = self.pick(family)
        self.record(opener)
        return f"{prefix}{opener} {rest}"
