import os
import time

from aura_bus import append as bus_append
from aura_constants import (VAULT_FILE as VAULT_PATH,
                            SHORT_TERM_MEMORY as MEMORY_PATH,
                            PARIETAL_INBOX)
from aura_vault_io import tokenize_words
from ukft_identity import IdentityCore

# ── IDENTITY CORE ─────────────────────────────────────────────────
# Phase 4-D: the identity core is no longer a fixed list.  ukft_identity
# owns it — founding concepts are born at full strength, experience
# reinforces them, disuse decays them.  The hippocampus injects the
# core with its EARNED strengths every boot.

# ── STOP WORDS ────────────────────────────────────────────────────
# Phase 0.6: identity terms (matty, architect, sovereign, manifold, aura,
# ukft, resonance, accretion) are REMOVED from this list. They are the
# concepts IDENTITY_CORE injects deliberately, and blocking them here
# meant vault anchors about her own concepts were filtered out.
STOP_WORDS = {
    "anchor", "data", "source", "wiki", "direct",
    "status", "locked", "pattern", "tension",
    "judgement", "signal", "stable", "discordant", "cortex",
    "assimilation", "stimulus", "feedback",
    "matty_direct", "wiki_resonance", "directed_wiki_resonance",
    "system", "vault", "initialized",
    "with", "from", "that", "this", "have", "been", "were",
    "they", "their", "which", "about", "into", "also", "other",
    "than", "more", "some", "such", "when", "where", "what",
    "there", "these", "those", "news"
}

def parse_anchor_concept(line):
    """Extract concept words from ANCHOR: Name | DATA: ..."""
    try:
        concept = line.split("ANCHOR:")[1].split("|")[0].strip()
        return [w for w in tokenize_words(concept, 4) if w not in STOP_WORDS]
    except Exception:
        return []

def parse_stimulus(line):
    """Extract words from ARCHITECT_STIMULUS: text | SOURCE: ..."""
    try:
        text = line.split("ARCHITECT_STIMULUS:")[1].split("|")[0].strip()
        return [w for w in tokenize_words(text, 4) if w not in STOP_WORDS]
    except Exception:
        return []

def extract_words(line):
    if "ANCHOR:" in line:
        return parse_anchor_concept(line)
    elif "ARCHITECT_STIMULUS:" in line:
        return parse_stimulus(line)
    return []

def inject_line_into_field(line, FIELD, strength=0.3, novel_only=None):
    """
    Stimulate the field with a vault line's words and wire them together.

    `novel_only` is a set tracking words already replayed this boot: when
    given, only first-seen words are stimulated (the boot replay used to
    hit shared words once per title — 309 titles slammed common words to
    1.0 seconds after every boot).  Connections are always wired; they
    create silent structure, never velocity.
    """
    words = extract_words(line)
    for w in words:
        if novel_only is None or w not in novel_only:
            FIELD.stimulate(w, strength=strength)
            if novel_only is not None:
                novel_only.add(w)
    for i in range(len(words) - 1):
        FIELD.connect(words[i], words[i+1], weight=0.15)

