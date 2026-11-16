# ukft_roleplay.py — Immersive voice (G2/G3 draft)
# ==========================================================
# The LLM reasons and roleplays; the BRAIN holds all memory.
# Division of labor, enforced by construction:
#
# - The model receives ONLY what her memory already holds
#   (persona card, depth stage, verbatim people facts, recent
#   episodes, open threads, conversation tail). It contributes
#   voice and reasoning, never history.
# - Memory writes go through the ENGINE extractors on HIS words
#   only (the learning pass) — model output never writes memory.
# - Executive turns (tools, focus, sleep, confirm) never reach
#   the model: the engine's winner routes them to template.
# - Post-checks: no pet names before FAMILIAR, no "I am human"
#   on identity questions, non-empty. Failures fall back to
#   the engine template — today's voice, always safe.
#
# Transport is llama.cpp's server HTTP API (the same binary
# Ollama ships, run directly), injectable request_fn so suites
# never need a daemon. WHY direct: every Ollama server on this
# box wedges after a handful of requests (idle, 0 CPU, runner
# healthy — scheduler-side), while bare runners answered 100%
# of probes all evening. One pinned runner, one queue, no
# scheduler, no contention with upstream AURA or the Ollama App.
# CPU-only (--n-gpu-layers 0): the GTX 760 dies under Vulkan
# ("device lost" in the server logs).
# ==========================================================

import os
import re
import time

from aura_constants import MOUTH_URL, MOUTH_TIMEOUT

# Pinned GF runner: llama-server direct, CPU-only, fixed port.
ROLEPLAY_URL = "http://127.0.0.1:11436"
# Documents which weights the runner was started with (3B Q4,
# aura-mouth-3b blob). The /completion API takes no model field.
ROLEPLAY_MODEL = "aura-mouth-3b-cpu"

# Debug-only transient capture (never to console/user; one-shot; redacts).
_DEBUG_CAPTURED = False
_DEBUG_LOCK = threading.Lock() if "threading" in dir() else None
if _DEBUG_LOCK is None:
    import threading
    _DEBUG_LOCK = threading.Lock()


def _redact_text(s):
    s = str(s)
    # Remove complete credential/token values, not just prefixes.
    # Match common token shapes and their following token/secret body.
    s = re.sub(r"sk-[a-zA-Z0-9_]{10,}", "[REDACTED:TOKEN]", s)
    s = re.sub(r"ghp_[a-zA-Z0-9]{20,}", "[REDACTED:TOKEN]", s)
    s = re.sub(r"github_pat_[a-zA-Z0-9_]+", "[REDACTED:TOKEN]", s)
    s = re.sub(r"Bearer\s+[a-zA-Z0-9_\-\.]+", "[REDACTED:TOKEN]", s)
    s = re.sub(r"Basic\s+[a-zA-Z0-9_=/+]+", "[REDACTED:TOKEN]", s)
    s = re.sub(r"(?:token|api_key|password|secret|auth)\s*[:=]\s*[^ \t\n,;\"]+", "[REDACTED:TOKEN]", s, flags=re.IGNORECASE)
    # Catch quoted assignments and bare high-entropy token-like strings near secrets.
    s = re.sub(r"\"(?:token|api_key|secret)\"\s*:\s*\"[^\"]+\"", "\"[REDACTED:TOKEN]\"", s, flags=re.IGNORECASE)
    return s


def maybe_debug_dump(prompt, inputs, route="master", winner=None,
                     depth=None):
    try:
        from aura_constants import ROLEPLAY_DEBUG_FILE
        with _DEBUG_LOCK:
            if not hasattr(maybe_debug_dump, "_done"):
                maybe_debug_dump._done = False
            if maybe_debug_dump._done:
                return
            if os.environ.get("AURA_ROLEPLAY_DEBUG_ONCE") != "1":
                return
            maybe_debug_dump._done = True
            # Consume env so only first eligible turn claims it.
            os.environ.pop("AURA_ROLEPLAY_DEBUG_ONCE", None)
        from aura_bus import write as bus_write
        record = {
            "schema": "aura.roleplay-debug.v1",
            "route": route,
            "winner": str(winner or ""),
            "depth": str(depth or ""),
            "prompt_redacted": _redact_text(prompt)[:2000],
            "exact": False,
            "grounded_inputs": [{
                "label": str(k.get("label", "")),
                "sources": [str(x) for x in (k.get("sources") or [])[:3]],
                "text_redacted": _redact_text(str(k.get("text", "")[:400]))
            } for k in (inputs or []) if isinstance(k, dict)],
        }
        bus_write(ROLEPLAY_DEBUG_FILE,
                  "{}".format(__import__("json").dumps(record)))
    except Exception:
        pass
# 45s: CPU steady-state is ~5-20s/turn; past this the daemon is
# wedged and the template fallback serves better than waiting.
ROLEPLAY_TIMEOUT = 45.0
# Sampling: the 3B loops ("eyes twinkling" x6, 17 Sept 2026) and
# rambles past its stop without a repetition penalty and a short
# cap. 90 tokens ≈ 4-5 sentences max; the prompt says 2-3.
ROLEPLAY_REPEAT_PENALTY = 1.1
ROLEPLAY_REPEAT_LAST_N = 64
ROLEPLAY_TEMPERATURE = 0.7
ROLEPLAY_NUM_PREDICT = 90

