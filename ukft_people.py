# ukft_people.py — AURA People Model (V6 C2)
# ==================================================
# A self-updating social memory: after one introduction she
# knows the person forever.  One record per person — name and
# aliases, relationship history (girlfriend -> fiancee -> wife
# keeps the old ones), first met / last seen, mention count,
# learned facts with provenance, and an importance that decays
# when unmentioned but never deletes.
#
#   - extract_introduction(text): high-confidence introductions
#     ("this is my fiancee, Sarah") commit; uncertain ones
#     (lowercase name, unknown relation word) stage for a
#     confirm/cancel round — unsure is asked, never assumed.
#   - PeopleModel(path, pending_path, clock): commit / stage /
#     confirm / cancel, note_mention, learn_fact, who_is,
#     describe.  Whole-file bus IO, parse-tolerant, lazy decay.
# ==================================================

import re
import time

from aura_bus import read as bus_read, write as bus_write
from aura_constants import PEOPLE_FILE, PENDING_PEOPLE

DECAY_HALFLIFE = 30 * 86400.0   # importance halves per quiet month
IMPORTANCE_FLOOR = 0.2          # the unmentioned fade, never vanish
IMPORTANCE_CAP = 2.0
MAX_FACTS = 20

ARCHITECT_KEY = "architect"     # V6 C3: the Architect is a person too —
                                # a first-class record, not a special case
ARCHITECT_DISPLAY = "Matty"     # the name this project knows them by;
                                # "call me X" can add to it, never erase
INTERLOCUTOR_KEY = "interlocutor"
UNKNOWN_DISPLAY = "the current user"

RELATIONS = {
    "fiancee", "fiance", "girlfriend", "boyfriend", "wife",
    "husband", "partner", "best friend", "friend", "brother",
    "sister", "mother", "father", "mom", "mum", "dad", "son",
    "daughter", "colleague", "boss", "neighbor", "neighbour",
}

REL_NORMALIZE = {
    "fiance": "fiancee", "mum": "mother", "mom": "mother",
    "dad": "father", "neighbour": "neighbor",
}

NAME_RE = r"[A-Z][a-z]+(?: [A-Z][a-z]+)?"
REL_RE = ("fiancee|fiance|girlfriend|boyfriend|wife|husband|partner|"
          "best friend|friend|brother|sister|mother|father|mom|mum|"
          "dad|son|daughter|colleague|boss|neighbor|neighbour")

# Words that can never be a staged name ("meet my friend the
# manager" stages nothing — precision over recall).
NAME_BAN = {
    "the", "a", "an", "my", "your", "our", "his", "her", "their",
    "this", "that", "very", "real", "good", "old", "new", "manager",
    "opinion", "point", "favour", "favor",
}

# G1 fix (16 Sept 2026): sentence-initial question words once parsed
# as names ("What is my sister's name?" committed a person named
# "What").  A captured name from this set is never a person.
WH_WORDS = {
    "what", "who", "whom", "whose", "which", "where", "when",
    "why", "how", "is", "are", "was", "were", "do", "does",
    "did", "can", "could", "will", "would", "tell",
}


def _good_name(n):
    """True when the captured string may be a person's name."""
    parts = (n or "").lower().split()
    return bool(parts) and not any(w in WH_WORDS for w in parts)


# Temporal/adverbial "call me X" is not naming ("call me later"
# means call me at a later time — c3 contract).
CALLME_BAN = {
    "later", "soon", "today", "tonight", "tomorrow", "back",
    "again", "please", "maybe", "sometime",
}

FACT_VERBS = ("likes", "loves", "works as", "lives in", "is a", "is an")


def _stem_attr_word(word):
    """Narrow plural/3rd-person stem for attribute matching: "likes" ->
    "like", "lives" -> "live". Only a trailing single 's' is stripped,
    so "address"/"glass" keep theirs and "like" never equals "live"."""
    w = str(word or "").lower()
    if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def second_person(fact):
    """
    Facts store third-person ("likes X"); speech TO the Architect
    is second-person ("you like X").  Single source — the bridge
    and describe_architect share it (audit: one grammar, one place).
    """
    swaps = (
        (r"^likes\b", "like"), (r"^loves\b", "love"),
        (r"^prefers\b", "prefer"), (r"^works as\b", "work as"),
        (r"^lives in\b", "live in"), (r"^is an\b", "are an"),
        (r"^is a\b", "are a"), (r"^calls\b", "call"),
        (r"^reads\b", "read"), (r"^has\b", "have"),
    )
    out = str(fact or "")
    for pattern, replacement in swaps:
        changed = re.sub(pattern, replacement, out, count=1,
                         flags=re.IGNORECASE)
        if changed != out:
            return changed
    return out


