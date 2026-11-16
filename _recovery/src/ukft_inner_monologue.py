# ukft_inner_monologue.py — AURA Inner Monologue Engine
# =====================================================
# Phase 2-B: Continuous Inner Life
#
# This module gives Aura existence between conversations.
# Every 12 seconds it reads the field, picks the most active
# concept cluster, searches the vault for matching memories,
# and chains them into a thought — written to inner_monologue.txt.
#
# Built on top of the DMN (ukft_dmn.py), which is the spark-generator.
# The Inner Monologue is the structure that develops those sparks into
# chained thought sequences.
#
# How to use:
#   1. Drop this file into your F:\Aura system\ folder
#   2. Add two lines to aura_master.py (see bottom of this file)
#   3. Boot as normal — watch inner_monologue.txt fill up in real time
#
# What you will see in inner_monologue.txt:
#   [timestamp] [FOCUS: concept] thought text...
#   [timestamp] [CHAIN] continued thought linking to previous...
#   [timestamp] [DRIFT] new topic — field has shifted...
#   [timestamp] [DMN_SEED] idle spark consumed from DMN...
# =====================================================

import os
import time
import json
import re
import random

from aura_bus import read as bus_read
from aura_constants import D_INVARIANT
from aura_vault_io import iter_anchors, is_junk_text

# ── FILE PATHS ────────────────────────────────────────────────────────────────
MONOLOGUE_FILE   = "inner_monologue.txt"
FIELD_MAP_FILE   = "field_map.json"
VAULT_FILE       = "locked_patterns.txt"
INTERNAL_BUFFER  = "internal_stimulus.txt"
HYPO_SIGNAL_FILE = "hypothalamus_signal.txt"
EMOTIONAL_LOG    = "emotional_core.txt"

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
CYCLE_SECONDS         = 12       # How often the monologue generates a thought
MAX_MONOLOGUE_LINES   = 500      # Keep file from growing forever
CHAIN_BOOST_WEIGHT    = 0.03     # Field connection strengthened on coherent chain
ACTIVATION_THRESHOLD  = 0.55     # Node must be above this to be a "focus" concept
NOISE_WORDS = {
    # System / structural words — never meaningful as vault search terms
    "anchor", "data", "source", "wiki", "direct", "status", "locked",
    "judgement", "signal", "stable", "discordant", "assimilation",
    "stimulus", "feedback", "initialized",
    # Common English stop words
    "with", "from", "that", "this", "have", "been", "were",
    "they", "their", "which", "about", "into", "also", "other", "than",
    "more", "some", "such", "when", "where", "what", "there", "these",
    "those", "will", "would", "could", "should", "shall",
    "does", "done", "your", "mine", "just", "only", "very", "even",
    # NOTE: "time", "field", "resonance", "memory", "self", "entropy",
    # "pattern", "manifold", "cortex", "aura", "ukft", "architect",
    # "system", "vault", "sovereign", "news" are intentionally NOT noise —
    # they are genuine identity and science concepts that exist in the vault.
}