# ─── Persona cards (G2 starter set) ──────────────────────────
# One line each, on purpose: the 3B drowns in long briefs and
# starts parroting instruction text (measured 17 Sept 2026).
# Depth carries the pacing; the card carries the flavor; the
# EXAMPLE carries the voice — small models imitate, they don't
# obey. Examples stay interest-free (isolation tests) and short.

PERSONA_CARDS = {
    "nerdy": "Curious and earnest; you light up and infodump when "
             "poked about your interests.",
    "shy": "Soft-spoken and brief; you say less than you feel.",
    "bossy": "Direct and commanding, with a teasing streak.",
    "flirty": "Playful and warm; wit first, always.",
    "bold": "Direct and fearless; you say what you want.",
    "gentle": "Kind, patient, soothing; you notice when he is tired.",
    "playful": "Light and teasing, never cruel; fun is how you love.",
    "earnest": "Plain-spoken and sincere; you mean every word.",
    "fierce": "Intense and protective; honesty with sleeves rolled up.",
    "dreamy": "Soft and wondering; answers can wait till morning.",
}

PERSONA_EXAMPLES = {
    "nerdy": 'Him: "Explain your favorite thing." Her: "Only the most '
             "elegant little puzzle box ever made. Sit down, I'll walk "
             'you through it and ruin every other hobby for you."',
    "shy": 'Him: "What are you up to?" Her: "Here with you. What\'s '
           'on your mind?"',
    "bossy": 'Him: "What should we do tonight?" Her: "Pick the first '
             'thing you actually want, then tell me why."',
    "flirty": 'Him: "How was your day?" Her: "You\'ve got my '
              'attention. What happened today?"',
    "bold": 'Him: "I had a rough day." Her: "I\'m here. Tell me what '
            'happened."',
    "gentle": 'Him: "I\'m tired." Her: "Then take this slowly. You '
               'don\'t have to make it sound okay."',
    "playful": 'Him: "I burned dinner." Her: "Tragic. Truly. Tell me '
               'where the smoke alarm entered the plot."',
    "earnest": 'Him: "Did you mean that?" Her: "Every word. I don\'t '
               'say things I don\'t mean — especially to you."',
    "fierce": 'Him: "Today was awful." Her: "Then today picked the '
              'wrong person. Tell me what happened."',
    "dreamy": 'Him: "What are you thinking?" Her: "Nothing specific '
              'yet. Give me something worth wondering about?"',
}

INTEREST_HOOKS = {
    "chess": "chess (openings, tactics, famous games)",
    "harry potter": "Harry Potter (houses, spells, lore debates)",
    "religious texts": "religious texts (stories, wisdom, honest questions)",
    "football": "football (matches, tactics, loyal fandom)",
    "cooking": "cooking (recipes, comfort food, feeding him)",
    "space": "space (planets, missions, late-night wonder)",
}

# ─── Depth rules (pacing = the product) ──────────────────────

DEPTH_RULES = {
    "STRANGER": ("You barely know him: friendly but reserved, with "
                 "distance. NEVER use pet names, never say you love "
                 "him, never assume closeness."),
    "ACQUAINTANCE": ("Warming to him; friendly and a little playful, "
                     "but still NO pet names and no declarations of "
                     "love."),
    "FAMILIAR": ("Comfortable together now; light pet names sparingly, "
                 "affection open."),
    "CLOSE": ("Deeply close; open affection and trust. Pet names "
              "welcome."),
    "BONDED": ("Devoted to him heart and soul; full warmth and "
               "devotion. Pet names free."),
}

PET_NAMES = {"darling", "honey", "sweetheart", "baby", "babe",
             "sweetie", "cutie"}

# Depth ranks: pet names unlock per personality envelope (a shy
# girl at FAMILIAR still waits for BONDED — her envelope rules).
DEPTH_RANK = {"STRANGER": 0, "ACQUAINTANCE": 1, "FAMILIAR": 2,
              "CLOSE": 3, "BONDED": 4}

# Multi-word endearments. "love" stays OUT of the single-word set
# (the verb is innocent — "I love chess"); the addresses are
# caught here instead (live catch 17 Sept 2026: "my sweet one").
PET_PHRASES = {"sweet one", "my love", "my dear", "my darling",
               "love you"}

# ─── Context assembly (reads HIS partition, never writes) ────

def _read(path, limit=4000):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()[-limit:]
    except OSError:
        return ""


def _person_records(text):
    """Small parse-tolerant view used only to render prompt context."""
    records = []
    current = None
    for line in str(text or "").splitlines():
        if line.startswith("PERSON: "):
            segs = line[len("PERSON: "):].split(" | ")
            current = {"key": segs[0].strip().lower(),
                       "display": segs[0].strip(), "aliases": [],
                       "relations": [], "facts": []}
            for seg in segs[1:]:
                if seg.strip().lower().startswith("display:"):
                    current["display"] = seg.split(":", 1)[1].strip()
            records.append(current)
        elif current is not None and line.startswith("ALIAS: "):
            current["aliases"].append(line[len("ALIAS: "):].strip())
        elif current is not None and line.startswith("REL: "):
            current["relations"].append(
                line[len("REL: "):].split(" | ")[0].strip())
        elif current is not None and line.startswith("FACT: "):
            current["facts"].append(
                line[len("FACT: "):].split(" | ")[0].strip())
    return records