def first_person(fact):
    """Canonical third-person predicate rendered as Aura's own fact."""
    out = second_person(fact)
    return re.sub(r"^are\b", "am", out, count=1, flags=re.IGNORECASE)


def render_fact(fact, perspective, display=""):
    """Render a person fact from a structurally selected perspective."""
    fact = " ".join(str(fact or "").split())
    if not fact:
        return ""
    if fact.startswith("project: "):
        value = fact[len("project: "):]
        if perspective == "current":
            return "your project is " + value
        if perspective == "self":
            return "my project is " + value
    if fact.startswith("note: "):
        value = fact[len("note: "):]
        if perspective == "current":
            return "your note says " + value
        if perspective == "self":
            return "my note says " + value
    if perspective == "current":
        return "you " + second_person(fact)
    if perspective == "self":
        return "I " + first_person(fact)
    return ((display + " ") if display else "") + fact


def learn_architect(text):
    """
    V6 C3: statements ABOUT the Architect ("my project is X",
    "I like Y", "remember that Z", "call me W") become facts or
    aliases on the architect record.  Returns ("fact", fact) /
    ("alias", name) / None.  Ordinary chat matches nothing.
    """
    t = " ".join(text.strip().split())
    m = re.search(r"\bmy project is ([^.?!]{1,60})", t, re.IGNORECASE)
    if m and m.group(1).strip():
        return ("fact", "project: " + m.group(1).strip(" ,"))
    m = re.search(r"\bi(?:'m| am) working on ([^.?!]{1,60})", t,
                  re.IGNORECASE)
    if m and m.group(1).strip():
        return ("fact", "project: " + m.group(1).strip(" ,"))
    m = re.search(r"\bi work on ([^.?!]{1,60})", t, re.IGNORECASE)
    if m and m.group(1).strip():
        return ("fact", "project: " + m.group(1).strip(" ,"))
    m = re.search(r"\bi (like|love|prefer) ([^.?!]{1,60})", t,
                  re.IGNORECASE)
    if m and m.group(2).strip():
        verb = {"like": "likes", "love": "loves",
                "prefer": "prefers"}[m.group(1).lower()]
        return ("fact", verb + " " + m.group(2).strip(" ,"))
    m = re.search(r"\b(?:remember|note) that ([^.?!]{1,120})", t,
                  re.IGNORECASE)
    if m and m.group(1).strip():
        return ("fact", "note: " + m.group(1).strip(" ,"))
    m = re.search(r"\bcall me ([A-Za-z]+)\b", t, re.IGNORECASE)
    if m and _good_name(m.group(1)) \
            and m.group(1).lower() not in CALLME_BAN:
        # Title-cased on commit: "call me matty" and "call me
        # Matty" are the same instruction (missed live 17 Sept
        # 2026 — lowercase fell through to "no vault resonance").
        return ("alias", m.group(1).strip().title())
    # What HE calls HER ("call you babe" — live 17 Sept 2026 went
    # to a status audit on "going" and learned nothing). Stored as
    # a fact so it persists; her own usage stays depth-gated.
    m = re.search(r"\bcall you ([A-Za-z]+)\b", t, re.IGNORECASE)
    if m and _good_name(m.group(1)) \
            and m.group(1).lower() not in CALLME_BAN:
        return ("fact", "calls me " + m.group(1).strip().title())
    return None


def learn_current_user(text):
    """Facts and names stated by whichever person is speaking now."""
    t = " ".join(str(text or "").strip().split())
    m = re.search(r"\bmy name is ([A-Za-z][A-Za-z'’-]*(?:\s+"
                  r"[A-Za-z][A-Za-z'’-]*)?)", t, re.IGNORECASE)
    if m:
        name = m.group(1).strip()
        name = re.split(r"\s+(?:and|but)\b", name,
                        maxsplit=1, flags=re.IGNORECASE)[0]
        if _good_name(name) and not any(
                w.lower() in NAME_BAN for w in name.split()):
            return ("display", name.title())
    return learn_architect(t)


