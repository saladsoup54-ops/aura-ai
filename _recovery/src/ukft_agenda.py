# ukft_agenda.py — AURA Agenda & Continuity (V6 C6)
# ==================================================
# Threads that survive the night.  Intentions the Architect
# states ("remind me to water the plants") become persistent
# open threads; closing words ("done with the plants") close
# them; "our story so far" renders today plus everything still
# held.  The boot briefing proactively names the open count.
# Whole-file bus IO, parse-tolerant, capped — the diary keeps
# what happened, the agenda keeps what is still owed.
# ==================================================

import re
import time

from aura_bus import read as bus_read, write as bus_write
from aura_constants import THREADS_FILE

MAX_THREADS = 50

# Explicit intentions — future-owed turns, never observations.
# Fix-pass: telegraphic chat drops the "to" ("remind me milk")
# and the apostrophe ("lets go") — the specific forms stay first
# so "remind me to X" never captures a leading "to ".
INTENTION_RES = (
    r"\bremind me to ([^.?!]{1,80})",
    r"\bdo not forget to ([^.?!]{1,80})",
    r"\bdon't forget to ([^.?!]{1,80})",
    r"\bwe should ([^.?!]{1,80})",
    r"\bwe need to ([^.?!]{1,80})",
    r"\blet's ([^.?!]{1,80})",
    r"\bplan to ([^.?!]{1,80})",
    r"\bi plan to ([^.?!]{1,80})",
    r"\bremind me (?!to\b)([^.?!]{1,80})",
    r"\blets ([^.?!]{1,80})",
    r"\blet us ([^.?!]{1,80})",
)

CLOSE_RES = (
    r"\bdone with ([^.?!]{1,60})",
    r"\bfinished with ([^.?!]{1,60})",
    r"\bwe'?re done with ([^.?!]{1,60})",
)

STORY_RES = (
    r"our story so far",
    r"summariz[ei] (our day|today)",
    r"recap today",
    r"catch me up",
)


def extract_intention(text):
    """An owed turn, or None.  Observations never match."""
    t = " ".join(str(text).strip().split())
    for rx in INTENTION_RES:
        m = re.search(rx, t, re.IGNORECASE)
        if m and m.group(1).strip(" ,"):
            return " ".join(m.group(1).strip(" ,").split())[:80]
    return None


def extract_close(text):
    """A closing phrase's topic, or None."""
    t = " ".join(str(text).strip().split())
    for rx in CLOSE_RES:
        m = re.search(rx, t, re.IGNORECASE)
        if m and m.group(1).strip(" ,"):
            return " ".join(m.group(1).strip(" ,").split())[:60]
    return None


def is_story_request(text):
    """'Our story so far' and its siblings."""
    t = " ".join(str(text).lower().split())
    return any(re.search(rx, t) for rx in STORY_RES)


def _parse_threads(text):
    """Parse-tolerant reader: bad lines are skipped, never fatal."""
    threads = []
    for line in text.splitlines():
        try:
            if not line.startswith("THREAD: "):
                continue
            segs = line[len("THREAD: "):].split(" | ")
            head = segs[0].strip()
            if not head:
                continue
            fields = {}
            for p in segs[1:]:
                if ": " in p:
                    k, v = p.split(": ", 1)
                    fields[k] = v
            threads.append({
                "id": head,
                "topic": fields.get("TOPIC", ""),
                "opened": float(fields.get("OPENED", "0") or 0),
                "updated": float(fields.get("UPDATED", "0") or 0),
                "status": fields.get("STATUS", "open"),
                "kind": fields.get("KIND", "intention"),
                "src": fields.get("SRC", "?"),
            })
        except (ValueError, AttributeError):
            continue
    return threads


class AgendaModel:
    """Persistent open threads, oldest-first memory of what is owed."""

    def __init__(self, path=THREADS_FILE, clock=time.time,
                 persist=True):
        self.path = path
        self._clock = clock
        # Finding #4: persist=False proposes in memory only (see
        # PeopleModel — same contract, same default-True safety).
        self._persist = persist
        self.threads = []
        self.load()

    def now(self):
        return self._clock()

    def load(self):
        self.threads = _parse_threads(bus_read(self.path))

    def save(self):
        if not self._persist:
            return
        lines = [f"--- AURA AGENDA (v1) | N: {len(self.threads)} ---"]
        for t in self.threads:
            lines.append(
                f"THREAD: {t['id']} | TOPIC: {t['topic']} | "
                f"OPENED: {int(t['opened'])} | "
                f"UPDATED: {int(t['updated'])} | STATUS: {t['status']} | "
                f"KIND: {t['kind']} | SRC: {t['src']}")
        bus_write(self.path, "\n".join(lines) + "\n")

    def opened(self):
        """Live threads, oldest first."""
        return [t for t in self.threads if t["status"] == "open"]

    def open(self, topic, kind="intention", src="architect", now=None):
        """
        Hold a thread.  Returns (thread, new?) — restating an open
        thread refreshes it instead of duplicating it.
        """
        now = self.now() if now is None else now
        key = " ".join(str(topic).lower().split())
        for t in self.threads:
            if t["status"] == "open" and t["topic"].lower() == key:
                t["updated"] = now
                self.save()
                return t, False
        thread = {"id": f"t{int(now)}-{len(self.threads)}",
                  "topic": key,
                  "opened": now, "updated": now, "status": "open",
                  "kind": kind, "src": src}
        self.threads.append(thread)
        while len(self.threads) > MAX_THREADS:
            closed = [t for t in self.threads if t["status"] != "open"]
            if closed:
                victim = min(closed, key=lambda t: t["updated"])
            else:
                victim = min(self.threads, key=lambda t: t["updated"])
            self.threads.remove(victim)
        self.save()
        return thread, True

    def close(self, words, now=None):
        """
        Close the open thread best matching `words`.  Whole-word
        overlap wins; None when nothing held matches.
        """
        now = self.now() if now is None else now
        want = set(re.findall(r"[a-z]+", str(words).lower()))
        want -= {"the", "a", "an", "with", "done", "finished"}
        best, score = None, 0
        for t in self.opened():
            got = set(re.findall(r"[a-z]+", t["topic"]))
            overlap = len(want & got)
            if overlap > score:
                best, score = t, overlap
        if best is None:
            return None
        best["status"] = "closed"
        best["updated"] = now
        self.save()
        return best

    def story(self, episodes, day_ts):
        """'Our story so far': today grouped, threads still held."""
        from ukft_time import summarize_day
        s = summarize_day(episodes, day_ts)
        lines = [f"Today ({s['n']} thing{'s' if s['n'] != 1 else ''}): "
                 + ("; ".join(s["lines"][:6]) if s["lines"]
                    else "nothing yet") + "."]
        held = self.opened()
        if held:
            lines.append(f"Holding {len(held)} thread"
                         f"{'' if len(held) == 1 else 's'}: "
                         + "; ".join(t["topic"] for t in held[:5]) + ".")
        else:
            lines.append("No open threads — a clean slate.")
        return " ".join(lines)
