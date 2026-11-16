# ukft_recall.py — AURA Recall (V6 C4)
# ==================================================
# The door into the diary she already keeps.  Episodic recall
# by time, person, and topic — pure functions over episode
# dicts, so the bridge supplies the live stores and the tests
# supply fixtures.  Recall only speaks when the diary holds
# something; otherwise it returns None and the normal pipeline
# (proof, honest ignorance, association) proceeds untouched.
#
#   - recall_time(episodes, window): "what did we talk about
#     yesterday" -> grouped, ranked summary; a busy window asks
#     the Architect to narrow it to a thread.
#   - recall_person(record, episodes, day_str): who they are plus
#     the latest diary traces of them.
#   - recall_topic(episodes, words): ranked episode hits on real
#     content words (chat grammar is filtered, never searched).
# ==================================================

from ukft_context import person_phrase
from ukft_time import SUMMARY_SKIP, episodes_in_window

import re

MAX_FRAGMENTS = 6
BROAD_AT = 25

# Grammar around the topic, never the topic — searching these
# matches every diary line and recalls nothing.  Modals and
# auxiliaries especially ("should" matched every intention ever
# logged); deictics ("now", "here") match the moment, not the
# matter.  Fix-pass: this set is what stands between "what should
# I cook" and "we should call mom".
TOPIC_STOP = {
    "about", "said", "say", "says", "talk", "talked", "talking",
    "tell", "told", "know", "knew", "thing", "things", "something",
    "today", "yesterday", "recently", "lately", "day", "week",
    "morning", "remember", "recall", "discuss", "discussed", "did",
    "does", "what", "which",
    "should", "would", "could", "will", "shall", "may", "might",
    "must", "have", "has", "had", "am", "is", "are", "was", "were",
    "be", "been", "do", "does", "did", "can",
    "now", "then", "here", "still", "just", "really", "very", "too",
    "also", "even", "ever", "never", "always", "again", "back",
    "than", "that", "this", "them", "they", "their", "our", "your",
    "with", "from",
}

# A diary line quoting its own question ("what is dark matter?
# -> vault") is a log entry, not substance — recalling it reads
# the log aloud (seen live).  Statement echoes ("this is my
# fiancee, Sarah -> people") stay: they ARE what was said.
QUESTION_OPENERS = (
    "what", "who", "where", "when", "why", "how", "is", "are",
    "was", "were", "compare", "tell me", "what can", "do", "does",
    "did", "can", "could", "would", "should", "have", "has",
)


# Social acts are never diary questions: gratitude and farewells
# ("thanks Jo", "good night") answered from the log read chatter
# aloud (seen live).  Leftover content beyond the act itself
# ("thank you for the book") keeps recall alive.
SOCIAL_ACT_WORDS = {
    "thanks", "thank", "thx", "bye", "goodbye", "goodnight",
    "night", "nite", "farewell", "see", "later", "sorry",
}


def is_social_act(text):
    """Gratitude/farewell with no query inside, or False."""
    words = re.findall(r"[a-z]+", str(text or "").lower())
    if not words:
        return False
    if not any(w in SOCIAL_ACT_WORDS or
               (w == "good" and "night" in words)
               for w in words):
        return False
    left = [w for w in words if w not in SOCIAL_ACT_WORDS
            and w not in ("good", "you", "see", "later", "all")]
    if not left:
        return True
    if len(left) <= 2 and all(len(w) <= 12 for w in left):
        return True
    return False


def is_story_request(text):
    """
    Bedtime imperatives ("tell me a story/joke") route to the
    associative vault, never the diary.  Definite forms ("our
    story so far", "tell me the story") stay agenda/recall
    business — only the indefinite article diverts.
    """
    t = " ".join(str(text or "").lower().split())
    return bool(re.search(
        r"\btell (me|us) a (story|stories|joke|jokes|tale|tales|"
        r"riddle|riddles)\b", t))


def is_question_echo(content):
    """
    A diary line that only logs a turn ("wrong -> teach",
    "thanks -> voice", "what is X? -> vault") is a log entry, not
    substance — recalling it reads the log aloud.  Fix-pass: ANY
    routing-ink line whose spoken head is question-formed OR too
    short to hold substance (bare inputs, degenerate fragments)
    is an echo.  Kept: statement echoes with real content ("this
    is my fiancee, Sarah -> people") — they ARE what was said.
    """
    head = str(content or "").rsplit(" -> ", 1)
    if len(head) != 2 or not head[1].strip():
        return False
    q = head[0].strip().lower()
    if not q:
        return False
    if q.endswith("?"):
        return True
    if q.startswith(QUESTION_OPENERS):
        return True
    if len(re.findall(r"[a-z]+", q)) <= 2:
        return True
    return False