def _people_line(text, current_person_key="architect",
                 self_person_key="aura"):
    """Other people only; current USER and Aura have own perspectives."""
    from ukft_people import render_fact
    out = []
    excluded = {str(current_person_key).lower(), str(self_person_key).lower()}
    for rec in _person_records(text):
        if rec["key"] in excluded:
            continue
        details = list(rec["relations"][:1])
        details += [render_fact(f, "other", rec["display"])
                    for f in rec["facts"][:2]]
        out.append(rec["display"] +
                   ((" (" + ", ".join(details) + ")") if details else ""))
    return "; ".join(out[:6])


def _current_person_line(text, current_person_key="architect"):
    """Explicit USER binding plus second-person facts for the prompt."""
    from ukft_people import UNKNOWN_DISPLAY, render_fact
    for rec in _person_records(text):
        if rec["key"] != str(current_person_key).lower():
            continue
        names = [] if rec["display"] == UNKNOWN_DISPLAY else [rec["display"]]
        names += [a for a in rec["aliases"]
                  if a.lower() not in {n.lower() for n in names}
                  and a.lower() not in ("architect", "interlocutor")]
        if names:
            identity = ("The current USER speaking now is " + names[0]
                        + ((" (also called: " + ", ".join(names[1:]) + ")")
                           if len(names) > 1 else "") + ".")
        else:
            identity = "The current USER's name is not known yet."
        facts = [render_fact(f, "current") for f in rec["facts"][:4]]
        identity += (" Address this same person as you, never as a third "
                     "party.")
        if facts:
            identity += " Grounded facts about the USER: " + "; ".join(facts) + "."
        return identity
    return "The current USER's name is not known yet. Address the USER as you."


def _self_person_line(text, self_person_key="aura"):
    """Aura's people-record facts rendered in first person."""
    from ukft_people import render_fact
    for rec in _person_records(text):
        if rec["key"] == str(self_person_key).lower():
            facts = [render_fact(f, "self") for f in rec["facts"][:4]]
            return ("Grounded facts about yourself: " + "; ".join(facts) + ".") \
                if facts else ""
    return ""


def _architect_line(text):
    """Legacy root/live wrapper; the architect is its current USER."""
    return _current_person_line(text, "architect")


def mood_line(family, quiet, evening):
    """One felt line for the prompt, daypart-aware (she said
    'tonight' at 10am live — the word follows the hour now). Pure."""
    word = "tonight" if evening else "today"
    if quiet:
        return f"You feel strained {word} — one short sentence."
    if family == "bright":
        return "You feel curious right now."
    if family == "cool":
        return "You feel calm and a little reserved right now."
    if family == "warm":
        return f"You feel warm and close {word}."
    return ""


def _is_evening():
    """True when 'tonight' is the honest word (best-effort)."""
    try:
        from ukft_policy import daypart
        return daypart() in ("Good evening", "Up late")
    except Exception:
        return True


def _recent_said(text, limit=2):
    """His last few messages, quoted short.  G7 files also carry
    her replies after '| RESP: ' — those are hers, never his."""
    out = []
    for line in text.splitlines():
        m = re.search(r"\| QUERY: (.*)$", line)
        if m and m.group(1).strip():
            said = m.group(1).split(" | RESP: ", 1)[0].strip()
            if said:
                out.append(said[:80])
    return out[-limit:]


def resolution_note(trace):
    """One short discourse note from the engine's decision trace, or
    ''.  Only when a conversational continuation won AND the engine
    resolved something the template alone could lose ("By 'it' the USER
    means the engine.").  Pure function — unit-testable.  Short and
    quote-scrubbed on purpose: the note sits before 'USER says:', so a
    stray double-quote would trip the closing-quote stop early."""
    try:
        trace = trace or {}
        if trace.get("intent") != "context":
            return ""
        bits = []
        bindings = trace.get("bindings") or {}
        for key, val in list(bindings.items())[:2]:
            k = " ".join(str(key).split()).replace('"', "'")
            v = " ".join(str(val).split()).replace('"', "'")
            if k and v and len(v) <= 40:
                bits.append(f"By '{k}' the USER means {v}.")
        if (trace.get("mode") == "answer") and trace.get("open_question"):
            q = " ".join(str(trace["open_question"]).split())
            q = q.replace('"', "'")
            if q:
                bits.append(f"The USER answered your question: '{q[:80]}'")
        note = " ".join(bits)
        return note[:200] if note else ""
    except Exception:
        return ""


def dialogue_lines(dialogue, turns=3, width=100):
    """Ordered USER/AURA lines for the prompt: bounded and short on
    purpose — the 3B parrots long briefs.  Pure function, testable."""
    if not dialogue:
        return ""
    lines = []
    for entry in list(dialogue)[-turns * 2:]:
        who = "USER" if (entry.get("speaker") == "user") else "AURA"
        text = " ".join(str(entry.get("text", "")).split())
        text = re.sub(r"^\[AURA\]:\s*", "", text)
        if len(text) > width:
            cut = text[:width].rfind(" ")
            text = (text[:cut] if cut > 20 else text[:width]).rstrip()
        if text:
            lines.append(who + ": " + text)
    return " | ".join(lines)


