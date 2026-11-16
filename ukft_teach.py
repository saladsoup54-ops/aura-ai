# ukft_teach.py — AURA Self-Teaching (V6 C8)
# ==================================================
# The predict-and-correct loop: she guesses, reality answers,
# the gap is the lesson.  Three teacher signals, each with
# provenance, each verified before anything is learned:
#
#   - Architect corrections ("no", "wrong", "actually X is Y"):
#     bare corrections ask for the lesson; counter-claims route
#     through the belief machinery (strong evidence contests,
#     the rest is held openly) and person facts learn in
#     passing.  Nothing is silently overwritten, ever.
#   - Tool/world outcomes (action_log CANCELLED / REFUSED /
#     DROPPED): declined or refused actions are feedback about
#     what was wanted — banked as lessons on review.
#   - Reflection ("what have you learned"): the ledger rendered
#     back — counts by teacher plus the latest lessons.
#
# Lessons live in lessons.txt, capped, deduplicated, each with
# teacher + topic: she can never learn nonsense because every
# lesson says who taught it and what it cost.
# ==================================================

import re
import time

from aura_bus import read as bus_read, write as bus_write
from aura_constants import LESSONS_FILE

MAX_LESSONS = 200

BARE_CORRECTIONS = (
    "no", "nope", "wrong", "incorrect", "not right",
    "that's not right", "not quite", "not exactly",
)

COUNTER_RES = (
    r"^(?:no|nope|wrong)[,. ]+(.+)$",
    r"^actually[,. ]+(.+)$",
    r"^i meant[,. ]+(.+)$",
    r"^that'?s (?:wrong|not right)[,. ]+(.+)$",
    r"^you'?re wrong[,. ]+(.+)$",
)

REVIEW_RES = (
    r"what have you learned",
    r"^reflect\b",
    r"^lessons\b",
    r"show me my lessons",
)

TOOL_LESSON_OUTCOMES = ("CANCELLED", "DROPPED")


def detect_correction(text):
    """
    ("bare", None) / ("counter", claim-text) / None.  A bare
    "no" asks for the lesson; a counter carries it.
    """
    t = " ".join(str(text).strip().split())
    low = t.lower().strip("?!.")
    if low in BARE_CORRECTIONS:
        return ("bare", None)
    for rx in COUNTER_RES:
        m = re.match(rx, t, re.IGNORECASE)
        if m and m.group(1).strip(" ,"):
            return ("counter",
                    " ".join(m.group(1).strip(" ,").split()))
    return None


def is_review_request(text):
    """'What have you learned' and its siblings."""
    t = " ".join(str(text).lower().split())
    return any(re.search(rx, t) for rx in REVIEW_RES)


def _parse_lessons(text):
    """Parse-tolerant reader: bad lines are skipped, never fatal."""
    lessons = []
    for line in text.splitlines():
        try:
            if not line.startswith("LESSON: "):
                continue
            segs = line[len("LESSON: "):].split(" | ")
            ts = float(segs[0].strip())
            fields = {}
            for p in segs[1:]:
                if ": " in p:
                    k, v = p.split(": ", 1)
                    fields[k] = v
            if not fields.get("LESSON", "").strip():
                continue
            lessons.append({
                "ts": ts,
                "teacher": fields.get("TEACHER", "?"),
                "topic": fields.get("TOPIC", ""),
                "lesson": fields.get("LESSON", ""),
            })
        except (ValueError, AttributeError, IndexError):
            continue
    return lessons


class LessonLedger:
    """Banked lessons with provenance.  Duplicates never re-bank."""

    def __init__(self, path=LESSONS_FILE, clock=time.time,
                 persist=True):
        self.path = path
        self._clock = clock
        # Finding #4: persist=False proposes in memory only (see
        # PeopleModel — same contract, same default-True safety).
        self._persist = persist
        self.lessons = []
        self.load()

    def now(self):
        return self._clock()

    def load(self):
        try:
            text = bus_read(self.path)
        except Exception:
            text = ""
        self.lessons = _parse_lessons(text)

    def save(self):
        if not self._persist:
            return
        lines = [f"--- AURA LESSONS (v1) | N: {len(self.lessons)} ---"]
        for e in self.lessons:
            lines.append(
                f"LESSON: {int(e['ts'])} | TEACHER: {e['teacher']} | "
                f"TOPIC: {e['topic'][:60]} | LESSON: {e['lesson'][:160]}")
        bus_write(self.path, "\n".join(lines) + "\n")

    def record(self, teacher, topic, lesson, now=None):
        """Bank one lesson.  False when empty or already banked."""
        now = self.now() if now is None else now
        topic = " ".join(str(topic or "").split())[:60]
        lesson = " ".join(str(lesson or "").split())[:160]
        if not lesson:
            return False
        for e in self.lessons:
            if (e["teacher"], e["topic"], e["lesson"]) == \
                    (teacher, topic, lesson):
                return False
        self.lessons.append({"ts": now, "teacher": teacher,
                             "topic": topic, "lesson": lesson})
        del self.lessons[:-MAX_LESSONS]
        self.save()
        return True

    def recent(self, n=5):
        return self.lessons[-n:] if n > 0 else []

    def count_by_teacher(self):
        counts = {}
        for e in self.lessons:
            counts[e["teacher"]] = counts.get(e["teacher"], 0) + 1
        return counts


def review_tools(action_log_text, ledger):
    """
    Bank lessons for declined/refused tool outcomes.  Returns the
    number of new lessons — idempotent via ledger dedupe, so
    re-reviews are free.
    """
    banked = 0
    for line in str(action_log_text or "").splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 4:
            continue
        _ts, tool, _arg, outcome = parts[0], parts[1], parts[2], parts[3]
        upper = outcome.upper()
        if any(k in upper for k in TOOL_LESSON_OUTCOMES) or \
                upper.startswith("REFUSED"):
            if ledger.record("tool", tool,
                             f"{tool} — {outcome.lower()}"):
                banked += 1
    return banked


def render_review(ledger, n=3):
    """The ledger rendered back: counts plus the latest lessons."""
    total = len(ledger.lessons)
    if not total:
        return ("Nothing banked yet — correct me when I'm wrong and "
                "I'll keep the lesson.")
    counts = ledger.count_by_teacher()
    bits = "; ".join(f"{c} from {t}" for t, c in sorted(counts.items()))
    latest = " / ".join(
        f"{e['topic']}: {e['lesson']}" if e["topic"]
        else e["lesson"] for e in ledger.recent(n))
    return (f"I've banked {total} lesson{'s' if total != 1 else ''} "
            f"({bits}). Latest: {latest}.")
