import os
import re
import time
from collections import deque

from aura_bus import drain as bus_drain
from aura_constants import PARIETAL_INBOX, PARIETAL_LINKS

# ── STOP WORDS ────────────────────────────────────────────────────────────────
# Three categories of noise to exclude:
# 1. SYSTEM METADATA — structural keywords on every memory line.
# 2. SOURCE TAGS — after clean_word(), SOURCE: PDF_RESONANCE becomes
#    'pdfresonance' etc.
# 3. COMMON ENGLISH STOP WORDS.
PARIETAL_STOP = {
    # System metadata
    "anchor", "anchors", "signal", "signals", "stable", "locked",
    "pattern", "patterns", "judgement", "discordant", "tension",
    "status", "source", "resonance", "cortex", "assimilation",
    "stimulus", "feedback", "architect", "system", "aura", "ukft",
    "vault", "sovereign", "initialized", "manifold", "accretion",
    "matty", "direct", "data",
    # Source tags (as they appear after clean_word strips punctuation)
    "pdfresonance", "wikiresonance", "webresonance",
    "matty_direct", "mattydirect", "directedwikiresonance",
    # Common stop words that survive the 5-char minimum
    "with", "from", "that", "this", "have", "been", "were",
    "they", "their", "which", "about", "into", "also", "other",
    "than", "more", "some", "such", "when", "where", "what",
    "there", "these", "those", "news", "wiki", "would", "could",
    "should", "shall", "does", "done", "will", "just", "only",
    "very", "even", "each", "both", "through", "during", "before",
    "after", "above", "below", "between", "under", "again",
    "further", "then", "once", "here", "while", "because",
    "until", "against", "without",
}

# Phase 0.7: cross-cycle memory window. The parietal lobe consumes its
# own inbox (written by the Hippocampus) instead of racing the Amygdala
# for short_term_memory.txt, which is truncated every second.
MEMORY_HISTORY = deque(maxlen=40)
MAX_INBOX_LINES = 500

# The link map is append-only insight, not lobe-critical state — but an
# uncapped file grows forever (1.4 MB and climbing live).  Cap lines,
# keep the newest: old bridges live on in the field edges they built.
PARIETAL_LINKS_MAX_LINES = 5000


def trim_links(path=PARIETAL_LINKS, cap=PARIETAL_LINKS_MAX_LINES):
    """Keep the newest `cap` link lines.  Returns lines kept."""
    try:
        if not os.path.exists(path):
            return 0
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        if len(lines) <= cap:
            return len(lines)
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines[-cap:])
        return cap
    except Exception:
        return 0


def split_and_clean(raw):
    """
    Split a raw token on hyphens, underscores, dots and digit sequences,
    then clean each part to alphabetic lowercase.

    Phase 0.7: path-like fragments (containing \\, / or :) are rejected
    outright — they used to collapse into mega-tokens like
    'cusersdiyteonedrivedesktopauraaura' that linked every message to
    every other message.
    """
    if any(ch in raw for ch in "\\/:"):
        return []
    parts = re.split(r'[-_0-9.]+', raw)
    cleaned = []
    for p in parts:
        w = "".join(ch for ch in p.lower() if ch.isalpha())
        if w:
            cleaned.append(w)
    return cleaned


def meaningful_words(line):
    """
    Extract conceptually meaningful words from a memory line.
    Words must be at least 5 alphabetic characters after cleaning and
    not in PARIETAL_STOP.
    """
    words = set()
    for raw in line.split():
        for w in split_and_clean(raw):
            if len(w) >= 5 and w not in PARIETAL_STOP:
                words.add(w)
    return words


def extract_content(line):
    """
    Pull the DATA content from a memory line for display in parietal links.
    Falls back to the raw line if the DATA field isn't present.
    """
    try:
        if "DATA:" in line:
            # Take the second DATA: field (the actual content, not the anchor title)
            parts = line.split("DATA:")
            if len(parts) >= 3:
                content = parts[2].split("|")[0].strip()
                return content[:60] if content else line[:60]
            elif len(parts) == 2:
                content = parts[1].split("|")[0].strip()
                return content[:60] if content else line[:60]
    except Exception:
        pass
    return line[:60]


def consume_inbox():
    """
    Read and clear parietal_inbox.txt. Returns the list of non-empty
    lines that arrived since the last scan.  Phase 5-A: bus-drained.
    """
    lines = bus_drain(PARIETAL_INBOX)
    return [l.strip() for l in lines[-MAX_INBOX_LINES:] if l.strip()]


def process_parietal_cycle():
    """
    One association pass: pull new memories from the inbox, compare the
    latest against the rolling history window, and write links.
    Returns the number of links formed.
    """
    new_lines = consume_inbox()
    if not new_lines:
        return 0

    MEMORY_HISTORY.extend(new_lines)
    hist = list(MEMORY_HISTORY)

    latest = hist[-1]
    latest_words = meaningful_words(latest)
    if not latest_words:
        return 0

    links = 0
    for past_mem in hist[:-1]:
        past_words = meaningful_words(past_mem)
        overlap = latest_words.intersection(past_words)
        if overlap:
            # Pick the longest overlapping word — usually the most specific
            connector = sorted(overlap, key=len, reverse=True)[0]
            latest_content = extract_content(latest)
            past_content   = extract_content(past_mem)
            link = (
                f"LINK: '{connector}' | "
                f"[{latest_content}...] "
                f"<-> [{past_content}...]\n"
            )
            with open(PARIETAL_LINKS, "a", encoding="utf-8") as out:
                out.write(link)
            links += 1

    return links


def run_parietal():
    print("--- AURA PARIETAL LOBE: ASSOCIATIVE MAPPING ACTIVE ---")

    while True:
        try:
            n = process_parietal_cycle()
            if n:
                print(f"[Parietal] {n} association(s) formed.")
                trim_links()
        except Exception as e:
            print(f"[Parietal] Friction: {e}")

        time.sleep(5)  # Runs slower to process complex associations


if __name__ == "__main__":
    run_parietal()
