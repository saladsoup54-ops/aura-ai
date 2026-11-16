# ukft_belief.py — AURA Belief & Trust (V6 C10)
# ==================================================
# Provenance, confidence and evidence for beliefs — and the
# deference policy as executable behaviour.  The knowledge
# graph holds what the vault proved; the belief store holds
# what the Architect ASSERTED, each with confidence, source,
# topic, and status.  An assertion that contradicts STRONG
# stored evidence is never silently absorbed: the conflict is
# surfaced and the change requires confirmation (gate C-G).
# Confirmed conflicts are held provisionally, with the
# dissent on record: "I think you are wrong.  I will go along
# for now.  Here is what would change my mind."
#
# Conflict classes mirror R3's own contradictions (kin
# inverses, has-vs-lacks, opposite comparators) over edges at
# or above STRONG_CONF.  is_a has no disjointness data, so a
# novel taxonomy is held, never contested — an honest limit,
# documented, not a silent gap.
# ==================================================

import re
import time

from aura_bus import read as bus_read, write as bus_write
from aura_constants import BELIEFS_FILE, PENDING_BELIEF

STRONG_CONF = 0.80       # "strong stored evidence" (gate C-G floor)
NOVEL_CONF = 0.60        # an uncontested assertion, held openly
CONFIRMED_CONF = 0.85    # the Architect doubled down explicitly
TRUST_START = 0.5
TRUST_MIN = 0.1
TRUST_MAX = 1.0

KIN_WORDS = {"son": "kin:son_of", "daughter": "kin:daughter_of",
             "father": "kin:father_of", "mother": "kin:mother_of",
             "parent": "kin:parent_of", "child": "kin:child_of",
             "ancestor": "kin:ancestor_of",
             "descendant": "kin:descendant_of",
             "wife": "kin:wife_of", "husband": "kin:husband_of",
             "brother": "kin:brother_of", "sister": "kin:sister_of"}

# Relation -> its inverse (symmetric pairs listed once).
INVERSES = {
    "kin:son_of": "kin:parent_of", "kin:daughter_of": "kin:parent_of",
    "kin:child_of": "kin:parent_of",
    "kin:father_of": "kin:child_of", "kin:mother_of": "kin:child_of",
    "kin:parent_of": "kin:child_of",
    "kin:ancestor_of": "kin:descendant_of",
    "kin:descendant_of": "kin:ancestor_of",
    "located_in": "contains", "contains": "located_in",
    "causes": "caused_by", "caused_by": "causes",
    "has_property:has": "has_property:lacks",
    "has_property:lacks": "has_property:has",
}

COMPARE_OPPOSITE = {
    "greater_than": "less_than", "less_than": "greater_than",
    "larger_than": "smaller_than", "smaller_than": "larger_than",
    "heavier_than": "lighter_than", "lighter_than": "heavier_than",
    "faster_than": "slower_than", "slower_than": "faster_than",
}

# Subjects that are grammar, not claims ("what is an apple"
# asks; it does not assert).
WH_SUBJECTS = {"what", "who", "where", "when", "why", "how",
               "which", "that", "this", "it", "there"}

COMPARE_WORDS = ("greater", "less", "larger", "smaller", "heavier",
                 "lighter", "faster", "slower")


def _clean(s):
    return " ".join(str(s or "").strip().strip("?.!").split())