def normalize_person_question(text):
    """Normalize common spoken contractions before person routing."""
    out = " ".join(str(text or "").strip().lower().split())
    out = re.sub(r"^who(?:'s|s)\b", "who is", out)
    out = re.sub(r"^what(?:'s|s)\b", "what is", out)
    return out


def architect_summary(rec, n_people, now=None):
    """
    One briefing line for the Architect, or "" while she still
    knows nothing worth announcing.
    """
    nf = len(rec["facts"])
    if not nf and rec["mentions"] < 3:
        return ""
    now = time.time() if now is None else now
    days = max(1, int((now - rec["first_met"]) / 86400.0))
    bits = [f"{nf} note" + ("" if nf == 1 else "s")]
    if n_people:
        bits.append(f"{n_people} person" + ("" if n_people == 1
                                            else "s") + " known")
    bits.append(f"{days} day" + ("" if days == 1 else "s") + " together")
    return f"{rec['display']} — " + ", ".join(bits)


def _norm_rel(rel):
    rel = " ".join(rel.lower().split())
    return REL_NORMALIZE.get(rel, rel)


def extract_introduction(text):
    """
    Returns {"name", "relation", "confidence"} ("high"/"low") or
    None.  High commits; low stages for confirm/cancel.

    G1 fix: questions are never introductions (a "?"-terminated
    input returns None — WH-questions route to who_is/recall/
    honest-ignorance instead of committing "What" as a person),
    and captured question-words are never names.
    """
    if " ".join(text.strip().split()).endswith("?"):
        return None
    m = re.search(r"\b[Tt]his is my (" + REL_RE + r"),?\s+("
                   + NAME_RE + r")\b", text)
    if m and _good_name(m.group(2)):
        return {"name": m.group(2), "relation": _norm_rel(m.group(1)),
                "confidence": "high"}
    m = re.search(r"\b[Mm]eet my (" + REL_RE + r") (" + NAME_RE
                   + r")\b", text)
    if m and _good_name(m.group(2)):
        return {"name": m.group(2), "relation": _norm_rel(m.group(1)),
                "confidence": "high"}
    m = re.search(r"\b(" + NAME_RE + r") is my (" + REL_RE + r")\b",
                   text)
    if m and _good_name(m.group(1)):
        return {"name": m.group(1), "relation": _norm_rel(m.group(2)),
                "confidence": "high"}
    m = re.search(r"\b[Mm]y (" + REL_RE + r") (" + NAME_RE + r")\s+"
                   r"(is|has|works|lives|likes|loves|was)\b", text)
    if m and _good_name(m.group(2)):
        return {"name": m.group(2), "relation": _norm_rel(m.group(1)),
                "confidence": "high"}
    # "<relation>'s name is <Name>" ("my sister's name is Maya").
    m = re.search(r"\b[Mm]y (" + REL_RE + r")[’']s name is ("
                   + NAME_RE + r")\b", text)
    if m and _good_name(m.group(2)):
        return {"name": m.group(2), "relation": _norm_rel(m.group(1)),
                "confidence": "high"}
    # Uncertain: an uncapitalized name, or a relation word outside
    # the vocabulary — stage it and ASK, never assume.  High
    # patterns run first, so capitals here mean unknown-relation.
    m = re.search(r"\b[Tt]his is my ([a-z ]{1,24}?),?\s+([A-Za-z]+"
                  r"(?: [A-Za-z]+)?)\s*$", text.strip())
    if m and not any(w in NAME_BAN for w in m.group(2).lower().split()):
        return {"name": m.group(2).title(),
                "relation": _norm_rel(m.group(1)), "confidence": "low"}
    m = re.search(r"\b[Mm]eet my ([a-z ]{1,24}?) ([A-Za-z]+"
                  r"(?: [A-Za-z]+)?)\s*$", text.strip())
    if m and not any(w in NAME_BAN for w in m.group(2).lower().split()):
        return {"name": m.group(2).title(),
                "relation": _norm_rel(m.group(1)), "confidence": "low"}
    return None