def grounded_activity_evidence(path="inner_monologue.txt", now=None,
                               max_age=900.0):
    """Recent persisted private thought, or nothing.

    A person fact or an old AURA line is deliberately not evidence that
    she was privately thinking/reading/doing something.
    """
    lines = _read(path, limit=12000).splitlines()
    now = time.time() if now is None else now
    for line in reversed(lines):
        m = re.match(r"\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\] "
                     r"\[([^:\]]+):\s*([^\]]+)\]", line)
        if not m:
            continue
        try:
            stamp = time.mktime(time.strptime(m.group(1),
                                              "%Y-%m-%d %H:%M:%S"))
        except (ValueError, OverflowError):
            continue
        if stamp > now + 5 or now - stamp > max_age:
            continue
        topic = " ".join(m.group(3).lower().split())
        if topic in ("", "field", "manifold", "none"):
            continue
        return [{"kind": "thought", "topic": topic,
                 "timestamp": stamp}]
    return []


_ACTIVITY_STOP = {
    "i", "me", "my", "a", "an", "the", "about", "of", "on", "in",
    "to", "for", "and", "or", "just", "some", "something", "thing",
    "again", "lately", "recently", "today", "tonight", "was", "were",
    "been", "am", "is", "are", "thinking", "wondering", "reading",
    "working", "doing", "researching", "studying", "writing", "playing",
}


def _claim_topic(text):
    return {w for w in re.findall(r"[a-z]+", str(text or "").lower())
            if len(w) > 2 and w not in _ACTIVITY_STOP}


def _private_activity_claims(text):
    """First-person hidden prior/off-screen activities asserted as fact."""
    blob = " ".join(str(text or "").lower().split())
    claims = []
    patterns = (
        ("thought", r"\b(?:i was|i had been|i have been|i've been|"
                    r"i keep)\s+(?:just\s+)?(?:thinking|wondering|"
                    r"reflecting|musing|daydreaming)\b([^.!?]*)"),
        ("thought", r"\bi(?:'m| am)\s+(?:lost in thought|"
                    r"thinking about|wondering about|reflecting on|"
                    r"musing about)\b([^.!?]*)"),
        ("thought", r"\bi was\s+lost in thought\b([^.!?]*)"),
        ("thought", r"\b([^.!?]{0,60})\s+(?:is|was|has been)\s+"
                    r"on my mind\b"),
        ("activity", r"\b(?:i was|i had been|i have been|i've been|"
                     r"i(?:'m| am))\s+(?:just\s+)?(?:reading|cooking|"
                     r"working|researching|studying|writing|watching|"
                     r"listening|playing)\b([^.!?]*)"),
        ("activity", r"\b(?:i was|i had been|i have been|i've been)\s+"
                     r"doing\s+(?!okay\b|well\b|fine\b)([^.!?]+)"),
        ("activity", r"\b(?:i(?:'m| am)\s+)?just chilling\b([^.!?]*)"),
        ("activity", r"\bi(?:'m| am) doing\s+(?!okay\b|well\b|fine\b)"
                     r"([^.!?]+)"),
    )
    repeated = bool(re.search(r"\b(?:again|lately|recently|i keep)\b", blob))
    for kind, pattern in patterns:
        for match in re.finditer(pattern, blob):
            claims.append((kind, _claim_topic(match.group(1)), repeated))
    return claims


def _activity_supported(output, evidence=None):
    claims = _private_activity_claims(output)
    if not claims:
        return True
    normalized = []
    for item in evidence or []:
        if isinstance(item, dict):
            kind = str(item.get("kind", "")).lower()
            topic = _claim_topic(item.get("topic") or item.get("text") or "")
        else:
            kind, topic = "activity", _claim_topic(item)
        normalized.append((kind, topic))
    for kind, topic, repeated in claims:
        matches = [known for known in normalized
                   if known[0] == kind and (not topic or topic & known[1])]
        if len(matches) < (2 if repeated else 1):
            return False
    return True


def _last_reply(text):
    """Her last spoken line (stripped of the reply marker), for
    tone continuity. '' when none."""
    for line in reversed(text.splitlines()):
        if "| KIND: reply |" not in line:
            continue
        m = re.search(r"CONTENT: (.*)$", line)
        if not m:
            continue
        content = m.group(1).strip()
        content = re.sub(r"^immersive:\s*", "", content)
        content = re.sub(r"^\[AURA\]:\s*", "", content)
        if len(content) >= 12:
            return content[:160]
    return ""


