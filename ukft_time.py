# ukft_time.py — AURA Time & Situation (V6 C1)
# ==================================================
# She lives in time now.  The wall clock becomes day boundaries,
# session stamps, and real windows behind "yesterday / today /
# recently" — R4 attaches them to every plan (additively; the
# graph still holds no temporal facts, so WHEN stays honest),
# and the episodic diary gets a door: episodes filtered by
# window, days summarized by kind and topic.
#
#   - TimeContext(clock): now(), midnight(), today/yesterday
#     bounds, day stamps ("2026-09-15", "15 September 2026"),
#     session ids (one session is one day), new-day detection.
#   - resolve_time(text, now): whole-word "yesterday / today /
#     this morning / recently / this week" -> (label, start, end).
#     Narrowest match wins when several words appear.
#   - episodes_in_window(episodes, start, end): diary slice,
#     oldest first.
#   - summarize_day(episodes, day_ts): grouped counts, ranked
#     topics, capped lines, and a `broad` flag C4 uses to ask
#     the Architect to narrow a busy day down.
# ==================================================

import re
import time
from datetime import datetime

DAY_SECONDS = 86400.0
RECENT_SECONDS = 3 * DAY_SECONDS   # "recently" trails three days
WEEK_SECONDS = 7 * DAY_SECONDS     # "this week" trails seven days

# Command scaffolding, not topics: the diary faithfully records
# "remind me to water the plants", but a summary about "remind"
# helps nobody.  Summaries skip these; the episodes keep them.
SUMMARY_SKIP = {
    "remind", "remember", "forget", "confirm", "cancel", "done",
    "finished", "finish", "plan", "call",
}


def _midnight(ts):
    """Local midnight starting the day that holds ts."""
    return datetime.fromtimestamp(ts).replace(
        hour=0, minute=0, second=0, microsecond=0).timestamp()


def resolve_time(text, now):
    """
    Map time words to a real window.  Returns
    {"label", "start", "end"} (epoch seconds) or None when the
    text names no time.  Whole words only — "recently" must not
    fire inside a longer word, and a narrower window beats a
    wider one when both are named.
    """
    words = set(re.findall(r"[a-z]+", text.lower()))
    mid = _midnight(now)
    if "yesterday" in words:
        return {"label": "yesterday", "start": mid - DAY_SECONDS,
                "end": mid}
    if "morning" in words and "this" in words:
        noon = mid + 12 * 3600.0
        return {"label": "this morning", "start": mid,
                "end": noon if now > noon else now}
    if "today" in words:
        return {"label": "today", "start": mid, "end": now}
    if words & {"recently", "lately"}:
        return {"label": "recently", "start": now - RECENT_SECONDS,
                "end": now}
    if "week" in words and "this" in words:
        return {"label": "this week",
                "start": _midnight(now - (WEEK_SECONDS - DAY_SECONDS)),
                "end": now}
    return None


def episodes_in_window(episodes, start, end):
    """Diary slice whose timestamps fall in [start, end], oldest first."""
    return [e for e in episodes
            if start <= float(e.get("ts", 0)) <= end]


def summarize_day(episodes, day_ts, max_lines=12, broad_at=25):
    """
    One day's diary as grouped counts + ranked topics.  Pure
    mechanism — C4/C6 decide what to SAY with it.
    """
    mid = _midnight(day_ts)
    day_eps = episodes_in_window(episodes, mid, mid + DAY_SECONDS)
    by_kind = {}
    topics = {}
    for e in day_eps:
        by_kind[e.get("kind", "event")] = \
            by_kind.get(e.get("kind", "event"), 0) + 1
        for c in e.get("concepts", []):
            if c in SUMMARY_SKIP:
                continue
            topics[c] = topics.get(c, 0) + 1
    ranked = sorted(topics.items(), key=lambda kv: (-kv[1], kv[0]))
    lines = [f"{kind}: {n}" for kind, n in sorted(by_kind.items())]
    lines += [f"about {t} ({n})" for t, n in ranked[:max_lines]]
    return {
        "day": datetime.fromtimestamp(mid).strftime("%Y-%m-%d"),
        "n": len(day_eps),
        "by_kind": by_kind,
        "topics": [t for t, _n in ranked],
        "lines": lines[:max_lines],
        "broad": len(day_eps) > broad_at,
    }


class TimeContext:
    """Clock-aware day/session stamps.  The clock injects for tests."""

    def __init__(self, clock=time.time):
        self._clock = clock

    def now(self):
        return self._clock()

    def midnight(self, ts=None):
        return _midnight(self.now() if ts is None else ts)

    def today_bounds(self):
        now = self.now()
        return self.midnight(now), now

    def yesterday_bounds(self):
        mid = self.midnight()
        return mid - DAY_SECONDS, mid

    def day_stamp(self, ts=None):
        return datetime.fromtimestamp(
            self.now() if ts is None else ts).strftime("%Y-%m-%d")

    def pretty_day(self, ts=None):
        # Portable day ("15 September 2026") — %-d is POSIX-only.
        dt = datetime.fromtimestamp(self.now() if ts is None else ts)
        return f"{dt.day} {dt.strftime('%B %Y')}"

    def session_id(self, ts=None):
        """One session is one day: the id is the day stamp."""
        return "session-" + self.day_stamp(ts)

    def is_new_day(self, last_ts, now=None):
        now = self.now() if now is None else now
        return self.day_stamp(last_ts) != self.day_stamp(now)

    def window(self, label):
        """Named window ending now: today/yesterday/recently/this week."""
        now = self.now()
        mid = self.midnight(now)
        if label == "today":
            return mid, now
        if label == "yesterday":
            return mid - DAY_SECONDS, mid
        if label == "recently":
            return now - RECENT_SECONDS, now
        if label == "this week":
            return self.midnight(now - (WEEK_SECONDS - DAY_SECONDS)), now
        raise ValueError(f"unknown window: {label}")