def detect_assertion(text):
    """
    A subject-first declarative claim -> {"rel","x","y"} or None.
    Questions (trailing "?"), wh-subjects, and greeting wrapping
    never assert — asking is not telling.
    """
    t = " ".join(str(text).strip().split())
    if not t or t.endswith("?"):
        return None
    q = re.sub(r"^(good morning|good evening|good afternoon|"
               r"greetings|hello|hey|hi)\b[,. ]*", "", t.lower()).strip()
    if not q:
        return None

    def out(rel, x, y):
        x, y = _clean(x), _clean(y)
        if not x or not y or x in WH_SUBJECTS:
            return None
        return {"rel": rel, "x": x, "y": y}

    m = re.match(r"^(.+?) is the (" + "|".join(KIN_WORDS) + r")"
                 r" of (.+)$", q)
    if m:
        return out(KIN_WORDS[m.group(2)], m.group(1), m.group(3))
    m = re.match(r"^(.+?) is (?:a|an) (.+)$", q)
    if m:
        return out("is_a", m.group(1), m.group(2))
    m = re.match(r"^(.+?) is located in (.+)$", q)
    if m:
        return out("located_in", m.group(1), m.group(2))
    m = re.match(r"^(.+?) is part of (.+)$", q)
    if m:
        return out("part_of", m.group(1), m.group(2))
    m = re.match(r"^(.+?) is (" + "|".join(COMPARE_WORDS) +
                 r") than (.+)$", q)
    if m:
        op = {"greater": "greater_than", "less": "less_than",
              "larger": "larger_than", "smaller": "smaller_than",
              "heavier": "heavier_than", "lighter": "lighter_than",
              "faster": "faster_than", "slower": "slower_than"}[m.group(2)]
        return out("compare:" + op, m.group(1), m.group(3))
    m = re.match(r"^(.+?) (has|lacks) (.+)$", q)
    if m:
        return out("has_property:has" if m.group(2) == "has"
                   else "has_property:lacks", m.group(1), m.group(3))
    return None


def _kin_parent(rel, a, b):
    """Who the edge names as the parent-side party (None if neither)."""
    if rel in ("kin:father_of", "kin:mother_of", "kin:parent_of",
               "kin:ancestor_of"):
        return a
    if rel in ("kin:son_of", "kin:daughter_of", "kin:child_of",
               "kin:descendant_of"):
        return b
    return None


def _kin_spouse(rel, a, b):
    """
    Spouses normalized to (wife, husband) — wife_of(a, b) and
    husband_of(b, a) agree; anything else on the pair conflicts.
    """
    if rel == "kin:wife_of":
        return (a, b)
    if rel == "kin:husband_of":
        return (b, a)
    return None


def _kin_conflict(rel, x, y, er, a, b):
    """
    Same-pair kin disagreement: different implied parents, swapped
    spouses, or one party cast as both brother and sister.
    Consistent inverses (father/son across the pair) agree.
    """
    pa, pb = _kin_parent(rel, x, y), _kin_parent(er, a, b)
    if pa is not None and pb is not None:
        return pa != pb
    sa, sb = _kin_spouse(rel, x, y), _kin_spouse(er, a, b)
    if sa is not None and sb is not None:
        return sa != sb
    if {rel, er} <= {"kin:brother_of", "kin:sister_of"}:
        return (a, b) == (x, y) and rel != er
    return False


def find_conflict(rel, x, y, edges):
    """
    edges: {(rel, x, y): (conf, origin)}.  Returns the strongest
    conflicting edge (rel, a, b, conf, origin) at/above
    STRONG_CONF, or None.  Restatements and consistent inverse
    pairs (father_of(david,solomon) vs son_of(solomon,david))
    are agreement, never conflict.
    """
    best = None
    inv = INVERSES.get(rel)
    for (er, a, b), (conf, origin) in edges.items():
        if conf < STRONG_CONF:
            continue
        hit = False
        if rel.startswith("kin:") and er.startswith("kin:"):
            # Same pair, disagreed kinship = contradiction (parents,
            # spouses, siblings each in their own geometry).
            if {a, b} == {x, y}:
                hit = _kin_conflict(rel, x, y, er, a, b)
        elif er == rel and (a, b) == (x, y):
            continue
        elif er == rel and (a, b) == (y, x):
            if rel not in ("is_a", "part_of"):
                hit = True
        elif inv is not None and er == inv and {a, b} == {x, y}:
            hit = True
        elif rel.startswith("compare:") and er.startswith("compare:"):
            op, eop = rel[len("compare:"):], er[len("compare:"):]
            if ({a, b} == {x, y}
                    and (eop == COMPARE_OPPOSITE.get(op)
                         or (eop == op and (a, b) == (y, x)))):
                hit = True
        if hit and (best is None or conf > best[3]):
            best = (er, a, b, conf, origin)
    return best