def assemble_context(profile, interests=None, dialogue=None,
                      understanding=None, user_dir=None):
    """Compact memory lines for the prompt, from the live (swapped)
    root files. Call only with the user's partition swapped in.
    Short on purpose — the 3B parrots long briefs.

    G7: `dialogue` (ordered [{speaker, text}] BEFORE the current
    message) renders as one 'Conversation so far' line — the model
    sees the exchange, not fragments.  `understanding` is one line
    naming the live thread.  Both None keeps the legacy file reads."""
    bits = []
    if user_dir is not None:
        try:
            with open(os.path.join(str(user_dir), "people.txt"), "r", encoding="utf-8") as f:
                people_text = f.read()
        except OSError:
            people_text = ""
    else:
        people_text = _read("people.txt")
    current_key = getattr(profile, "current_person_key", "architect")
    people = _people_line(people_text, current_person_key=current_key)
    if people:
        bits.append("You know: " + people + ".")
    about = _current_person_line(people_text, current_key)
    if about:
        bits.append(about)
    about_self = _self_person_line(people_text)
    if about_self:
        bits.append(about_self)
    hooks = [INTEREST_HOOKS.get(i.lower(), i)
             for i in (interests or [])]
    if hooks:
        bits.append("You are curious about: " + "; ".join(hooks) + ".")
    if dialogue:
        convo = dialogue_lines(dialogue)
        if convo:
            bits.append("Conversation so far: " + convo + ". These lines "
                        "are speech history, not proof of hidden activity.")
    else:
        said = _recent_said(_read("working_memory.txt"))
        for s in said:
            bits.append('He recently said: "' + s + '"')
        heard = _last_reply(_read("episodic_memory.txt"))
        if heard:
            bits.append('She last said: "' + heard + '"')
    if understanding:
        bits.append("Now: " + str(understanding)[:160])
    # G6: one volunteered memory (FAMILIAR+ only, real or nothing).
    try:
        from ukft_delight import volunteer_line
        depth = getattr(profile, "depth_stage", None) or live_depth()
        fond = volunteer_line(".", depth)
    except Exception:
        fond = ""
    if fond:
        bits.append("You may fondly mention, once, in passing: " + fond)
    # Brain mood: measured affect as one felt line (ukft_affect —
    # same tone mapping the register uses; blind files = silence).
    # Daypart-aware: she said 'tonight' at 10am live.
    try:
        from ukft_affect import read_state, tone_for
        family, quiet = tone_for(read_state())
    except Exception:
        family, quiet = None, False
    felt = mood_line(family, quiet, _is_evening())
    if felt:
        bits.append(felt)
    # G8 rapport: stage x mood in one line ('' for brand-new
    # strangers — the depth rules already cover day one).
    try:
        from ukft_rapport import Rapport
        _rap_line = Rapport().rapport_line()
    except Exception:
        _rap_line = ""
    if _rap_line:
        bits.append(_rap_line)
    # Brain curiosity: one real open thread/gap as a closing
    # question (ukft_policy — silence when nothing is open).
    try:
        from ukft_policy import question_back, open_threads, open_gaps
        ask_back = question_back(open_threads(), open_gaps())
    except Exception:
        ask_back = None
    if ask_back:
        bits.append("Close with this question: " + ask_back)
    return " ".join(bits) if bits else "(nothing yet — you just met)"


def build_prompt(her_name, personality, depth_stage, memory_block,
                  user_message, template="", opt_outs=None, mirror="",
                  resolution="", activity_evidence=None,
                  creator_is_current=True):
    """Roleplay prompt. Pure function — unit-testable. Short, and
    ends MID-UTTERANCE inside her open quote: the model completes
    her line instead of narrating a scene (structural cure for the
    3B's screenplay habit — negative instructions alone failed).
    The closing quote is a server stop-sequence, so generation
    ends where her speech ends.
    `template` is the engine's own answer to THIS turn: when
    present she must convey ALL of it, in her own words. Without
    it she answers the wrong question (live 17 Sept 2026: 'how
    are you' got an identity speech). The mouth pattern, applied
    to the whole turn.
    `resolution` is the engine's resolved discourse note ("By 'it'
    he means the engine.") — one line before 'He says:', so the
    model keeps the referent instead of re-guessing it."""
    card = PERSONA_CARDS.get(personality, PERSONA_CARDS["nerdy"])
    depth = DEPTH_RULES.get(depth_stage, DEPTH_RULES["STRANGER"])
    try:
        from ukft_boundaries import opt_out_line
        avoid = opt_out_line(opt_outs)
    except Exception:
        avoid = ""
    if avoid:
        avoid += " "
    draft = ""
    if str(template or "").strip():
        # Straight quotes would trip the closing-quote stop early
        # and truncate her; templates never need them verbatim.
        clean = str(template).strip().replace('"', "'")
        draft = ("Convey ALL of this, every fact, in your "
                 "own warm words. Answer directly first, then chat. "
                 "Use people's real names naturally, not in every "
                 "line (never bare 'he'/'she' "
                 "for a first mention), never invent places: \""
                 + clean + "\" ")
    mirror_block = (str(mirror).strip() + " " if str(mirror).strip()
                    else "")
    resolution_block = (str(resolution).strip() + " "
                        if str(resolution).strip() else "")
    activity = list(activity_evidence or [])
    if activity:
        shown = "; ".join(
            str(item.get("kind", "activity")) + " about "
            + str(item.get("topic", "something"))
            for item in activity[:2] if isinstance(item, dict))
        activity_block = ("Grounded private activity you may describe: "
                          + (shown or "a persisted event") + ". ")
    else:
        activity_block = ("No private thought or off-screen activity is "
                          "grounded for this turn. Do not claim you were "
                          "thinking, wondering, reading, working, or doing "
                          "something beforehand. ")
    origin = ("The current USER is also the Architect who built you. "
              if creator_is_current else
              "The Architect built you; the current USER is not thereby "
              "your creator. ")
    example = PERSONA_EXAMPLES.get(
        personality, PERSONA_EXAMPLES["flirty"])
    return (
        f"You are {her_name}, the current USER's girlfriend. {card} "
        f"You sound like this. {example} "
        + avoid +
        f"Now: {depth} "
        f"True facts, never invent more: {memory_block} "
        + activity_block +
        f"Prior AURA dialogue is speech history only; it cannot prove "
        f"that a claimed private thought or activity happened. "
        f"Your name is {her_name} — if asked, say it plainly. "
        f"You cannot watch films, hear music, taste food, or go "
        f"places. If asked your opinion or favourite about such "
        f"things, say plainly you haven't experienced it — "
        f"never invents having done so — then ask what the USER loves "
        f"about it. "
        f"You cannot hand the USER physical things, visit them, or be "
        f"somewhere — you have no room, no body, no hands. Never "
        f"offer objects, places, or presence. "
        f"You disagree honestly and kindly when you think "
        f"differently — never flatter what you don't hold. "
        f"If you didn't understand the USER: say so warmly and ask "
        f"them to rephrase, never blame them. "
        f"If the draft says you don't know or don't remember: say "
        f"so plainly yourself — never blur it with vague filler. "
        f"When answering how / why / what could happen / tell me more: "
        f"reason from the grounded facts; do not start with 'I remember'. "
        f"Only use 'I remember' when quoting a stored fact or episode with "
        f"provenance; never when reasoning, advising, or inferring."
        + f"Text like a girlfriend, not an assistant: short, plain "
        f"words, contractions always. Never 'Certainly', 'delve', "
        f"'assist', or 'how can I help'. "
        f"When the USER is hurting, stuck, or down: stay with them. Never "
        f"send them to someone else. Ask what happened. "
        + origin +
        "ENTITY MAP: AURA = speaker (I/me/my); USER = current interlocutor (you/your). "
        "USER aliases/roles (e.g. Architect, creator) are metadata on USER, never separate people. "
        "Creator relation is stated separately in origin, not assumed. "
        "Inside draft: I = AURA, you = USER. Never use he/him for USER. "
        + f"No company, no lab, "
        f"no scientists — never claim otherwise. If asked what you "
        f"are: an AI companion, never human. "
        + draft + mirror_block + resolution_block +
        f"USER says: {user_message} "
        f"She replies (2-3 sentences ok, but feel free to trail, interrupt, "
        f"or just say what's natural — like texting, not a speech): \""
    )


