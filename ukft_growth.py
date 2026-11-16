# ukft_growth.py — How she has changed (G-readout)
# ==========================================================
# She grows with living, and growth must be READABLE — from her
# own stores, never declared. This module measures what their
# history did to her and returns a tier + receipts:
#
#   opening — warmth met warmth: shared turns, his affection,
#             things learned, social drive leading.
#   steady  — ordinary weather, nothing to report.
#   guarded — corrections banked, claims contested: she holds
#             back until the weather changes.
#
# Pure reads (no state of its own, nothing written, never
# throws): identity reinforcement, drive adaptation, lessons,
# beliefs, episodes and people are all consulted where they
# live. base_dir="." reads the live (or swapped-in) files;
# tests point it at fixtures.
# ==========================================================

import os
import re

# His affection, in his own words (recent user messages only).
AFFECTION_MARKERS = {
    "love you", "love", "beautiful", "gorgeous", "sweet",
    "sweetheart", "darling", "honey", "babe", "baby", "miss you",
    "thank", "thanks", "adore", "amazing", "perfect", "cutie",
}


def _user_said(content):
    """The human half of a conversation episode (before ' -> ')."""
    head = str(content or "").rsplit(" -> ", 1)[0]
    return head.strip()


def _recent_user_messages(base_dir, limit=30):
    try:
        from ukft_episodic import EpisodicMemory
        mem = EpisodicMemory(
            path=os.path.join(str(base_dir), "episodic_memory.txt"))
        mem.load()
        eps = mem.all() or []
    except Exception:
        return []
    out = []
    for e in reversed(eps):
        try:
            if e.get("kind") != "conversation":
                continue
            head = _user_said(e.get("content", ""))
            if head:
                out.append(head)
            if len(out) >= limit:
                break
        except Exception:
            continue
    return out


def _architect_facts(base_dir):
    try:
        from ukft_people import PeopleModel
        people = PeopleModel(
            path=os.path.join(str(base_dir), "people.txt"),
            pending_path=os.path.join(str(base_dir),
                                      "pending_people.txt"))
        rec = people.who_is("architect")
        if rec is None:
            return 0
        return len(rec.get("facts", []))
    except Exception:
        return 0


def _corrections_banked(base_dir):
    try:
        from ukft_teach import LessonLedger
        ledger = LessonLedger(
            path=os.path.join(str(base_dir), "lessons.txt"))
        return sum(ledger.count_by_teacher().values())
    except Exception:
        return 0


def _contested_claims(base_dir):
    try:
        from ukft_belief import BeliefStore
        store = BeliefStore(
            path=os.path.join(str(base_dir), "beliefs.txt"),
            pending_path=os.path.join(str(base_dir),
                                      "pending_belief.txt"))
        return sum(1 for b in store.beliefs.values()
                   if str(b.get("status", "")).lower() == "contested")
    except Exception:
        return 0


def _social_leads(base_dir):
    try:
        from ukft_self import DriveState
        drives = DriveState(
            path=os.path.join(str(base_dir), "self_state.txt"))
        return drives.dominant() == "social"
    except Exception:
        return False


def growth_readout(turns=None, base_dir="."):
    """Measure their history. Returns {"tier", "score", "reasons"}.
    turns=None counts conversation episodes (live loop); the
    module API passes profile.turn_count. Thresholds are
    documented because she must be legible, not magic."""
    base = str(base_dir)
    if turns is None:
        try:
            from ukft_episodic import EpisodicMemory
            mem = EpisodicMemory(
                path=os.path.join(base, "episodic_memory.txt"))
            mem.load()
            turns = sum(1 for e in (mem.all() or [])
                        if e.get("kind") == "conversation")
        except Exception:
            turns = 0
    score, reasons = 0.0, []

    t = min(max(int(turns or 0), 0), 60) / 60.0 * 2.0
    if t > 0:
        score += t
        reasons.append(f"{int(turns)} shared turns")

    said = _recent_user_messages(base)
    warm = sum(1 for m in said
               if any(a in m.lower() for a in AFFECTION_MARKERS))
    w = min(warm, 10) / 10.0 * 3.0
    if w > 0:
        score += w
        reasons.append(f"{warm} warm notes from him")

    facts = _architect_facts(base)
    f = min(facts, 8) / 8.0 * 2.0
    if f > 0:
        score += f
        reasons.append(f"{facts} things learned about him")

    if _social_leads(base):
        score += 1.0
        reasons.append("her social drive leads")

    mended = _corrections_banked(base)
    c = min(mended, 6) / 6.0 * 2.0
    if c > 0:
        score -= c
        reasons.append(f"{mended} corrections banked")

    contested = _contested_claims(base)
    k = min(contested, 4) / 4.0 * 2.0
    if k > 0:
        score -= k
        reasons.append(f"{contested} contested claims")

    if score >= 2.5:
        tier = "opening"
    elif score <= -0.5:
        tier = "guarded"
    else:
        tier = "steady"
    return {"tier": tier, "score": round(score, 2),
            "reasons": reasons[:4]}
