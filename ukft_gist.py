# ukft_gist.py — Nightly gist abstraction (G6)
# ==========================================================
# The day's story, abstracted and re-ingested: top concepts of
# the day's episodes + thread outcomes, written back as ONE
# canonical vault ANCHOR (SOURCE: GIST) via the vault contract
# (dedup + thread-safe — reruns never double-write).
# Extractive only: counts and quotes, zero invention.
#
#   python ukft_gist.py [user_id|--all]   (operator / nightly job)
# ==========================================================

import os
import re
import sys
import time

try:
    from ukft_time import SUMMARY_SKIP
except Exception:
    SUMMARY_SKIP = set()

STOP = set(SUMMARY_SKIP) | {
    "with", "that", "this", "from", "have", "been", "will",
    "would", "should", "could", "into", "also", "more", "some",
    "such", "when", "where", "what", "there", "these", "those",
    "than", "then", "about", "after", "before", "because",
    "while", "only", "very", "just", "even", "each", "both",
    "does", "done", "doing", "know", "tell", "remember",
    "learned", "about", "with",
}


def _content_words(text):
    return [w for w in re.findall(r"[a-z]+", str(text or "").lower())
            if len(w) > 2 and w not in STOP]


def gist_episodes(episodes, day_label):
    """One gist line from episode dicts. '' when nothing to say."""
    if not episodes:
        return ""
    counts: dict = {}
    for e in episodes:
        for c in e.get("concepts", []) or []:
            c = str(c).lower()
            if len(c) > 2 and c not in STOP:
                counts[c] = counts.get(c, 0) + 1
        for w in _content_words(e.get("content", "")):
            counts[w] = counts.get(w, 0) + 1
    if not counts:
        return ""
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    topics = ", ".join(f"{w} ({n})" for w, n in top)
    n = len(episodes)
    return (f"Night of {day_label}: {n} exchange" +
            ("" if n == 1 else "s") +
            f". Most alive: {topics}.")


def gist_user(user_id, manager=None):
    """Distill one user's day into their vault. Returns the line."""
    from ukft_user_state import get_user_state_manager
    from ukft_episodic import EpisodicMemory
    from aura_vault_io import append_anchor
    mgr = manager or get_user_state_manager()
    udir = mgr.user_dir(user_id)
    mem = EpisodicMemory(path=str(udir / "episodic_memory.txt"))
    mem.load()
    if not mem.episodes:
        return ""
    day_label = time.strftime("%d %B %Y")
    line = gist_episodes(
        [{"concepts": e.get("concepts", []),
          "content": e.get("content", "")} for e in mem.episodes],
        day_label)
    if not line:
        return ""
    append_anchor(str(udir / "locked_patterns.txt"),
                  "Nightly Gist", line, "GIST")
    return line


def _cli():
    from ukft_user_state import get_user_state_manager
    args = sys.argv[1:]
    mgr = get_user_state_manager()
    targets = mgr.list_users() if args == ["--all"] else args
    if not targets:
        print("usage: python ukft_gist.py [user_id|--all]")
        return 1
    for uid in targets:
        try:
            line = gist_user(uid, mgr)
            print(f"{uid}: {line or '(nothing to distill)'}")
        except Exception as e:
            print(f"{uid}: FAILED ({e})")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