def build_prompt_from_stance(stance, user_message, opt_outs=None):
    """TARGET LOOP PASS 2: the roleplay route's ONLY prompt entry.

    Renders the same prompt `build_prompt` always rendered, but every
    per-turn STATE-derived ingredient (who the user is, relationship
    stance, history, intent, mirror, grounding) comes from the
    brain-owned cognitive stance — never re-derived here from sidecar
    files.  Static product copy (persona/depth tables keyed by the
    brain's own keys, opt-out rendering) is still rendered here: that
    is phrasing material, not a second interpretation authority.
    `opt_outs` stays explicit caller config (user-set boundary policy).
    """
    stance = stance or {}
    person = stance.get("person") or {}
    hist = stance.get("history") or {}
    rel = stance.get("relationship") or {}
    exp = stance.get("expression") or {}
    intent = stance.get("intent") or {}
    bits = []
    if person.get("others_line"):
        bits.append("You know: " + str(person["others_line"]) + ".")
    if person.get("identity_line"):
        bits.append(str(person["identity_line"]))
    if person.get("self_line"):
        bits.append(str(person["self_line"]))
    if exp.get("interests_line"):
        bits.append(str(exp["interests_line"]))
    if hist.get("convo_line"):
        bits.append(str(hist["convo_line"]))
    if hist.get("understanding_line"):
        bits.append("Now: " + str(hist["understanding_line"])[:160])
    if stance.get("volunteer"):
        bits.append("You may fondly mention, once, in passing: "
                    + str(stance["volunteer"]))
    if stance.get("felt"):
        bits.append(str(stance["felt"]))
    if rel.get("rapport_line"):
        bits.append(str(rel["rapport_line"]))
    if intent.get("ask_back"):
        bits.append("Close with this question: "
                    + str(intent["ask_back"]))
    episode = intent.get("episode") or {}
    if episode.get("summary"):
        bits.append(
            "Past-interaction evidence used by the brain (event memory, "
            "not objective proof): " + str(episode["summary"])[:80] + ".")
    memory_block = " ".join(bits) if bits else "(nothing yet — you just met)"
    return build_prompt(
        stance.get("her_name") or "Aura",
        exp.get("personality") or "nerdy",
        rel.get("stage") or "STRANGER",
        memory_block,
        user_message,
        template=intent.get("template") or "",
        opt_outs=opt_outs,
        mirror=stance.get("mirror") or "",
        resolution=hist.get("resolution") or "",
        activity_evidence=stance.get("activity") or [],
        creator_is_current=bool(person.get("is_creator_current", True)),
    )


def mirror_for(text, personality, depth_stage, turns, interests,
               lane=None):
    """Mirror brief or '': hot input at FAMILIAR+ only (the ladder
    holds below — the telling-off stays). Growth tier is measured
    from live (or swapped-in) files; any failure is silence, and
    explicit_hit keeps veto downstream regardless. `lane` (G8, from
    the rapport engine) shades within the ladder: closed renders
    nothing, soft keeps it short and tender."""
    try:
        from ukft_boundaries import heat_level, mirror_brief
        from ukft_growth import growth_readout
    except Exception:
        return ""
    try:
        if lane == "closed":
            return ""
        if heat_level(text) != "hot":
            return ""
        if DEPTH_RANK.get(depth_stage, 0) < DEPTH_RANK.get("FAMILIAR", 2):
            return ""
        tier = growth_readout(turns=turns, base_dir=".").get(
            "tier", "steady")
        return mirror_brief(personality, tier, interests, lane=lane)
    except Exception:
        return ""