def _parse_beliefs(text):
    """Parse-tolerant reader: bad lines are skipped, never fatal."""
    beliefs, trust = {}, {}
    for line in text.splitlines():
        try:
            if line.startswith("BELIEF: "):
                segs = line[len("BELIEF: "):].split(" | ")
                head = segs[0].strip().split(" >> ")
                if len(head) != 3:
                    continue
                rel, x, y = (h.strip() for h in head)
                fields = {}
                for p in segs[1:]:
                    if ": " in p:
                        k, v = p.split(": ", 1)
                        fields[k] = v
                beliefs[(rel, x, y)] = {
                    "conf": float(fields.get("CONF", "0") or 0),
                    "src": fields.get("SRC", "?"),
                    "topic": fields.get("TOPIC", rel),
                    "status": fields.get("STATUS", "held"),
                    "ts": float(fields.get("TS", "0") or 0),
                    "prior": fields.get("PRIOR", ""),
                }
            elif line.startswith("TRUST: "):
                segs = line[len("TRUST: "):].split(" | ")
                head = segs[0].strip().split(" >> ")
                if len(head) != 2:
                    continue
                fields = {}
                for p in segs[1:]:
                    if ": " in p:
                        k, v = p.split(": ", 1)
                        fields[k] = v
                trust[(head[0].strip(), head[1].strip())] = {
                    "score": float(fields.get("SCORE", "0.5") or 0.5),
                    "n": int(float(fields.get("N", "0") or 0)),
                }
        except (ValueError, AttributeError):
            continue
    return beliefs, trust


