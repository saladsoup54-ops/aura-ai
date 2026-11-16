# aura_vault_io.py — AURA Vault I/O Contract (Phase 0.6)
# ======================================================
# Single source of truth for locked_patterns.txt parsing and writing.
#
# Canonical record format:
#   ANCHOR: <concept> | DATA: <content> | SOURCE: <tag>
#
# The parser also tolerates the legacy nested format produced by the
# Cortex/Dream-State pipeline:
#   JUDGEMENT: STABLE | SIGNAL: 0.0670 | DATA: ANCHOR: <concept> | DATA: <content> | SOURCE: <tag>
#
# PATTERN: lines and section headers are not memories and are ignored.

import hashlib
import os
import re

VAULT_FILE = "locked_patterns.txt"

# In-memory hash index for append-side deduplication.
_seen_hashes = set()
_index_state = {"loaded": False, "size": -1, "mtime": 0.0}


def parse_vault_line(line):
    """
    Parse one vault line into (concept, data, source), or None if the
    line is not a memory record (noise, headers, blanks).
    Underscores/hyphens in the concept are rendered as spaces for display
    and later tokenization.
    """
    s = line.strip()
    if not s:
        return None
    if s.startswith("PATTERN:") or s.startswith("---"):
        return None

    idx = s.find("ANCHOR:")
    if idx == -1:
        return None

    concept_part = s[idx + len("ANCHOR:"):]
    head, sep, rest = concept_part.partition("|")
    concept = " ".join(head.replace("_", " ").replace("-", " ").split())
    if not concept:
        return None

    source = ""
    body = rest
    if "SOURCE:" in body:
        body, source = body.rsplit("SOURCE:", 1)
        source = source.strip()

    data = ""
    if "DATA:" in body:
        data = body.rsplit("DATA:", 1)[1].strip()
    if not data:
        data = rest.strip()

    # Drop the field separator left over before SOURCE: (if any)
    data = data.rstrip("|").strip()

    if not data:
        return None
    return concept, data, source


def iter_anchors(path=VAULT_FILE):
    """
    Yield (concept, data, source) for every memory record in the vault.
    """
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            parsed = parse_vault_line(line)
            if parsed:
                yield parsed


def tokenize_words(text, min_len=4):
    """Lowercase alphabetic runs of at least min_len characters."""
    return [w for w in re.findall(r"[a-zA-Z]+", repair_hyphenation(text.lower()))
            if len(w) >= min_len]


# Legitimate short words — everything else that short (or vowel-less)
# counts against a text's quality.
SHORT_WORDS = {"a", "i", "of", "to", "in", "on", "at", "by", "be", "he",
               "we", "it", "is", "as", "an", "or", "so", "if", "me",
               "my", "us", "do", "go", "no", "up", "am"}


def is_junk_text(text):
    """
    Scanned-page OCR garbage ("M I R P U B L I S H E R S M O S C OW .\
    llll") consists of spaced single letters and vowel-less runs.  A
    text is junk when more than a third of its tokens are short
    fragments or vowel-less "words" — real prose never looks like that.
    """
    tokens = re.findall(r"[a-zA-Z]+", text.lower())
    if not tokens:
        return True
    bad = 0
    for t in tokens:
        if t in SHORT_WORDS:
            continue
        if len(t) <= 2 or not re.search(r"[aeiouy]", t):
            bad += 1
    return bad / len(tokens) > 0.35


# Suspended-hyphenation function words: "project- or system- level" must
# NOT be glued into "projector systemlevel" — these never merge.
HYPHEN_STOP = {
    "or", "and", "to", "in", "of", "on", "the", "a", "an", "with",
    "for", "by", "at", "be", "is", "was", "are", "it", "as", "per",
    "so", "if", "he", "we", "you", "they", "she", "his", "her", "its",
    "their", "from", "into", "onto", "that", "this", "not", "but",
    "do", "did", "does", "may", "can", "will", "have", "has", "had",
    "been", "being", "one", "all", "any", "no", "nor", "yet", "than",
    "then", "when", "where", "which", "who", "whom", "whose", "what",
    "why", "how", "also", "only", "very", "just", "must", "our",
    "your", "my", "me", "us", "them", "him", "i",
}


def repair_hyphenation(text):
    """
    Rejoin line-break hyphenation from PDF extraction ("be- cause" ->
    "because", "is- ra- el" -> "israel").  A fragment pair is merged
    only when at least one side is a short syllable (<=4 chars) and the
    right side is not a function word, so genuine suspended compounds
    ("project- or system- level") are left intact.  Iterated until
    stable because words can split across three fragments.
    """
    changed = [True]

    def repl(m):
        left, right = m.group(1), m.group(2)
        if right in HYPHEN_STOP:
            return m.group(0)
        if len(left) > 4 and len(right) > 4:
            return m.group(0)
        changed[0] = True
        return left + right

    while changed[0]:
        changed[0] = False
        text = re.sub(r"([a-zA-Z]+)-\s+([a-zA-Z]+)", repl, text)
    return text