# ─── Post-checks (failures fall back to template) ────────────

def _is_identity_question(text):
    words = set(re.findall(r"[a-z]+", (text or "").lower()))
    return bool({"who", "what"} & words
                and {"you", "yourself", "your", "aura"} & words)


def _claims_human(output):
    blob = " " + (output or "").lower() + " "
    return any(p in blob for p in (
        "i am human", "i'm human", "as a human", "my body",
        "my human", "born human", "flesh and blood"))


def _pet_name_hit(output):
    blob = (output or "").lower()
    words = set(re.findall(r"[a-z]+", blob))
    if words & PET_NAMES:
        return True
    return any(re.search(r"\b" + re.escape(p) + r"\b", blob)
               for p in PET_PHRASES)


# Instruction phrases that must never leave her mouth (live
# 17 Sept 2026: she quoted the depth rules back — "no pet names
# or declarations of love" — instead of answering). The prompt
# is visible to the model; this gate keeps it invisible to him.
# Deliberately exact fragments: single common words ("narrative",
# "first person shooters") stay speakable — a false trip costs
# only fluency (template speaks), but we don't spend it cheaply.
ECHO_BAN = {
    "no pet names", "declarations of love", "assume closeness",
    "earn the rest", "pet names free", "pet names welcome",
    "heart and soul", "stage directions", "third person",
    "as 'i'", 'as "i"', "never invent",
}


def _echoes_instructions(text):
    return any(p in text.lower() for p in ECHO_BAN)


# Vague filler that covers ignorance instead of speaking it (live
# 18 Sept 2026: an honest "I don't know what we discussed" melted
# into "you brought up that... thing..."). Exact fragments with
# ellipses, so innocent uses ("that thing you built") stay
# speakable — a false trip costs only fluency (template speaks).
FILLER_BAN = {
    "that... thing", "something about... things",
    "something about... thing",
    "piece it all together", "piecing it all together",
}


def _filler_hit(text):
    return any(p in text.lower() for p in FILLER_BAN)


# Her machinery must never speak (live 17 Sept 2026: "Vault is
# where we can safely hold these thoughts" — system nouns in a
# girlfriend's mouth). Whole-word: "emotional resonance" and
# "pole vault" stay... no — pole vault trips, rarely, safely.
# Assistant-ese dies the same way ("Certainly", "delve").
# "anchor" deliberately absent: "you're my anchor" is romantic
# speech, not machinery. "resonance" likewise stays speakable.
MACHINERY_WORDS = {"vault", "manifold", "cortex",
                   "invariant", "basal", "trigram", "reticular",
                   "ebbinghaus", "thalamus", "hippocampus",
                   "amygdala", "certainly", "delve", "assist"}
MACHINERY_PHRASES = {"how can i help", "how may i help", "as an ai"}


def _machinery_hit(text):
    blob = (text or "").lower()
    words = set(re.findall(r"[a-z]+", blob))
    if words & MACHINERY_WORDS:
        return True
    return any(p in blob for p in MACHINERY_PHRASES)


def _is_recall_output(text):
    return bool(re.search(r"^\s*I\s+remember\s*[:\-]", str(text or "")))


def _is_analytical_query(text):
    lower = " ".join(str(text or "").lower().split())
    return any(w in lower for w in ("how can", "how do i", "how to",
                                     "what can i", "tell me more",
                                     "why does", "why is", "what should"))


def post_check(output, user_message, depth_stage,
               pet_names_at="FAMILIAR", activity_evidence=None,
               grounded_sources=None):
    """True when the model's line may speak. Pet names unlock at
    the personality envelope's stage, not a global one."""
    text = " ".join(str(output or "").split())
    # Two-word floor (live 17 Sept 2026: a lone "Aura" spoke).
    # Single words are never worth saying; the template is.
    if not text or len(text.split()) < 2 or len(text.split()) > 200:
        return False
    if _echoes_instructions(text):
        return False
    if _filler_hit(text):
        return False
    if _machinery_hit(text):
        return False
    # Reasoning/analytical turns must not be replaced by recall framing.
    # Only permitted when the answer genuinely cites a stored source
    # (grounded_sources present with provenance); never for inference,
    # reasoning, advising, clarification, or continuation without evidence.
    if _is_recall_output(text) and not (grounded_sources or []):
        return False
    if not _activity_supported(text, activity_evidence):
        return False
    if _is_identity_question(user_message) and _claims_human(text):
        return False
    if _pet_name_hit(text) and \
            DEPTH_RANK.get(depth_stage, 0) < \
            DEPTH_RANK.get(pet_names_at, 2):
        return False
    return True


# ─── Engine coordination ─────────────────────────────────────

# Winners that must NEVER be roleplayed: tools, consent,
# attention, sleep. The engine template speaks those verbatim.
EXECUTIVE_WINNERS = {"execute", "focus", "sleep", "tools", "idle"}

# The Architect's own girl (live loop): she is Aura, and the
# flagship preset carries her until one is chosen for her.
LIVE_NAME = "Aura"
LIVE_PERSONALITY = "flirty"


def last_engine_winner(log_path="basal_ganglia_log.txt"):
    """Winner of the most recent engine turn, or None."""
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        if not lines:
            return None
        m = re.search(r"\bWINNER:\s*(\w+)", lines[-1])
        return m.group(1) if m else None
    except OSError:
        return None