def _fields(segments):
    """Keyed trailing segments ("K: v"); the bare head is separate."""
    out = {}
    for p in segments:
        if ": " in p:
            k, v = p.split(": ", 1)
            out[k] = v
    return out


def _parse_people(text):
    """Parse-tolerant reader: bad lines are skipped, never fatal."""
    people = {}
    current = None
    for line in text.splitlines():
        try:
            if line.startswith("PERSON: "):
                segs = line[len("PERSON: "):].split(" | ")
                key = segs[0].strip().lower()
                if not key:
                    continue
                fields = _fields(segs[1:])
                current = {
                    "key": key,
                    "display": fields.get("DISPLAY", key),
                    "first_met": float(fields.get("FIRST", "0") or 0),
                    "last_seen": float(fields.get("LAST", "0") or 0),
                    "mentions": int(float(fields.get("MENTIONS", "0") or 0)),
                    "importance": float(fields.get("IMPORT", "1") or 1),
                    "aliases": [], "relationships": [], "facts": [],
                }
                people[key] = current
            elif line.startswith("ALIAS: ") and current is not None:
                current["aliases"].append(line[len("ALIAS: "):].strip())
            elif line.startswith("REL: ") and current is not None:
                segs = line[len("REL: "):].split(" | ")
                fields = _fields(segs[1:])
                until = fields.get("UNTIL", "-").strip()
                current["relationships"].append({
                    "relation": segs[0].strip(),
                    "since": float(fields.get("SINCE", "0") or 0),
                    "until": None if until == "-" else float(until),
                    "src": fields.get("SRC", "?"),
                })
            elif line.startswith("FACT: ") and current is not None:
                segs = line[len("FACT: "):].split(" | ")
                fields = _fields(segs[1:])
                current["facts"].append({
                    "fact": segs[0].strip(),
                    "ts": float(fields.get("TS", "0") or 0),
                    "src": fields.get("SRC", "?"),
                })
        except (ValueError, AttributeError):
            continue
    return people


