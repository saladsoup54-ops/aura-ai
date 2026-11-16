# ukft_delight.py — Memory as delight (G6)
# ==========================================================
# She volunteers real shared history (never fabricated), tells
# true standings with receipts, surfaces forgetting honestly,
# and distills nightly gists back into the vault. Everything
# here reads; the gist is the one writer, and it writes
# canonical ANCHOR records only.
# ==========================================================

import re
import time

# "Where do we stand" patterns (module API pre-check).
STANDING_PATTERNS = (
    r"where do we stand",
    r"how long have we",
    r"how long (has it|has this) been",
    r"what do you remember about (me|us)",
)


def is_standing_question(text):
    t = " ".join(str(text or "").strip().lower().split())
    return any(re.search(p, t) for p in STANDING_PATTERNS)


def _read_lines(path, limit=400):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().splitlines()[-limit:]
    except OSError:
        return []


def _count_anchors(path):
    return sum(1 for l in _read_lines(path, 100000)
               if "ANCHOR:" in l and "DATA:" in l)


def standing_line(profile, user_dir):
    """True receipts: conversations, days, facts, faded trivia."""
    import os
    turns = profile.turn_count
    days = max(1, int((time.time() - profile.started_at) / 86400.0))
    facts = profile.facts_learned
    faded = 0
    try:
        faded = sum(1 for l in _read_lines(
            os.path.join(str(user_dir), "forgotten_memories.txt"),
            100000) if l.strip())
    except Exception:
        faded = 0
    stage = (profile.depth_stage or "STRANGER").lower()
    bits = [f"{turns} conversation" + ("" if turns == 1 else "s"),
            f"{days} day" + ("" if days == 1 else "s") + " together",
            f"{facts} thing" + ("" if facts == 1 else "s") + " learned"]
    out = ("Us, honestly: " + ", ".join(bits) + f" — {stage}.")
    if faded:
        out += f" I've let {faded} little trivium fade; kept what matters."
    return out


def volunteer_line(user_dir, depth_stage):
    """One real shared memory to volunteer (FAMILIAR+ only).
    People facts first, then latest closed thread, then newest
    episode — verbatim, short, never invented. '' when young."""
    from ukft_roleplay import DEPTH_RANK
    import os
    if DEPTH_RANK.get(depth_stage, 0) < DEPTH_RANK.get("FAMILIAR", 2):
        return ""
    base = str(user_dir)
    for line in _read_lines(os.path.join(base, "people.txt")):
        if line.startswith("FACT: "):
            fact = line[len("FACT: "):].split(" | ")[0].strip()
            if fact:
                return "I still hold that " + fact[:120] + "."
    for line in _read_lines(os.path.join(base, "threads.txt")):
        if not line.startswith("THREAD: "):
            continue
        segs = line[len("THREAD: "):].split(" | ")
        fields = dict(p.split(": ", 1) for p in segs[1:]
                      if ": " in p)
        if fields.get("STATUS", "").strip().lower() == "closed" \
                and fields.get("TOPIC", "").strip():
            return "Remember when we finished: " \
                + fields["TOPIC"].strip()[:120] + "?"
    try:
        from ukft_recall import is_question_echo
    except Exception:
        is_question_echo = lambda c: False
    for line in reversed(_read_lines(
            os.path.join(base, "episodic_memory.txt"))):
        if "| KIND: reply |" in line or "immersive:" in line:
            continue
        m = re.search(r"\| CONTENT: (.*)$", line)
        content = (m.group(1).strip() if m else line.strip())
        if len(content) < 12 or is_question_echo(content):
            continue
        return "I keep thinking about: " + content[:120] + "."
    return ""