def _spoken(content):
    """
    Diary lines carry routing ink ("question -> vault") that must
    never be read aloud — strip a known winner tail, keep the
    words that were actually said.
    """
    head, sep, tail = str(content or "").rpartition(" -> ")
    if sep and tail.strip() in ("execute", "focus", "sleep", "tools",
                                "reasoning", "voice", "vault", "field",
                                "dark", "context", "recap", "people",
                                "agenda", "belief", "self", "teach"):
        return head.strip()
    return str(content or "").strip()


def _grouped(episodes):
    """Kind counts + topics ranked by frequency (ties alphabetical)."""
    by_kind = {}
    topics = {}
    for e in episodes:
        by_kind[e.get("kind", "event")] = \
            by_kind.get(e.get("kind", "event"), 0) + 1
        for c in e.get("concepts", []):
            if c in SUMMARY_SKIP:
                continue
            topics[c] = topics.get(c, 0) + 1
    ranked = sorted(topics.items(), key=lambda kv: (-kv[1], kv[0]))
    return by_kind, [t for t, _n in ranked]


def recall_time(episodes, window, people=None):
    """
    Summarize the diary inside window {"label","start","end"}.
    None when the window holds nothing — silence, not invention.
    Known people are named with their relationship (C5: context
    unasked) instead of a bare topic word.
    """
    eps = episodes_in_window(episodes, window["start"], window["end"])
    if not eps:
        return None
    label = window["label"].capitalize()
    by_kind, topics = _grouped(eps)
    if len(eps) > BROAD_AT:
        top = ", ".join(topics[:3]) if topics else "many things"
        return (f"{label} was busy ({len(eps)} things, mostly {top}). "
                f"Which thread — {', '.join(topics[:5])}?".rstrip())
    frags = [f"{n} {k}" + ("" if n == 1 else "s")
             for k, n in sorted(by_kind.items())]
    named = 0
    for t in topics:
        if len(frags) >= MAX_FRAGMENTS:
            break
        rec = None
        if people is not None:
            try:
                rec = people.who_is(t)
            except Exception:
                rec = None
        if rec is not None and named < 2:
            try:
                rel = people.current_relation(rec)
            except Exception:
                rel = None
            frags.append("with " + person_phrase(rec["display"], rel))
            named += 1
        else:
            frags.append(f"about {t}")
    things = "1 thing" if len(eps) == 1 else f"{len(eps)} things"
    return f"{label} ({things}): " + "; ".join(
        frags[:MAX_FRAGMENTS]) + "."


def recall_person(record, episodes, day_str, thread=None):
    """
    Who they are, the latest diary traces, and the live thread
    when it adds something (C5) — all unasked, all from memory.
    """
    from ukft_context import thread_line
    from ukft_people import PeopleModel
    _people = PeopleModel()
    out = _people.describe(record, day_str)
    keys = [record["key"]] + [a.lower() for a in record["aliases"]]
    # Reply-kind episodes are HER old lines, not evidence about the
    # world — quoting them parrots past speech as fact (live 17 Sept
    # 2026: pre-fix confabulations resurfaced as "memories").
    hits = [e for e in episodes
            if e.get("kind") != "reply"
            and any(k in e.get("content", "").lower() for k in keys)
            and not is_question_echo(e.get("content", ""))]
    if hits:
        recent = " / ".join(_spoken(h["content"])[:80]
                            for h in hits[-2:])
        out += f" Recently: {recent}."
    about = set(record["key"].split()) | set(
        record["display"].lower().split())
    try:
        about |= set((_people.current_relation(record) or "").split())
    except Exception:
        pass
    line = thread_line(thread, about=about)
    if line:
        out += f" {line}"
    return out


def recall_topic(episodes, words, echo=None):
    """
    Ranked episode hits on content words.  None when nothing
    matches — the question falls back to proof or ignorance.
    `echo` is the current question: its own prior echo in the
    diary ("what did we say about X -> ...") is substance-free
    and must not recall itself.
    """
    terms = [w.lower() for w in words
             if w.lower() not in TOPIC_STOP and len(w) > 2]
    if not terms:
        return None
    prefix = (echo or "")[:40].lower()
    scored = []
    for e in episodes:
        content = e.get("content", "")
        if e.get("kind") == "reply":
            continue
        if len(prefix) >= 12 and content.lower().startswith(prefix):
            continue
        if is_question_echo(content):
            continue
        # Score the SPOKEN words, never the routing ink: the old
        # code matched query words against "-> teach/vault/…"
        # tails ("teach me chess" recalled "wrong -> teach").
        # Fix-pass: strip the tail before scoring; substance only.
        spoken = _spoken(content)
        hay = (spoken + " " + " ".join(e.get("concepts", ""))).lower()
        hits = sum(1 for t in terms if t in hay)
        if hits:
            scored.append((hits, e.get("ts", 0), e))
    if not scored:
        return None
    scored.sort(key=lambda s: (s[0], s[1]), reverse=True)
    top = " / ".join(_spoken(s[2]["content"])[:80] for s in scored[:3])
    return f"I remember: {top}."
