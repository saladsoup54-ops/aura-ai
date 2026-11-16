# ukft_policy.py — AURA Conversational Policy (V7 F4)
# ==================================================
# Talks WITH, not AT: greetings fit the hour, and a greeting
# may ask one question back — naming an open thread first, an
# unattended curiosity second, silence otherwise (no thread, no
# question: honesty before initiative).  A second consecutive
# hello never nags twice.
#
# Hard boundaries (fluency contract):
#   - Proofs, quotes, ignorance, protocol and every non-greeting
#     turn are untouched — questions-back live on greetings ONLY
#     (a "?" would fail mouth verification and the grammar gate).
#   - The daypart mirrors ukft_presence exactly (same words, same
#     hour lines) — one voice for briefing and greeting.
#   - Topics render sanitized (capped, no smuggled punctuation),
#     never with "I remember" (the social guard: greetings greet).
# No state of its own: threads, gaps and turns are read where
# they live, so there is nothing to cap, back up, or preflight.
# ==================================================

import re
import time

MAX_TOPIC = 60


def daypart(hour=None):
    """
    Time of day in her own words — the presence briefing's exact
    mapping, so boot and greeting never disagree about the hour.
    """
    if hour is None:
        hour = time.localtime().tm_hour
    try:
        hour = int(hour) % 24
    except Exception:
        return "Hello"
    if 5 <= hour < 12:
        return "Good morning"
    if 12 <= hour < 18:
        return "Good afternoon"
    if 18 <= hour < 24:
        return "Good evening"
    return "Up late"


def clean_topic(text):
    """Short, flat, unpunctuated — safe inside a spoken question."""
    flat = " ".join(str(text or "").split())
    flat = flat.rstrip(".!?;:,").strip()
    if len(flat) > MAX_TOPIC:
        cut = flat[:MAX_TOPIC].rfind(" ")
        flat = flat[:cut] if cut > 20 else flat[:MAX_TOPIC]
    return flat.rstrip(".!?;:,").strip()


def question_back(threads=(), gaps=()):
    """
    One question naming what is open: oldest thread first, then
    the strongest unattended curiosity.  () or ("",) or attended-
    only means silence — never perform interest in nothing.
    """
    topics = [clean_topic(t) for t in (threads or [])]
    topics = [t for t in topics if t]
    if topics:
        return "Shall we pick up our thread on %s?" % topics[0]
    words = []
    for g in (gaps or []):
        try:
            (_kind, word), entry = g
        except Exception:
            continue
        if isinstance(entry, dict) and entry.get("attended"):
            continue
        word = clean_topic(word)
        if word:
            words.append(word)
    if words:
        return "Still curious about %s — shall we look?" % words[0]
    return None


def open_threads(path=None):
    """Oldest-first open thread topics; [] when none (never throws)."""
    try:
        from ukft_agenda import AgendaModel
        model = AgendaModel(path=path) if path else AgendaModel()
        return [t["topic"] for t in model.opened() if t.get("topic")]
    except Exception:
        return []


def open_gaps(path=None, n=3):
    """Top curiosity gaps ((kind, word), entry); [] when none."""
    try:
        from ukft_gaps import KnowledgeGaps
        model = KnowledgeGaps(path=path) if path else KnowledgeGaps()
        return model.top_gaps(n) or []
    except Exception:
        return []