class BeliefStore:
    """Architect-held claims with provenance, plus earned trust."""

    def __init__(self, path=BELIEFS_FILE, pending_path=PENDING_BELIEF,
                 clock=time.time, persist=True):
        self.path = path
        self.pending_path = pending_path
        self._clock = clock
        # Finding #4: persist=False proposes in memory only (see
        # PeopleModel — same contract, same default-True safety).
        self._persist = persist
        self.beliefs = {}
        self.trust = {}
        self.load()

    def now(self):
        return self._clock()

    def load(self):
        try:
            text = bus_read(self.path)
        except Exception:
            text = ""
        self.beliefs, self.trust = _parse_beliefs(text)

    def save(self):
        if not self._persist:
            return
        lines = [f"--- AURA BELIEFS (v1) | N: {len(self.beliefs)} ---"]
        for (rel, x, y) in sorted(self.beliefs):
            b = self.beliefs[(rel, x, y)]
            lines.append(
                f"BELIEF: {rel} >> {x} >> {y} | CONF: {b['conf']:.2f} | "
                f"SRC: {b['src']} | TOPIC: {b['topic']} | "
                f"STATUS: {b['status']} | TS: {int(b['ts'])} | "
                f"PRIOR: {b['prior']}")
        for (src, topic) in sorted(self.trust):
            t = self.trust[(src, topic)]
            lines.append(
                f"TRUST: {src} >> {topic} | SCORE: {t['score']:.2f} | "
                f"N: {t['n']}")
        bus_write(self.path, "\n".join(lines) + "\n")

    def trust_of(self, source, topic):
        """Earned reliability, 0.1..1.0 — the unknown start at 0.5."""
        t = self.trust.get((source, topic))
        return t["score"] if t else TRUST_START

    def _move_trust(self, source, topic, delta):
        t = self.trust.get((source, topic),
                           {"score": TRUST_START, "n": 0})
        t["score"] = max(TRUST_MIN, min(TRUST_MAX, t["score"] + delta))
        t["n"] += 1
        self.trust[(source, topic)] = t

    def match(self, x, y, relation=None):
        """A held claim about (x, y) — relation-preferred, else any."""
        x = " ".join(str(x or "").lower().split())
        y = " ".join(str(y or "").lower().split())
        cands = [(k, b) for k, b in self.beliefs.items()
                 if k[1] == x and k[2] == y]
        if not cands:
            return None
        if relation:
            for k, b in cands:
                if k[0] == relation:
                    return dict(b, rel=k[0], x=k[1], y=k[2])
        k, b = sorted(cands, key=lambda kv: -kv[1]["conf"])[0]
        return dict(b, rel=k[0], x=k[1], y=k[2])

    def match_words(self, words):
        """
        A held claim whose subject and every object word appear in
        `words` — for VERIFY plans whose entities never resolved.
        Strongest confidence wins ties of coverage.
        """
        vocab = {str(w).lower() for w in (words or [])}
        best, score = None, (0, -1.0)
        for (rel, x, y), b in self.beliefs.items():
            if x not in vocab:
                continue
            ywords = y.split()
            if not ywords or not all(w in vocab for w in ywords):
                continue
            key = (len(ywords), b["conf"])
            if best is None or key > score:
                best, score = (rel, x, y, b), key
        if best is None:
            return None
        rel, x, y, b = best
        return dict(b, rel=rel, x=x, y=y)

    def hold(self, rel, x, y, conf=NOVEL_CONF, src="architect",
             status="held", prior="", now=None):
        """Record a claim.  Confirmation, not silent absorption."""
        now = self.now() if now is None else now
        self.beliefs[(rel, x, y)] = {
            "conf": conf, "src": src, "topic": rel, "status": status,
            "ts": now, "prior": prior[:120],
        }
        self.save()
        return self.beliefs[(rel, x, y)]

    def confirm_contest(self, staged, now=None):
        """
        The Architect doubled down over strong evidence: hold it
        as CONTESTED (dissent on record), trust moves accordingly.
        """
        now = self.now() if now is None else now
        rec = self.hold(staged["rel"], staged["x"], staged["y"],
                        conf=CONFIRMED_CONF, status="contested",
                        prior=staged.get("prior", ""), now=now)
        self._move_trust("architect", staged["rel"], +0.10)
        self._move_trust("graph", staged["rel"], -0.05)
        self.save()
        self.clear_pending()
        return rec

    def cancel_contest(self, staged):
        """Evidence stands: graph trust earned, Architect barely dented."""
        self._move_trust("graph", staged["rel"], +0.10)
        self._move_trust("architect", staged["rel"], -0.05)
        self.save()
        self.clear_pending()

    # ── PENDING CONTESTS ─────────────────────────────────────
    def stage(self, rel, x, y, prior="", now=None):
        """
        Park one contradiction for confirm/cancel.  Returns False
        (keeping the old park) when a slot is already waiting.
        """
        now = self.now() if now is None else now
        if self.pending():
            return False
        if not self._persist:
            # Proposal only: same True contract, no disk trace.
            return True
        bus_write(self.pending_path,
                  f"CLAIM: {rel} >> {x} >> {y} | TS: {int(now)} | "
                  f"PRIOR: {prior[:120]}\n")
        return True

    def pending(self):
        """The staged contest, or None."""
        try:
            line = bus_read(self.pending_path).strip()
        except Exception:
            return None
        if not line.startswith("CLAIM: "):
            return None
        try:
            segs = line[len("CLAIM: "):].split(" | ")
            head = segs[0].strip().split(" >> ")
            if len(head) != 3:
                return None
            fields = {}
            for p in segs[1:]:
                if ": " in p:
                    k, v = p.split(": ", 1)
                    fields[k] = v
            return {"rel": head[0].strip(), "x": head[1].strip(),
                    "y": head[2].strip(),
                    "ts": float(fields.get("TS", "0") or 0),
                    "prior": fields.get("PRIOR", "")}
        except (ValueError, AttributeError):
            return None

    def clear_pending(self):
        if not self._persist:
            return
        bus_write(self.pending_path, "")


def claim_text(rel, x, y):
    """A held claim in plain words (R5's relation semantics)."""
    try:
        from ukft_answer import _claim
        return _claim(rel, x, y)
    except Exception:
        return f"{x} relates to {y}"
