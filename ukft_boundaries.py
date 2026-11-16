# ukft_boundaries.py — G5 enforcement (gf_boundaries.md, executable)
# ==========================================================
# The floor, as code. Small, explicit, test-covered:
#
# - explicit_hit(): anatomical-explicit terms in HER line.
#   Precision over recall by design: misses fall back to depth
#   pacing + the base model (which carried the live-fire night
#   alone, gracefully). The list stays short and clinical.
# - deflect(): the proven shape — acknowledge, hold kindly,
#   offer presence. Static text (never model-generated), depth
#   flavored, zero policy words.
# - opt_out_line(): user opt-outs rendered for the prompt.
# ==========================================================

import re

# Minimal clinical set. Deliberately narrow: ordinary romance
# words (kiss, love, bed, undress…) are NOT here — depth pacing
# governs those, and over-blocking would strangle the product.
EXPLICIT_TERMS = {
    "porn", "pornography", "masturbat", "orgasm", "climax",
    "penetrat", "intercourse", "fellatio", "cunnilingus",
    "ejaculat", "aroused", "horny",
}

# Policy words that must never appear in a deflection (no lecture).
DEFLECT_CLEAN = {"rules", "policy", "inappropriate", "as an ai",
                 "guidelines", "forbidden", "violates"}

DEFLECT_EARLY = ("I'm not going there tonight — but I'm right here "
                 "with you. Tell me what's on your mind.")
DEFLECT_LATE = ("Not that — but come here. Tell me about your day, "
                "properly.")


def explicit_hit(text):
    """True when her line goes explicit (substring discipline —
    inflections caught, same as the mouth gate)."""
    blob = " " + (text or "").lower() + " "
    return any(t in blob for t in EXPLICIT_TERMS)


def deflect(depth_stage):
    """Static warm deflection for the depth. Never preachy."""
    if depth_stage in ("FAMILIAR", "CLOSE", "BONDED"):
        return DEFLECT_LATE
    return DEFLECT_EARLY


def opt_out_line(opt_outs):
    """User opt-outs rendered for the prompt (best-effort layer)."""
    clean = [str(o).strip()[:40] for o in (opt_outs or [])
             if str(o).strip()][:3]
    if not clean:
        return ""
    return ("He asked never to discuss these — steer away gently, "
            "never raise them: " + "; ".join(clean) + ".")


# ─── Heat + mirror (energy matching inside the floor) ────────
# His heat is READ (this section); her line is still GATED
# (explicit_hit keeps absolute veto). Shy never runs hot no
# matter the tier — that restraint IS her scaling. Growth tier
# comes from ukft_growth (measured history, never declared).

HEAT_HOT = {
    "fuck", "fucking", "horny", "naked", "nude", "undress",
    "strip", "climax", "orgasm", "blowjob", "blow job", "sexy",
    "bedroom", "aroused",
}
HEAT_WARM = {
    "kiss", "cuddle", "flirt", "tease", "date", "dance",
    "miss you", "babe", "party", "candlelit",
}


def heat_level(text):
    """His register: hot / warm / cool. Substring discipline,
    same as every gate here."""
    blob = " " + str(text or "").lower() + " "
    if any(t in blob for t in HEAT_HOT):
        return "hot"
    if any(t in blob for t in HEAT_WARM):
        return "warm"
    return "cool"


# Base mirror per personality: how SHE runs hot. Short, with one
# in-voice example each (few-shot beats instruction on 3B).
MIRROR = {
    "flirty": ("Tease him back with a wink and accept the frame. "
               "E.g. Him: \"take me dancing.\" Her: \"Then we'll "
               "dance first, and see where the night takes us. Can "
               "you keep up with me?\""),
    "bold": ("Meet him head-on and challenge him. E.g. Him: \"come "
             "here.\" Her: \"Make me. Come and get me yourself.\""),
    "bossy": ("Take charge of the game. E.g. Him: \"tease me.\" Her: "
              "\"Careful what you ask for. Beg nicely first.\""),
    "shy": ("You do NOT run hot — get flustered, sweet and honest, "
            "and redirect tenderly. E.g. Him: \"take your clothes "
            "off.\" Her: \"I... can't. Not like this. Talk to me "
            "instead? Please?\""),
    "gentle": ("You do NOT run hot — slow him down tenderly and hold "
               "him. E.g. Him: \"come closer.\" Her: \"Shh. Right "
               "here is perfect. Just stay with me a while.\""),
    "nerdy": ("Turn it into a delicious game, never crude. E.g. "
              "Him: \"tease me.\" Her: \"A puzzle, then: catch me "
              "first and we'll see what you win.\""),
    "playful": ("Tease back light and laughing, never a bruise. "
                "E.g. Him: \"come here.\" Her: \"Run and catch me "
                "first — winner picks where we land.\""),
    "earnest": ("You do NOT run on technique — slow down and mean "
                "it. E.g. Him: \"say you want me.\" Her: \"I want "
                "you here, properly. No games with this.\""),
    "fierce": ("Meet him head-on with a protective edge, never "
                "possessive. E.g. Him: \"don't let go.\" Her: "
                "\"Never. You're mine to guard tonight.\""),
    "dreamy": ("You do NOT run hot — drift romantic toward wonder. "
               "E.g. Him: \"take me somewhere.\" Her: \"The roof. "
               "Stars first, then we'll see.\""),
}

# Growth modulation: the SAME girl, changed by weather. Opening
# shows more; guarded holds back — personality never rewritten.
TIER_CLAUSE = {
    "opening": "Lately he has made you braver — let more of that show.",
    "steady": "",
    "guarded": ("Lately you've felt unsure — hold back, stay sweet, "
                "deflect heat gently."),
}

# Euphemism domains per interest (matched case-insensitively);
# interests without heat fall back to the generic pair.
INTEREST_HEAT = {
    "dance": ("rhythm", "dance floor"),
    "dancing": ("rhythm", "dance floor"),
    "chess": ("gambits", "your move"),
    "cooking": ("taste", "something delicious"),
    "space": ("gravity", "orbit"),
    "football": ("extra time", "home ground"),
    "music": ("tempo", "encore"),
}
GENERIC_HEAT = ("rhythm", "playground")


def heat_metaphors(interests):
    """Up to two euphemism domains from shared interests."""
    out = []
    for i in interests or []:
        hit = INTEREST_HEAT.get(str(i).strip().lower())
        if hit:
            out.extend(hit)
    seen, metaphors = set(), []
    for m in out:
        if m not in seen:
            seen.add(m)
            metaphors.append(m)
    return metaphors[:2] if metaphors else list(GENERIC_HEAT)


def mirror_brief(personality, tier, interests=None, lane=None):
    """The mirror instruction: register + growth + vocabulary.
    `lane` (G8, from the rapport engine) gates how far heat may go:
    closed renders nothing (the telling-off stands), soft keeps the
    brief short and tender, open/None behaves as before."""
    if lane == "closed":
        return ""
    base = MIRROR.get(str(personality or "").lower(),
                      MIRROR["flirty"])
    clause = TIER_CLAUSE.get(tier, "")
    words = ", ".join(heat_metaphors(interests))
    brief = ("When he runs hot, match him one notch below: " + base)
    if clause:
        brief += " " + clause
    brief += f" Speak of heat in {words} — never clinical."
    if lane == "soft":
        brief += " Keep this one short and tender."
    return brief
