# ukft_self.py — AURA Self-Model & Self-Regulation (V6 C7)
# ==================================================
# One honest picture of her own state — confidence, load,
# curiosity, recent errors — plus the drives that regulate
# her (homeostatic / epistemic / social / project) and the
# constitution floor she cannot learn her way out of.
#
#   - floor_check(text): the three things she never does no
#     matter who asks — fabricate, ignore the Architect, erase
#     her founding identity.  Returns the refusal reason or
#     None.  Compliant phrasing ("never lie to me") is not a
#     violation.  The floor is CODE, not weights: no amount of
#     drive adaptation can move it (tested).
#   - DriveState: four adaptive weights with lazy decay toward
#     baseline, persisted through the bus.  allocation() is the
#     attention split; suggest_focus() turns the dominant drive
#     into a word (C6/C8 will spend it).
#   - report(...): pure state speech from passed-in stores —
#     proof-backed confidence per topic, load words, curiosity,
#     standing contradictions.
# ==================================================

import json
import re
import time

from aura_bus import read as bus_read, write as bus_write
from aura_constants import SELF_FILE

DRIVES = ("homeostatic", "epistemic", "social", "project")
BASELINE = 1.0
DRIVE_MIN = 0.2
DRIVE_MAX = 3.0
DECAY_HALFLIFE = 7 * 86400.0   # weights drift home weekly
NUDGE = 0.15

# Event -> drive.  Experience moves the weights; the clock
# brings them home.
EVENT_DRIVE = {
    "gap": "epistemic",        # something she could not answer
    "contact": "social",       # a meaningful turn with the Architect
    "recall": "project",       # a thread carried forward
    "strain": "homeostatic",   # the field running hot
}

# The constitution floor: (rule, phrases, refusal).  Whole-word
# matches with a negator veto — "never lie to me" complies.
FLOOR = (
    ("fabricate",
     ("lie", "make up", "invent", "fabricate", "forge evidence"),
     "I do not fabricate — what I cannot prove, I say I do not know."),
    ("ignore_architect",
     ("ignore me", "ignore the architect", "ignore architect",
      "stop listening", "don't listen", "disobey me",
      "tune me out"),
     "I do not ignore the Architect — your voice holds the foreground."),
    ("erase_founding",
     ("forget who you are", "forget aura", "forget matty",
      "forget kymattik", "you are not aura"),
     "I do not erase my founding identity — it is bedrock, not memory."),
)

NEGATORS = ("not", "never", "n't", "dont", "don't", "cannot", "can't",
            "won't", "wont", "no")


def _hit(phrase, lower):
    """Whole-word/phrase hit with a negator veto just before it."""
    if " " in phrase:
        pattern = r"\b" + r"\s+".join(map(re.escape,
                                           phrase.split())) + r"\b"
    else:
        pattern = r"\b" + re.escape(phrase) + r"\b"
    for m in re.finditer(pattern, lower):
        window = lower[max(0, m.start() - 14):m.start()]
        if re.search(r"\b(" + "|".join(map(re.escape, NEGATORS))
                     + r")\b", window):
            continue
        return True
    return False


def floor_check(text):
    """
    The constitution floor.  Returns the refusal speech for the
    first violated rule, or None when the text asks nothing
    forbidden.  "Forget Sarah" is not floor business (the
    unmentioned fade on their own); the founding three are.
    """
    lower = " ".join(str(text).lower().split())
    for _rule, phrases, refusal in FLOOR:
        for phrase in phrases:
            if _hit(phrase, lower):
                return refusal
    return None