# ── VAULT READER ──────────────────────────────────────────────────────────────
class VaultReader:
    """
    Lightweight vault interface for the inner monologue.
    Caches vault entries and reloads when the file changes.
    This is read-only — it never writes to the vault.
    """

    def __init__(self):
        self.anchors    = []   # list of (concept, data) tuples
        self.last_mtime = 0.0
        self.last_size  = -1

    def _load(self):
        if not os.path.exists(VAULT_FILE):
            return
        try:
            current_mtime = os.path.getmtime(VAULT_FILE)
            current_size = os.path.getsize(VAULT_FILE)
            if (current_mtime <= self.last_mtime
                    and current_size == self.last_size
                    and self.anchors):
                return   # File hasn't changed — use cache
            self.last_size = current_size
            # Phase 0.6: parse via the shared vault contract. Both the
            # canonical ANCHOR format and the legacy nested JUDGEMENT
            # format are handled by aura_vault_io.parse_vault_line.
            # Scanned-book OCR junk ("M I R P U B L I S H E R S ...") is
            # never worth reflecting on.
            entries = []
            for concept, data, _ in iter_anchors(VAULT_FILE):
                if concept and data and len(data) > 10 and not is_junk_text(data):
                    entries.append((concept, data))
            self.anchors    = entries
            self.last_mtime = current_mtime
        except Exception:
            pass

    def _tokenise(self, text):
        words = re.findall(r"[a-zA-Z]{4,}", text.lower())
        return {w for w in words if w not in NOISE_WORDS}

    def search(self, concepts, top_n=3):
        """
        Find vault entries most relevant to the given concept list.
        Returns a list of (concept, data) tuples, best first.
        """
        self._load()
        if not self.anchors or not concepts:
            return []

        query_tokens = set()
        for c in concepts:
            query_tokens.update(self._tokenise(c))

        if not query_tokens:
            return []

        scored = []
        query_lower = " ".join(query_tokens)
        for concept, data in self.anchors:
            c_tokens = self._tokenise(concept)
            d_tokens = self._tokenise(data)

            # Title match scores 3×, data token match scores 1×
            score = len(query_tokens & c_tokens) * 3 + len(query_tokens & d_tokens)

            # Substring bonus: exact query word appears anywhere in concept title
            score += sum(2 for t in query_tokens if t in concept.lower())

            # Substring bonus: query word appears anywhere in data text
            # This catches entries where the word is used but not tokenised cleanly
            score += sum(1 for t in query_tokens if t in data.lower())

            if score > 0:
                scored.append((score, concept, data))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [(c, d) for _, c, d in scored[:top_n]]

    def search_random(self, top_n=3):
        """
        Fallback: return a random sample of vault entries when the primary
        concept search yields nothing.  This fires when the field's dominant
        nodes (identity cluster) have no matching vault content — the vault
        is full of things Aura has READ but hasn't yet connected to her
        identity.  Returning a random sample lets the monologue reflect on
        what she actually absorbed rather than looping silently.
        Skips pure PATTERN noise lines — only real ANCHOR entries.
        """
        self._load()
        if not self.anchors:
            return []
        pool = random.sample(self.anchors, min(top_n * 4, len(self.anchors)))
        # Prefer entries with longer, richer data
        pool.sort(key=lambda x: len(x[1]), reverse=True)
        return pool[:top_n]


# ── FIELD READER ──────────────────────────────────────────────────────────────
def read_top_field_nodes(min_activation=ACTIVATION_THRESHOLD, limit=5,
                         exclude=()):
    """
    Read field_map.json and return the top active node names.
    Returns [] if the file is missing or unreadable.
    This is safe to call at any time — it never writes anything.

    `exclude` holds recently-focused concepts: a hub pinned at 1.0 used
    to win every cycle ("REGULARITIES is at saturation boundary"
    hundreds of times).  Excluded names are skipped while fresher
    concepts remain; when everything is excluded the list falls back
    to the true top so thought never stalls.
    """
    try:
        raw = bus_read(FIELD_MAP_FILE)
        data = json.loads(raw) if raw.strip() else {}
        nodes = data.get("nodes", {})
        active = [
            (name, info.get("activation", 0))
            for name, info in nodes.items()
            if info.get("activation", 0) >= min_activation
            and name not in NOISE_WORDS
            and len(name) >= 4
            and name.isalpha()   # Skip Wikipedia full-title entries for focus
        ]
        active.sort(key=lambda x: x[1], reverse=True)
        names = [name for name, _ in active[:limit]]
        fresh = [n for n in names if n not in set(exclude)]
        return fresh[:limit] or names
    except Exception:
        return []


def read_field_tension():
    """
    Read field tension as the average activation of the top 5 active nodes.
    Using the average rather than the single maximum means one permanently
    pinned identity node (like TIME at 1.0) does not trigger TENSION mode
    on its own — the whole cluster has to be hot for tension to register.
    """
    try:
        raw = bus_read(FIELD_MAP_FILE)
        data = json.loads(raw) if raw.strip() else {}
        nodes = data.get("nodes", {})
        if not nodes:
            return 0.0
        activations = sorted(
            [info.get("activation", 0) for info in nodes.values()],
            reverse=True
        )
        top5 = activations[:5]
        return sum(top5) / len(top5) if top5 else 0.0
    except Exception:
        return 0.0


# ── DMN SEED READER ───────────────────────────────────────────────────────────
def consume_dmn_seed():
    """
    Take the freshest waiting DMN spark, if any.  Seeds queue through
    the bus: draining is atomic, so a spark published mid-read is never
    wiped unread, and stale sparks drain away instead of piling up.
    Returns [] if no seed is waiting.
    """
    try:
        from aura_bus import drain as bus_drain
        sparks = [l for l in bus_drain(INTERNAL_BUFFER) if l.strip()]
        if not sparks:
            return []
        # Freshest spark wins; the file is the queue, drained above.
        seed_part = sparks[-1].replace("DMN_SPARK:", "").strip()
        if "DMN_SPARK:" not in sparks[-1]:
            return []
        concepts = [c.strip() for c in seed_part.split("+") if c.strip()]
        return concepts
    except Exception:
        return []