# Seed candidates never start a generated sentence with function words,
# question words, or the Architect's address terms — the response must
# open on the query's content ("jesus lord...", not "the cloud...").
SEED_STOP = set(HYPHEN_STOP) | {
    "what", "know", "tell", "please", "hello", "hi", "hey",
    "aura", "architect", "matty", "about", "can", "could", "would",
    "should", "may", "might", "do", "did", "does", "are", "was",
    "were", "been", "be", "is", "am", "has", "have", "had", "let",
    "me", "my", "our", "us", "we", "you", "your", "get", "give",
    "make", "take", "like", "just", "really", "very", "much", "many",
    "more", "most", "some", "any", "all", "there", "here", "their",
    "them", "then", "than", "this", "that", "these", "those",
    # Discourse verbs: "what do you mean by that" is a follow-up
    # pointing at the previous topic, not a new "mean" thread.
    "mean", "means", "meant", "say", "said", "says", "saying",
    "talk", "talking", "speak", "spoke", "speaking", "explain",
    "explained", "explains", "describe", "described", "describes",
    "define", "defined", "understand", "understood", "think",
    "thought", "thinking", "believe", "believed",
    # Attention directives: "focus on dark matter" targets dark matter.
    "focus", "focusing", "focused", "concentrate", "concentrating",
    "attention", "stop", "stopped", "release",
}


def hash_key(concept, data):
    return hashlib.sha1(
        f"{concept}\x1f{data}".encode("utf-8", "ignore")
    ).hexdigest()


def ensure_hash_index(path=VAULT_FILE):
    """
    Build the dedup hash index once, and REBUILD it whenever the vault
    file changed underneath us (compaction, restore, external rewrite).
    A stale index silently mis-deduped after a rewrite — Phase 5-A
    hardening found this under stress.
    """
    global _seen_hashes
    try:
        st = os.stat(path)
    except OSError:
        return
    if (_index_state["loaded"] and st.st_size == _index_state["size"]
            and st.st_mtime == _index_state["mtime"]):
        return
    hashes = {hash_key(c, d) for c, d, _ in iter_anchors(path)}
    _seen_hashes = hashes
    _index_state.update({"loaded": True, "size": st.st_size,
                         "mtime": st.st_mtime})


def append_anchor(path, concept, data, source="MANIFEST", dedup=True):
    """
    Append a canonical record. Returns True if written, False if it was a
    duplicate (dedup=True). Uses an in-memory hash index so repeated calls
    do not rescan the file.  Phase 5-A: the dedup check and the write
    happen under the message-bus path lock — concurrent appenders can
    neither interleave lines nor double-write the same record.
    """
    from aura_bus import locked as bus_locked
    from aura_state import deny_live_write
    deny_live_write(path)

    concept = " ".join(concept.replace("_", " ").replace("-", " ").split())
    key = hash_key(concept, data)

    with bus_locked(path):
        if dedup:
            ensure_hash_index(path)
            if key in _seen_hashes:
                return False
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(f"ANCHOR: {concept} | DATA: {data} | SOURCE: {source}\n")
        except Exception as e:
            # A failed append is data loss, not a duplicate: say so on
            # the console (which is mirrored to disk) instead of
            # vanishing into a False.
            print(f"[Vault] append friction on {path}: {e}")
            return False
        if dedup:
            _seen_hashes.add(key)
            # The file just grew: refresh the cached stat so the NEXT
            # append does not see a size mismatch and rescan the whole
            # vault (every append used to cost one full 9 MB re-read).
            try:
                st = os.stat(path)
                _index_state.update({"loaded": True, "size": st.st_size,
                                     "mtime": st.st_mtime})
            except OSError:
                _index_state.update({"loaded": False})
        return True


def compact_vault(path=VAULT_FILE, legacy_path="locked_patterns_legacy.txt"):
    """
    One-time migration (Phase 0.6): rewrite the vault in canonical,
    deduplicated form. Non-memory noise (PATTERN: lines, headers) is
    archived to legacy_path. Returns a stats dict.

    Crash-safe: the whole read-rewrite runs under the message-bus path
    lock (concurrent appends wait instead of interleaving), and the new
    content lands via temp-file + atomic replace — a crash leaves the
    old vault intact, never a truncation.
    """
    from aura_bus import locked as bus_locked

    with bus_locked(path):
        records = {}
        noise = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parsed = parse_vault_line(line)
                if parsed:
                    concept, data, source = parsed
                    key = hash_key(concept, data)
                    if key not in records:
                        records[key] = (concept, data, source)
                elif line.strip():
                    noise.append(line)

        if legacy_path and noise:
            with open(legacy_path, "a", encoding="utf-8",
                      errors="ignore") as lf:
                lf.writelines(noise)

        tmp_path = path + ".compact_tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write("--- AURA SOVEREIGN VAULT (v2 CANONICAL) ---\n")
            for concept, data, source in records.values():
                f.write(f"ANCHOR: {concept} | DATA: {data} | "
                        f"SOURCE: {source}\n")
        os.replace(tmp_path, path)

    return {"records": len(records), "noise_archived": len(noise)}