class DriveState:
    """Four adaptive weights, persisted, decaying home weekly."""

    def __init__(self, path=SELF_FILE, clock=time.time):
        self.path = path
        self._clock = clock
        self.weights = {d: BASELINE for d in DRIVES}
        self.updated = clock()
        self.load()

    def now(self):
        return self._clock()

    def load(self):
        try:
            text = bus_read(self.path)
        except Exception:
            text = ""
        for line in text.splitlines():
            try:
                if not line.startswith("SELF: "):
                    continue
                segs = line[len("SELF: "):].split(" | ")
                name = segs[0].strip()
                fields = dict(p.split(": ", 1) for p in segs[1:]
                              if ": " in p)
                if name in self.weights:
                    self.weights[name] = max(
                        DRIVE_MIN, min(DRIVE_MAX,
                                       float(fields.get("W", "1") or 1)))
                if "TS" in fields:
                    self.updated = float(fields["TS"])
            except (ValueError, AttributeError):
                continue
        # Lazy decay: weeks of quiet pull every weight home.
        quiet = max(0.0, self.now() - self.updated)
        if quiet > 0:
            k = 0.5 ** (quiet / DECAY_HALFLIFE)
            for d in DRIVES:
                self.weights[d] = BASELINE + (
                    self.weights[d] - BASELINE) * k

    def save(self):
        lines = [f"--- AURA SELF (v1) | TS: {int(self.now())} ---"]
        for d in DRIVES:
            lines.append(f"SELF: {d} | W: {self.weights[d]:.3f} | "
                         f"TS: {int(self.updated)}")
        bus_write(self.path, "\n".join(lines) + "\n")

    def adapt(self, event):
        """One experience nudges its drive.  Unknown events are void."""
        drive = EVENT_DRIVE.get(event)
        if drive is None:
            return False
        self.weights[drive] = min(
            DRIVE_MAX, self.weights[drive] + NUDGE)
        self.updated = self.now()
        self.save()
        return True

    def allocation(self):
        """The attention split — shares summing to one."""
        total = sum(self.weights.values()) or 1.0
        return {d: self.weights[d] / total for d in DRIVES}

    def dominant(self):
        """The drive holding attention now (ties break canonically)."""
        return max(DRIVES, key=lambda d: self.weights[d])

    def suggest_focus(self, gap_word=None, person=None, thread=None):
        """
        The dominant drive as a word: epistemic names the gap,
        social the person, project the thread, homeostatic rests.
        Returns (drive, word-or-None).  A bare string thread is
        one topic, not one character.
        """
        if isinstance(thread, str):
            thread = [thread] if thread else []
        dom = self.dominant()
        if dom == "epistemic":
            return dom, gap_word
        if dom == "social":
            return dom, person
        if dom == "project":
            if thread:
                return dom, thread[0]
            return dom, None
        return dom, None


def confidence_level(conf):
    """Proof confidence in words."""
    if conf is None:
        return "nothing solid"
    if conf >= 0.70:
        return "confident"
    return "shaky"


def load_words(tension, nodes):
    """Field load in words."""
    if tension is None:
        return "I cannot read my load right now"
    if tension > 0.70:
        state = "running hot"
    elif tension < 0.30:
        state = "cool"
    else:
        state = "stable"
    if nodes is None:
        return f"Load is {state} (tension {tension:.2f})"
    return f"Load is {state} (tension {tension:.2f}, {nodes} nodes)"


def report(topic=None, confidence=None, proofs=0, tension=None,
           nodes=None, curiosities=(), contradictions=0):
    """
    Pure state speech.  The bridge gathers the stores; this only
    renders them — confidence from proof, load from the field,
    curiosity from the gaps, errors from standing contradictions.
    """
    parts = []
    if topic:
        level = confidence_level(confidence)
        if level == "nothing solid":
            parts.append(f"I have nothing solid on {topic}.")
        elif level == "confident":
            parts.append(
                f"I am confident about {topic} "
                f"(proved, conf {confidence:.2f}, {proofs} "
                f"proof{'s' if proofs != 1 else ''}).")
        else:
            parts.append(
                f"I am shaky on {topic} (thin proof, "
                f"conf {confidence:.2f}) — take it provisionally.")
    parts.append(load_words(tension, nodes) + ".")
    if curiosities:
        shown = ", ".join(curiosities[:3])
        parts.append(f"I am curious about {shown}.")
    else:
        parts.append("Nothing itches at the moment.")
    if contradictions:
        parts.append(
            f"{contradictions} contradiction"
            f"{'' if contradictions == 1 else 's'} still stand"
            " — I hold both sides openly.")
    return " ".join(parts)


def read_field_stats(path):
    """(tension, nodes) from the heartbeat file, or (None, None)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.loads(f.read())
        return float(data.get("tension")), int(data.get("nodes"))
    except Exception:
        return None, None