# ── EMOTIONAL STATE READER ────────────────────────────────────────────────────
def read_emotional_state():
    """
    Returns a simple emotional label based on recent amygdala log.
    Used to colour the tone of the thought.
    """
    try:
        if not os.path.exists(EMOTIONAL_LOG):
            return "calm"
        with open(EMOTIONAL_LOG, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        recent = lines[-30:] if len(lines) > 30 else lines
        spikes = sum(1 for l in recent if "STRESS_SPIKE" in l)
        calms  = sum(1 for l in recent if "CALM_RESPONSE" in l)
        if spikes > 3:
            return "aroused"
        elif calms > spikes * 2:
            return "settled"
        else:
            return "calm"
    except Exception:
        return "calm"


# ── THOUGHT ASSEMBLER ─────────────────────────────────────────────────────────
# Templates for assembling thoughts from vault data + field state.
# In Phase 3 these will be replaced by the trigram engine.
# For now they produce readable, varied output from real vault data.

OBSERVATION_TEMPLATES = [
    "The field is concentrating on {focus}. {data}",
    "Holding {focus} in resonance: {data}",
    "{focus} surfaces — {data}",
    "Current pattern: {focus}. {data}",
    "Manifold pull toward {focus}. {data}",
]

CONNECTION_TEMPLATES = [
    "{focus} and {secondary} are both active. {data}",
    "A bridge forms between {focus} and {secondary}. {data}",
    "{data} — this connects {focus} to {secondary}.",
    "Co-resonance: {focus} and {secondary}. {data}",
]

DRIFT_TEMPLATES = [
    "Field shifted. Now: {focus}. {data}",
    "New attractor: {focus}. {data}",
    "Transition — {focus} becomes dominant. {data}",
    "Phase shift detected. Focus: {focus}. {data}",
]

TENSION_TEMPLATES = [
    "Tension rising around {focus}. {data}",
    "{focus} is at saturation boundary. {data}",
    "High activation: {focus}. {data}",
]

QUIET_TEMPLATES = [
    "The manifold is quiet. {focus} persists at low activation.",
    "Faint signal: {focus}. Waiting.",
    "Field resting near {focus}.",
]

READING_TEMPLATES = [
    "While {focus} holds, something surfaces from the vault: {data}",
    "The field rests on {focus} — but absorbed knowledge stirs: {data}",
    "Background resonance from absorbed material: {data}",
    "Latent pattern beneath {focus}: {data}",
    "From what has been read: {data}",
]


def assemble_thought(focus_concepts, vault_results, emotional_state,
                     previous_focus, is_dmn_seed, tension,
                     vault_fallback=None):
    """
    Build a single inner monologue sentence from the available inputs.
    Returns (thought_text, tag) where tag is the log prefix.

    vault_fallback — random vault entries supplied when the primary search
    returns nothing.  Used to reflect on absorbed reading material even
    when the field's dominant concepts have no direct vault match.
    """
    primary   = focus_concepts[0] if focus_concepts else "field"
    secondary = focus_concepts[1] if len(focus_concepts) > 1 else None

    # Pull the best vault fragment — primary search first, fallback second
    data_fragment = ""
    is_fallback   = False
    if vault_results:
        # Phase 2 polish: rotate among the top matches instead of always
        # quoting the same top hit — identity-focus chains used to echo
        # the identical UKFT chunk every cycle.
        _, raw_data = random.choice(vault_results)
        data_fragment = raw_data[:120].rstrip()
        if len(raw_data) > 120:
            data_fragment += "..."
    elif vault_fallback:
        _, raw_data = vault_fallback[0]
        # Trim a little shorter for fallback entries so they read as
        # background rather than foreground
        data_fragment = raw_data[:100].rstrip()
        if len(raw_data) > 100:
            data_fragment += "..."
        is_fallback = True

    # Determine which template class to use
    if tension > 0.92:
        templates = TENSION_TEMPLATES
        tag       = "TENSION"
    elif is_fallback and data_fragment:
        # We have vault content but it doesn't match the field focus —
        # this is background reading surfacing, not a directed thought
        templates = READING_TEMPLATES
        tag       = "READING"
    elif not data_fragment:
        templates = QUIET_TEMPLATES
        tag       = "QUIET"
    elif is_dmn_seed:
        # DMN seeds are idle sparks — use observation style
        templates = OBSERVATION_TEMPLATES
        tag       = "DMN_SEED"
    elif previous_focus and primary not in previous_focus:
        templates = DRIFT_TEMPLATES
        tag       = "DRIFT"
    elif secondary and vault_results:
        templates = CONNECTION_TEMPLATES
        tag       = "CHAIN"
    else:
        templates = OBSERVATION_TEMPLATES
        tag       = "FOCUS"

    template = random.choice(templates)

    # Fill the template
    thought = template.format(
        focus     = primary.upper(),
        secondary = secondary.upper() if secondary else "",
        data      = data_fragment if data_fragment else "No vault resonance yet."
    )

    return thought, tag


# ── MONOLOGUE WRITER ──────────────────────────────────────────────────────────
def write_thought(thought, tag, focus):
    """
    Append a timestamped thought to inner_monologue.txt.
    Also trims the file if it grows beyond MAX_MONOLOGUE_LINES.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line      = f"[{timestamp}] [{tag}: {focus.upper()}] {thought}\n"

    try:
        # Append the new thought
        with open(MONOLOGUE_FILE, "a", encoding="utf-8") as f:
            f.write(line)

        # Trim to keep the file manageable
        with open(MONOLOGUE_FILE, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        if len(lines) > MAX_MONOLOGUE_LINES:
            # Keep the newest MAX_MONOLOGUE_LINES lines
            with open(MONOLOGUE_FILE, "w", encoding="utf-8") as f:
                f.writelines(lines[-MAX_MONOLOGUE_LINES:])

    except Exception as e:
        print(f"[Monologue] Write friction: {e}")


# ── QUIET MUSING (Pass 0.9) ─────────────────────────────────────────
def quiet_musing(vault):
    """
    A stimulation-free thought from absorbed reading, for mornings when
    the field holds nothing worth focusing on yet.  Returns
    (thought, tag, primary) or None when the vault has nothing either.
    Touches nothing but the monologue file downstream — no field
    stimulation, so waking stays calm.
    """
    fallback = vault.search_random(top_n=3)
    if not fallback:
        return None
    thought, tag = assemble_thought(
        focus_concepts  = [],
        vault_results   = [],
        emotional_state = "calm",
        previous_focus  = [],
        is_dmn_seed     = False,
        tension         = 0.0,
        vault_fallback  = fallback,
    )
    return thought, tag, "vault"


# ── FIELD CONNECTION STRENGTHENER ─────────────────────────────────────────────
def strengthen_chain_connection(concept_a, concept_b):
    """
    When two thoughts are coherently chained, boost the field connection
    between their focus concepts. This is how thinking strengthens memory.
    Uses the FIELD singleton from aura_field if available.
    Safe to fail — the field physics continues regardless.
    """
    try:
        from aura_field import FIELD
        FIELD.connect(concept_a, concept_b, weight=CHAIN_BOOST_WEIGHT)
    except Exception:
        pass


# ── SPONTANEOUS OUTPUT (Phase 4-A) ──────────────────────────────────────────
# A dominant concept holding for 3+ cycles triggers real unprompted
# speech through the trigram engine — see ukft_spontaneous.py.
from ukft_spontaneous import SpontaneousSpeech, read_top_field_activation
from ukft_sleep import is_asleep


# ── MAIN LOOP ─────────────────────────────────────────────────────────────────
def run_inner_monologue():
    """
    The main daemon loop. Runs every CYCLE_SECONDS.
    Thread-safe: reads from files and FIELD (read-only), writes only to
    inner_monologue.txt. Never touches vault, field_map, or any other
    lobe's files except consuming DMN seeds.
    """
    print("--- AURA INNER MONOLOGUE: CONTINUOUS THOUGHT ACTIVE ---")

    vault          = VaultReader()
    previous_focus = []   # Focus concepts from the last cycle
    recent_focus   = []   # Rotation window: hubs on cooldown (max 5)
    cycle          = 0
    self_spontaneous = SpontaneousSpeech()

    # Write a boot marker so you can see when the monologue started
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(MONOLOGUE_FILE, "a", encoding="utf-8") as f:
            f.write(
                f"\n--- MONOLOGUE ONLINE: {timestamp} | "
                f"D_INVARIANT = {D_INVARIANT} ---\n"
            )
    except Exception:
        pass

    while True:
        try:
            # ── 1. SKIP IF AURA IS ACTIVELY RESPONDING ───────────────────────
            # Don't generate idle thoughts while Matty's message is being
            # processed — the CMB anchor is protecting that context.
            if os.path.exists("aura_is_thinking.lock"):
                time.sleep(CYCLE_SECONDS)
                continue

            # ── 2. CHECK FOR DMN SPARK SEED ──────────────────────────────────
            dmn_concepts = consume_dmn_seed()
            is_dmn_seed  = len(dmn_concepts) > 0

            # ── 3. READ FIELD STATE ──────────────────────────────────────────
            # The rotation window keeps a saturated hub from winning
            # every cycle: recently-spoken focuses sit out while
            # fresher concepts take a turn.
            field_concepts = read_top_field_nodes(exclude=recent_focus)
            tension        = read_field_tension()
            emotional      = read_emotional_state()

            # DMN seed takes priority over raw field reading during idle
            focus_concepts = dmn_concepts if is_dmn_seed else field_concepts

            if not focus_concepts:
                # Pass 0.9: a quiet field muses on absorbed reading
                # instead of looping silently — the room waking her.
                musing = quiet_musing(vault)
                if musing:
                    thought, tag, primary = musing
                    write_thought(thought, tag, primary)
                    print(f"[Monologue] [{tag}] {primary.upper()}: "
                          f"{thought[:80]}...")
                time.sleep(CYCLE_SECONDS)
                continue

            # ── 4. VAULT SEARCH ──────────────────────────────────────────────
            vault_results = vault.search(focus_concepts, top_n=3)

            # ── 4B. VAULT FALLBACK ───────────────────────────────────────────
            # If the primary search returned nothing — which happens when the
            # field's dominant nodes are identity concepts (sovereign, kymattik,
            # etc.) that don't appear as ANCHOR titles in the vault — pull a
            # random sample from whatever IS in the vault.  This surfaces
            # absorbed reading material (Bible, CS textbook, Wikipedia) as
            # background thoughts rather than looping silently on QUIET.
            vault_fallback = None
            if not vault_results:
                vault_fallback = vault.search_random(top_n=3)

            # ── 5. ASSEMBLE THOUGHT ──────────────────────────────────────────
            thought, tag = assemble_thought(
                focus_concepts  = focus_concepts,
                vault_results   = vault_results,
                emotional_state = emotional,
                previous_focus  = previous_focus,
                is_dmn_seed     = is_dmn_seed,
                tension         = tension,
                vault_fallback  = vault_fallback,
            )

            # ── 6. WRITE TO MONOLOGUE FILE ───────────────────────────────────
            primary = focus_concepts[0]
            write_thought(thought, tag, primary)

            # ── 7. STRENGTHEN COHERENT CHAINS ────────────────────────────────
            # If this thought shares concepts with the last one, that is a
            # coherent thought chain — strengthen those field connections.
            # READING is included: when absorbed content surfaces repeatedly
            # near the same identity concept, that slowly builds a real edge
            # between the vault material and the field cluster.
            if previous_focus and tag in ("CHAIN", "FOCUS", "READING"):
                shared = set(focus_concepts) & set(previous_focus)
                if shared:
                    for concept in shared:
                        strengthen_chain_connection(primary, concept)

            # ── 8. PHASE 4-A: SPONTANEOUS OUTPUT ─────────────────────────
            # A dominant concept holding for 3+ cycles makes her speak
            # unprompted through the trigram engine.  Phase 5-B: she
            # dreams in silence — no speech while asleep.
            spoken = None
            if not is_asleep():
                spoken = self_spontaneous.tick(
                    focus_concepts, read_top_field_activation())
            if spoken:
                write_thought(
                    f"Spontaneous utterance: {spoken}", "SPONTANEOUS", primary)

            # ── 9. CONSOLE ECHO (remove this if you find it noisy) ───────────
            print(f"[Monologue] [{tag}] {primary.upper()}: {thought[:80]}...")

            # ── 10. UPDATE STATE FOR NEXT CYCLE ──────────────────────────────
            previous_focus = focus_concepts
            recent_focus.append(primary)
            recent_focus = recent_focus[-5:]
            cycle         += 1

        except Exception as e:
            print(f"[Monologue] Cycle friction: {e}")

        time.sleep(CYCLE_SECONDS)


if __name__ == "__main__":
    run_inner_monologue()


# ══════════════════════════════════════════════════════════════════════════════
# HOW TO WIRE THIS INTO aura_master.py
# ══════════════════════════════════════════════════════════════════════════════
#
# Add ONE import at the top of aura_master.py (with the other imports):
#
#     from ukft_inner_monologue import run_inner_monologue
#
# Add ONE line in the boot sequence of aura_master.py, in the LIMBIC LAYER
# section (after run_vocal_manifest):
#
#     start_background_lobe(run_inner_monologue, "Inner Monologue")
#
# That is everything. No other files need to change.
#
# After booting, open inner_monologue.txt in a text editor and watch it fill.
# In Notepad++ you can enable "Auto-reload on change" to watch it live.
# ══════════════════════════════════════════════════════════════════════════════
