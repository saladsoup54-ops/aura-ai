# ukft_context.py — AURA Context Assembly (V6 C5)
# ==================================================
# The pre-answer gatherer: every turn's human context in one
# bundle — time + situation, people involved, recent episodes,
# their facts, the working-memory thread, and open threads
# (recent unanswered questions; C6 will persist them).
# Pure assembly over passed-in stores, so tests use fixtures
# and the bridge passes the live ones.  Consumers (recall,
# who-is) render bundle slices they did not ask for — that is
# the companion contract's "relevant context, unasked".
#
# Finding #6 (21 Sept 2026): only `current_user` reaches
# selection (M4/M3/M14, M5-proven). The `day`, `session`, and
# episode-derived `open_threads` keys had zero production readers
# and were retired. The remaining copies are DUPLICATE by design:
# detectors, recall, policy, and stance read the authoritative
# stores directly; the bundle keeps the C5 unit contract but feeds
# no decision. Perturbing any of them cannot move the winner
# (receipt: tests/verify_finding06_shadow_context.py).
# ==================================================

from ukft_time import TimeContext, resolve_time

RECENT_N = 5
OPEN_N = 3


def assemble(user_input, people=None, episodes=(), memory=None,
             gaps=(), now=None, drives=None, threads=None,
             current_person_key="architect"):
    """
    Build the human-context bundle.  All stores optional —
    missing ones simply contribute nothing, never an error.
    """
    tc = TimeContext() if now is None else TimeContext(clock=lambda: now)
    user_input = user_input or ""
    bundle = {
        "time_window": None,
        "people": [],
        "architect": None,
        "current_user": None,
        "recent": [],
        "facts": [],
        "thread": [],
        "gaps": [],
        "drives": dict(drives) if drives else {},
        "threads": [dict(t) for t in (threads or [])][:10],
    }
    for g in list(gaps)[:OPEN_N]:
        try:
            (kind, words), info = g
            bundle["gaps"].append(
                {"kind": kind, "words": words,
                 "count": info.get("count", 1)})
        except (ValueError, TypeError, AttributeError):
            continue
    try:
        bundle["time_window"] = resolve_time(user_input, tc.now())
    except Exception:
        pass
    words = set(user_input.lower().split())
    if people is not None:
        try:
            bundle["architect"] = people.who_is("architect")
        except Exception:
            pass
        try:
            bundle["current_user"] = people.people.get(current_person_key)
        except Exception:
            pass
        try:
            lowered = user_input.lower()
            for rec in people.people.values():
                keys = {rec["key"]} | {a.lower()
                                       for a in rec["aliases"]}
                if keys & words:
                    hit = True
                else:
                    # Substring fallback for possessives ("sarah's")
                    # — but only for keys long enough that "Al"
                    # can never fire on "hospital" (audited).
                    hit = any(len(k) > 2 and k in lowered
                              for k in keys)
                if hit:
                    bundle["people"].append(rec)
                    for f in rec["facts"]:
                        bundle["facts"].append(
                            (rec["display"], f["fact"]))
        except Exception:
            pass
    try:
        bundle["recent"] = list(episodes)[-RECENT_N:]
    except Exception:
        pass
    if memory is not None:
        try:
            bundle["thread"] = list(memory.recent_topic(3) or [])
        except Exception:
            pass
    return bundle


def person_phrase(display, relation=None):
    """'Sarah, your fiancee' — a person named with context attached."""
    if relation:
        return f"{display}, your {relation}"
    return display


def thread_line(thread, about=()):
    """
    'Our thread: france.' — the working-memory topic, spoken only
    when it adds something the answer does not already name.
    """
    words = [w for w in (thread or []) if w not in set(about)]
    if not words:
        return ""
    return "Our thread: " + " ".join(words[:4]) + "."