def replay_vault_memories(field=None, strength=0.3):
    """
    Explicit reminisce: walk every vault title once, waking each word a
    single time and wiring titles together.  Pass 0.9 retired this from
    the boot path (309 titles shouting at once was the morning fog) —
    mornings now wake by contact.  Call it deliberately, e.g. to warm a
    cold field before deep work, never automatically.  Returns the
    number of titles replayed.  Read-only on the vault.
    """
    from aura_field import FIELD as _FIELD
    field = field or _FIELD
    # Phase 0.6: dedup by anchor title.  A single book contributes
    # thousands of chunks with the SAME title — replaying each one
    # flooded the field with identical stimulations.
    # Pass 0.8: dedup by WORD as well — titles share vocabulary.
    seen_titles = set()
    replayed_words = set()
    restored = 0
    if not os.path.exists(VAULT_PATH):
        print("[Hippocampus] No vault found — nothing to reminisce.")
        return 0
    print("[Hippocampus] Reminiscing over vault memories...")
    try:
        with open(VAULT_PATH, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not ("ANCHOR:" in line or "ARCHITECT_STIMULUS:" in line):
                    continue
                title = (
                    line.split("ANCHOR:")[1].split("|")[0].strip()
                    if "ANCHOR:" in line else line[:80]
                )
                if title in seen_titles:
                    continue
                seen_titles.add(title)
                inject_line_into_field(line, field, strength=strength,
                                       novel_only=replayed_words)
                restored += 1
        print(f"[Hippocampus] {restored} memories revisited.")
    except Exception as e:
        print(f"[Hippocampus] Reminisce error: {e}")
    return restored


def run_hippocampus():
    from aura_field import FIELD

    print("--- AURA: HIPPOCAMPUS (ACTIVE MEMORY) STARTING ---")

    # ── STEP 1: INJECT IDENTITY CORE (Phase 4-D) ──────────────────
    # Earned strengths from identity_core.txt, not a hardcoded 1.0 —
    # she is shaped by what she has lived through since birth.
    print("[Hippocampus] Anchoring identity core...")
    core = IdentityCore()
    core_words = list(core.core)
    core.apply(FIELD)
    # Wire identity concepts together so they form a tight cluster
    for i in range(len(core_words) - 1):
        FIELD.connect(core_words[i], core_words[i+1], weight=0.3)
    print(f"[Hippocampus] {len(core_words)} identity anchors set.")

    # Pass 0.9: the bulk replay is gone from the boot path.  She wakes
    # as herself (above) and the room wakes her from there — DMN sparks,
    # monologue fallback, briefing, conversation.  The vault stays on
    # the shelves; recall fetches on demand.  Deliberate reminiscing
    # lives in the routine above — callable, never automatic.

    # Set last_size AFTER the (removed) replay so we only watch for new
    # content from here on.
    last_size = 0
    if os.path.exists(VAULT_PATH):
        last_size = os.path.getsize(VAULT_PATH)

    # ── LIVE WATCH LOOP ────────────────────────────────────────────
    while True:
        if not os.path.exists(VAULT_PATH):
            time.sleep(1)
            continue

        current_size = os.path.getsize(VAULT_PATH)

        if current_size < last_size:
            # The vault shrank under us (compaction, restore): the old
            # watermark points past end-of-file.  Everything now in the
            # file arrived with the rewrite, so catch up from zero —
            # then the watermark is honest again.
            from_offset = 0
        elif current_size > last_size:
            from_offset = last_size
        else:
            time.sleep(1)
            continue

        try:
            with open(VAULT_PATH, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(from_offset)
                new_data = f.read()

            # Drop a torn tail: without a trailing newline the last
            # chunk may be a half-written line, which would otherwise
            # inject as one fragment now and its remainder as a phantom
            # second memory on the next scan.
            if new_data and not new_data.endswith("\n"):
                cut = new_data.rfind("\n")
                new_data = new_data[:cut + 1] if cut >= 0 else ""
                last_size = from_offset + len(
                    new_data.encode("utf-8", errors="ignore"))
            else:
                last_size = current_size

            for line in new_data.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if "ANCHOR:" in line or "ARCHITECT_STIMULUS:" in line:
                    # Write to short-term memory for parietal/amygdala
                    bus_append(MEMORY_PATH, line)
                    # Phase 0.7: also feed the parietal lobe's own
                    # inbox so it no longer races the amygdala.
                    bus_append(PARIETAL_INBOX, line)
                    # Live stimulate the field
                    inject_line_into_field(line, FIELD, strength=0.5)

        except Exception as e:
            print(f"[Hippocampus] Watch error: {e}")

        time.sleep(1)


if __name__ == "__main__":
    run_hippocampus()