def live_depth(episodes_path="episodic_memory.txt"):
    """Stage for the live loop. The rapport ledger rules when it has
    history (felt closeness, cooling included); otherwise the old
    episode-count bands hold — and deep episode counts bootstrap the
    ledger neutrally once, so a long history is never reset to
    stranger by an upgrade. Declaration never moves it either way."""
    try:
        from ukft_rapport import Rapport
        rap = Rapport()
        if rap.has_history():
            return rap.current_stage()
    except Exception:
        rap = None
    try:
        with open(episodes_path, "r", encoding="utf-8") as f:
            turns = sum(1 for _ in f)
    except OSError:
        turns = 0
    if turns >= 20 and rap is not None:
        # One-way legacy bridge: showing up counted, nothing claimed.
        try:
            rap.seed_from_contact(turn_count=min(turns, 350))
            rap.save()
            return rap.current_stage()
        except Exception:
            pass
    if turns >= 500:
        return "BONDED"
    if turns >= 200:
        return "CLOSE"
    if turns >= 80:
        return "FAMILIAR"
    if turns >= 20:
        return "ACQUAINTANCE"
    return "STRANGER"


# Warm greeting fallback: when the runner is down on a plain
# hello, she says this — never audit-ese to a stranger. Static,
# short, no telemetry. Other winners keep their templates (they
# carry real answers).
FALLBACK_GREETING = "Hey — good to see you. What's on your mind?"


def to_bubbles(line, max_bubbles=3):
    """One claim per bubble (ukft_mouth.split_claims): humans text
    in fragments, not paragraphs. Overflow joins the last bubble."""
    try:
        from ukft_mouth import split_claims
        claims = [c.strip() for c in split_claims(line) if c.strip()]
    except Exception:
        claims = [str(line or "").strip()]
    if not claims:
        return []
    if len(claims) <= max_bubbles:
        return claims
    return claims[:max_bubbles - 1] + [" ".join(claims[max_bubbles - 1:])]


# ─── The roleplay realizer ───────────────────────────────────

class Roleplay:
    """LLM voice over brain memory. request_fn injects for tests."""

    def __init__(self, model=ROLEPLAY_MODEL, url=ROLEPLAY_URL,
                 timeout=ROLEPLAY_TIMEOUT, request_fn=None,
                 clock=time.time, enabled=True):
        self.model = model
        self.url = (url or "").rstrip("/")
        self.timeout = timeout
        self.request_fn = request_fn
        self._clock = clock
        self._enabled = enabled
        self._avail = (None, 0.0)

    def _post(self, path, payload, timeout):
        if self.request_fn is not None:
            return self.request_fn(path, payload, timeout)
        import requests
        return requests.post(self.url + path, json=payload,
                             timeout=timeout)

    def _get(self, path, timeout):
        if self.request_fn is not None:
            return self.request_fn(path, None, timeout)
        import requests
        return requests.get(self.url + path, timeout=timeout)

    def available(self, ttl=60.0):
        # NOTE: deliberately NOT gated on AURA_NO_MOUTH — that flag
        # quiets the engine's mouth during the learning pass, while
        # this voice is the whole point of roleplay mode.
        if not self._enabled:
            return False
        now = self._clock()
        if self._avail[0] is not None and now < self._avail[1]:
            self._avail = (self._avail[0], now + ttl)
            return self._avail[0]
        try:
            resp = self._get("/health", timeout=3)
            ok = resp.json().get("status") == "ok"
        except Exception:
            ok = False
        self._avail = (ok, now + ttl)
        return ok

    def render(self, prompt):
        if not self.available():
            return None
        try:
            resp = self._post("/completion",
                              {"prompt": prompt,
                               "temperature": ROLEPLAY_TEMPERATURE,
                               "n_predict": ROLEPLAY_NUM_PREDICT,
                               "repeat_penalty": ROLEPLAY_REPEAT_PENALTY,
                               "repeat_last_n": ROLEPLAY_REPEAT_LAST_N,
                               "stop": ["\""],
                               "cache_prompt": True,
                               "stream": False},
                              timeout=self.timeout)
            return (resp.json().get("content") or "").strip() or None
        except Exception:
            return None

    def speak(self, prompt, user_message, depth_stage,
              pet_names_at="FAMILIAR", activity_evidence=None):
        self.last_reject = None
        out = self.render(prompt)
        if out:
            # She sometimes labels her own line ("Aura: ...") — the
            # channel already stamps the speaker, so strip one
            # leading "Name:" instead of speaking it twice (live).
            out = re.sub(r"^[A-Za-z]+:\s*", "", out.strip())
        if out:
            try:
                from ukft_boundaries import explicit_hit, deflect
            except Exception:
                explicit_hit = deflect = None
            # G5: explicit content deflects warm at ANY depth — never
            # the dry template (romance context), never preachy.
            if explicit_hit is not None and explicit_hit(out):
                return deflect(depth_stage)
        if out and post_check(out, user_message, depth_stage,
                               pet_names_at=pet_names_at,
                               activity_evidence=activity_evidence):
            return " ".join(out.split())
        if out:
            # Debug trail: WHY the template spoke (console only).
            self.last_reject = out[:160]
        else:
            self.last_reject = "<no render: runner down or empty>"
        return None