class PeopleModel:
    """One record per person, persisted through the message bus."""

    def __init__(self, path=PEOPLE_FILE, pending_path=PENDING_PEOPLE,
                 clock=time.time, persist=True):
        self.path = path
        self.pending_path = pending_path
        self._clock = clock
        # Finding #4: persist=False loads current state but never
        # touches disk — detectors propose in memory; only the
        # post-selection commit writes (default True preserves every
        # existing caller).
        self._persist = persist
        self.people = {}
        self.load()

    def now(self):
        return self._clock()

    # ── PERSISTENCE ──────────────────────────────────────────
    def load(self):
        self.people = _parse_people(bus_read(self.path))
        # Lazy decay: the unmentioned fade by the clock, never by
        # a lobe sweep — no thread, no schedule, fully testable.
        now = self.now()
        for rec in self.people.values():
            quiet = max(0.0, now - rec["last_seen"])
            if quiet > 0:
                rec["importance"] = max(
                    IMPORTANCE_FLOOR,
                    min(IMPORTANCE_CAP, rec["importance"])
                    * 0.5 ** (quiet / DECAY_HALFLIFE))

    def save(self):
        if not self._persist:
            return
        from aura_state import deny_live_write
        deny_live_write(self.path)
        lines = [f"--- AURA PEOPLE (v1) | N: {len(self.people)} ---"]
        for key in sorted(self.people):
            r = self.people[key]
            lines.append(
                f"PERSON: {key} | DISPLAY: {r['display']} | "
                f"FIRST: {int(r['first_met'])} | LAST: {int(r['last_seen'])} | "
                f"MENTIONS: {r['mentions']} | IMPORT: {r['importance']:.3f}")
            for a in r["aliases"]:
                lines.append(f"ALIAS: {a}")
            for rel in r["relationships"]:
                until = "-" if rel["until"] is None else f"{int(rel['until'])}"
                lines.append(
                    f"REL: {rel['relation']} | SINCE: {int(rel['since'])} | "
                    f"UNTIL: {until} | SRC: {rel['src']}")
            for f in r["facts"]:
                lines.append(f"FACT: {f['fact']} | TS: {int(f['ts'])} | "
                             f"SRC: {f['src']}")
        bus_write(self.path, "\n".join(lines) + "\n")

    # ── LOOKUP ───────────────────────────────────────────────
    def who_is(self, name):
        """Case/alias/display-insensitive lookup; None when unknown."""
        key = " ".join(str(name).lower().split())
        if key in self.people:
            return self.people[key]
        for rec in self.people.values():
            if key in [a.lower() for a in rec["aliases"]]:
                return rec
            if key == rec["display"].lower():
                return rec
        return None

    def names(self):
        return [r["display"] for r in self.people.values()]

    def match_attr_fact(self, key, keywords):
        """Best held fact answering the requested attribute, else None.

        Finding #6: person-attribute frames (what-does / possessive /
        where / how-old) must answer the REQUESTED held fact — never an
        unrelated one. Matching is whole-word on a narrow plural/3rd-
        person stem so "like" finds "likes hiking" but never
        "lives in Berlin". Keywords are caller-supplied attribute words.
        Finding #8: scoring prefers more distinct keyword hits, then
        the earliest hit (an attribute-led predicate such as "lives
        in Berlin" beats an incidental mention such as "is a live
        performer" regardless of order), then the most recent fact —
        so an accepted person-fact correction surfaces on ties.
        Pure single-keyword ties stay recency-biased by design (both
        facts retained; `describe` lists all). Nothing is erased.
        """
        rec = self.people.get(" ".join(str(key or "").lower().split()))
        if rec is None:
            return None
        wants = {_stem_attr_word(w) for w in (keywords or [])}
        wants.discard("")
        if not wants:
            return None
        best, best_key = None, None
        for f in rec.get("facts", []):
            words = [_stem_attr_word(w)
                     for w in str(f.get("fact", "")).split()]
            hit_idx = [i for i, w in enumerate(words) if w in wants]
            if not hit_idx:
                continue
            score = (len({words[i] for i in hit_idx}), -hit_idx[0])
            # Chronological scan, latest wins ties: recency bias for
            # accepted corrections.
            if best_key is None or score >= best_key:
                best, best_key = f.get("fact", ""), score
        return best
        rec = self.people.get(" ".join(str(key or "").lower().split()))
        if rec is None:
            return None
        wants = {_stem_attr_word(w) for w in (keywords or [])}
        wants.discard("")
        if not wants:
            return None
        for f in reversed(rec.get("facts", [])):
            words = {_stem_attr_word(w)
                     for w in str(f.get("fact", "")).split()}
            if wants & words:
                return f.get("fact", "")
        return None

    def current_relation(self, rec):
        for rel in reversed(rec["relationships"]):
            if rel["until"] is None:
                return rel["relation"]
        return None

    # ── LEARNING ─────────────────────────────────────────────
    def commit(self, name, relation, src="architect", now=None,
               first_met=None):
        """
        Record (or update) who someone is.  Returns (record,
        change) with change in new/same/updated — a changed
        relationship closes the old one, never overwrites it.
        """
        now = self.now() if now is None else now
        key = " ".join(name.lower().split())
        display = " ".join(name.split())
        rec = self.people.get(key)
        if rec is None:
            rec = {"key": key, "display": display, "first_met": now,
                   "last_seen": now, "mentions": 1, "importance": 1.0,
                   "aliases": [], "relationships": [], "facts": []}
            self.people[key] = rec
            change = "new"
        else:
            change = "same"
            rec["mentions"] += 1
            rec["last_seen"] = now
            if first_met is not None and first_met < rec["first_met"]:
                rec["first_met"] = first_met
        cur = self.current_relation(rec)
        if cur != relation:
            for rel in rec["relationships"]:
                if rel["until"] is None:
                    rel["until"] = now
            rec["relationships"].append(
                {"relation": relation, "since": now, "until": None,
                 "src": src})
            if change == "same":
                change = "updated"
        rec["importance"] = min(IMPORTANCE_CAP, rec["importance"] + 0.1)
        self.save()
        return rec, change

    def note_mention(self, name, now=None):
        """A sighting: count it, stamp it, warm it.  False if unknown."""
        now = self.now() if now is None else now
        rec = self.who_is(name)
        if rec is None:
            return False
        rec["mentions"] += 1
        rec["last_seen"] = now
        rec["importance"] = min(IMPORTANCE_CAP, rec["importance"] + 0.1)
        self.save()
        return True

    def learn_fact(self, name, fact, src="architect", now=None):
        """One learned fact, deduped and capped.  False if unknown."""
        now = self.now() if now is None else now
        rec = self.who_is(name)
        if rec is None:
            return False
        fact = " ".join(str(fact).split())[:80]
        if not fact:
            return False
        if any(f["fact"].lower() == fact.lower() for f in rec["facts"]):
            return False
        rec["facts"].append({"fact": fact, "ts": now, "src": src})
        del rec["facts"][:-MAX_FACTS]
        self.save()
        return True

    def learn_fact_from_text(self, text):
        """
        "Sarah likes hiking" about someone KNOWN becomes a fact.
        Unknown names are never learned from — that road ends in
        confabulation.
        """
        learned = []
        for rec in self.people.values():
            for alias in [rec["display"]] + rec["aliases"]:
                m = re.search(r"\b" + re.escape(alias) + r"\s+"
                              r"(likes|loves|works as|lives in|is a|is an)"
                              r"\s+([^.]{1,80})", text, re.IGNORECASE)
                if m and text[m.start()].isupper():
                    fact = f"{m.group(1).lower()} {m.group(2).strip()}"
                    if self.learn_fact(rec["key"], fact):
                        learned.append((rec, fact))
        return learned

    def describe(self, rec, day_str):
        """Template speech: relationship + when learned + top facts."""
        rel = self.current_relation(rec) or "someone I know"
        out = (f"{rec['display']} is your {rel} — you introduced us "
               f"on {day_str}.")
        if rec["facts"]:
            shown = "; ".join(f["fact"] for f in rec["facts"][:3])
            out += f" I know {len(rec['facts'])} things: {shown}."
        else:
            out += " No notes yet — tell me about them."
        return out

    # ── THE ARCHITECT (V6 C3) ────────────────────────────────
    def ensure_architect(self, now=None):
        """Idempotent seed: the Architect has always been here."""
        now = self.now() if now is None else now
        rec = self.people.get(ARCHITECT_KEY)
        if rec is None:
            rec = {"key": ARCHITECT_KEY, "display": ARCHITECT_DISPLAY,
                   "first_met": now, "last_seen": now, "mentions": 0,
                   "importance": IMPORTANCE_CAP,
                   "aliases": ["architect"], "relationships": [],
                   "facts": []}
            rec["relationships"].append(
                {"relation": "architect", "since": now, "until": None,
                 "src": "founding"})
            self.people[ARCHITECT_KEY] = rec
            self.save()
        return rec

    def ensure_current(self, key=ARCHITECT_KEY, display=None, now=None):
        """Return this partition's explicitly bound current speaker."""
        key = " ".join(str(key or ARCHITECT_KEY).lower().split())
        if key == ARCHITECT_KEY:
            return self.ensure_architect(now=now)
        now = self.now() if now is None else now
        rec = self.people.get(key)
        if rec is None:
            rec = {"key": key, "display": display or UNKNOWN_DISPLAY,
                   "first_met": now, "last_seen": now, "mentions": 0,
                   "importance": IMPORTANCE_CAP, "aliases": [],
                   "relationships": [{"relation": "interlocutor",
                                      "since": now, "until": None,
                                      "src": "partition"}], "facts": []}
            self.people[key] = rec
            self.save()
        elif display and rec.get("display") == UNKNOWN_DISPLAY:
            rec["display"] = " ".join(str(display).split())
            self.save()
        return rec

    def set_display(self, name, display, now=None):
        """Set a known person's primary display name; aliases remain."""
        rec = self.who_is(name)
        display = " ".join(str(display or "").split())
        if rec is None or not display or not _good_name(display):
            return False
        old = rec.get("display", "")
        if old.lower() == display.lower():
            return False
        if old and old != UNKNOWN_DISPLAY and old.lower() not in {
                a.lower() for a in rec["aliases"]}:
            rec["aliases"].append(old)
        rec["display"] = display
        rec["last_seen"] = self.now() if now is None else now
        self.save()
        return True

    def add_alias(self, name, alias, now=None):
        """A new name for someone known.  False if unknown."""
        now = self.now() if now is None else now
        rec = self.who_is(name)
        if rec is None:
            return False
        alias = " ".join(str(alias).split())
        known = {rec["display"].lower(), rec["key"]} | {
            a.lower() for a in rec["aliases"]}
        if not alias or alias.lower() in known:
            return False
        rec["aliases"].append(alias)
        rec["last_seen"] = now
        self.save()
        return True

    def describe_architect(self, rec, episodes, day_str, now=None):
        """You, to her: projects, preferences, notes, history.

        ``episodes=None`` omits the conversation count for response paths
        that must not read episodic storage outside M14. Existing callers
        that supply a list keep the historical count unchanged.
        """
        projects = [f["fact"][len("project: "):] for f in rec["facts"]
                    if f["fact"].startswith("project: ")]
        prefs = [f["fact"] for f in rec["facts"]
                 if re.match(r"^(likes|loves|prefers) ", f["fact"])]
        notes = [f["fact"][len("note: "):] for f in rec["facts"]
                 if f["fact"].startswith("note: ")]
        other = [f["fact"] for f in rec["facts"]
                 if f["fact"] not in
                 (["project: " + p for p in projects] + prefs
                  + ["note: " + n for n in notes])]
        now = self.now() if now is None else now
        days = max(1, int((now - rec["first_met"]) / 86400.0))
        out = (f"You are the Architect — {rec['display']} to me. "
               f"{days} day" + ("" if days == 1 else "s") + " together")
        if episodes is not None:
            convos = sum(1 for e in episodes
                         if e.get("kind") == "conversation")
            out += (f", {convos} conversation"
                    + ("" if convos == 1 else "s"))
        out += "."
        if projects:
            out += " Projects: " + "; ".join(projects[:3]) + "."
        if prefs:
            out += " You " + "; ".join(second_person(p) for p in prefs[:3]) + "."
        if notes:
            out += " Notes: " + "; ".join(notes[:3]) + "."
        if other:
            out += " Also held: " + "; ".join(other[:2]) + "."
        if not rec["facts"]:
            out += (" I am still learning you — tell me about your "
                    "projects and what you like.")
        return out

    def describe_current(self, rec, episodes, day_str, now=None,
                         creator=False):
        """Describe the bound current speaker as YOU, never third person."""
        if creator:
            return self.describe_architect(rec, episodes, day_str, now=now)
        display = rec.get("display") or UNKNOWN_DISPLAY
        if display == UNKNOWN_DISPLAY:
            out = ("You are the person speaking with me. I do not know "
                   "your name yet — tell me what to call you.")
        else:
            aliases = [a for a in rec.get("aliases", [])
                       if a.lower() != display.lower()]
            out = f"You are {display} to me."
            if aliases:
                out += " I also know you as " + ", ".join(aliases[:3]) + "."
        facts = [render_fact(f["fact"], "current")
                 for f in rec.get("facts", [])[:4]]
        if facts:
            out += " I know that " + "; ".join(facts) + "."
        elif display != UNKNOWN_DISPLAY:
            out += " I am still learning about you."
        return out

    # ── PENDING INTRODUCTIONS ────────────────────────────────
    def stage(self, name, relation, src_text="", now=None):
        """
        Park one uncertain introduction for confirm/cancel.
        Returns False (leaving the old park untouched) when a
        slot is already waiting — like tools, a second park must
        not silently discard the first.
        """
        now = self.now() if now is None else now
        if self.pending():
            return False
        if not self._persist:
            # Proposal only: same True contract, no disk trace.
            return True
        bus_write(self.pending_path,
                  f"NAME: {name} | REL: {relation} | TS: {int(now)} | "
                  f"SRC: {' '.join(src_text.split())[:120]}\n")
        return True

    def pending(self):
        """The staged introduction, or None."""
        try:
            line = bus_read(self.pending_path).strip()
        except Exception:
            return None
        if not line.startswith("NAME: "):
            return None
        try:
            segs = line[len("NAME: "):].split(" | ")
            name = segs[0].strip()
            if not name:
                return None
            fields = _fields(segs[1:])
            return {"name": name,
                    "relation": fields.get("REL", "").strip(),
                    "ts": float(fields.get("TS", "0") or 0),
                    "src": fields.get("SRC", "")}
        except (ValueError, AttributeError):
            return None

    def clear_pending(self):
        if not self._persist:
            return
        bus_write(self.pending_path, "")
