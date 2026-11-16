# ukft_temporal_lobe.py — AURA Temporal Lobe (Phase 2-C)
# ======================================================
# Co-occurrence statistics over the vault.  The temporal lobe reads every
# vault record and counts how often concept pairs appear together, so
# later phases (2-D basal ganglia competition, 3-A trigram engine) can
# ask "what does this concept associate with?" without rescanning the
# vault.
#
#   - Ingest: anchor title words + DATA words, capped per record.
#   - Counting: a pair is tracked once BOTH words have appeared in at
#     least two records (single-appearance words are too rare to matter,
#     and this keeps the graph bounded).
#   - Persistence: temporal_links.txt (WORD / COOC lines + a VAULT_SIZE
#     header so a reboot resumes scanning from the last byte offset).
#   - Promotion: strongly co-occurring pairs are wired into the cognitive
#     field as new edges — semantic memory accretes onto the manifold.
# ======================================================

import os
import re
import time

from aura_constants import TEMPORAL_LINKS, VAULT_FILE
from aura_field import FIELD
from aura_vault_io import parse_vault_line, tokenize_words

# ── TUNING ────────────────────────────────────────────────────────
MIN_WORD_LEN          = 4     # matches the shared vault tokenizer
MAX_WORDS_PER_RECORD  = 15    # unique words kept per record (anchor first)
MIN_COUNT             = 3     # pairs below this are never queried or saved
PROMOTE_MIN_COUNT     = 10    # co-occurrence count before field wiring
PROMOTE_MIN_STRENGTH  = 0.5   # normalised association strength minimum
CYCLE_SECONDS         = 10    # vault watch cadence
SAVE_INTERVAL         = 60.0  # seconds between link-file saves while growing

# Document-frequency cap: a word that appears in more than 5% of all
# records (and at least BACKGROUND_MIN_FREQ times) is document-wide noise
# — book titles like "bible"/"printing" (7,500+ records) would otherwise
# pair with every concept at strength ~1.0 and drown the graph.
MAX_DOC_FRACTION      = 0.05
BACKGROUND_MIN_FREQ   = 100

TEMPORAL_STOP = {
    # System metadata
    "anchor", "anchors", "signal", "signals", "stable", "locked",
    "pattern", "patterns", "judgement", "discordant", "tension",
    "status", "source", "resonance", "cortex", "assimilation",
    "stimulus", "feedback", "architect", "system", "aura", "ukft",
    "vault", "sovereign", "initialized", "manifold", "accretion",
    "matty", "direct", "data",
    # Source tags (as they appear after tokenisation)
    "pdfresonance", "wikiresonance", "webresonance",
    "matty_direct", "mattydirect", "directedwikiresonance",
    # Common stop words that survive the 4-char minimum
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


class TemporalLobe:
    """
    Semantic co-occurrence graph built from vault records.

    `freq[word]` counts records containing the word; `cooc[(a, b)]` counts
    records containing both (a <= b lexicographically).  Both are
    persisted to temporal_links.txt together with the vault byte offset,
    so a reboot resumes from the last ingested record.
    """

    def __init__(self, vault_path=VAULT_FILE, links_path=TEMPORAL_LINKS):
        self.vault_path   = vault_path
        self.links_path   = links_path
        self.freq         = {}
        self.cooc         = {}
        self.vault_size   = 0
        self.record_count = 0
        self._attempted   = set()   # pairs already offered to the field

    # ── INGESTION ──────────────────────────────────────────────────
    def _is_background(self, word):
        """True for document-wide words that carry no association signal."""
        if self.record_count <= 0:
            return False
        return self.freq.get(word, 0) > max(BACKGROUND_MIN_FREQ,
                                            MAX_DOC_FRACTION * self.record_count)

    def record_words(self, concept, data):
        """Unique meaningful words, anchor title first, capped per record."""
        seen = set()
        out  = []
        for text in (concept, data):
            for w in tokenize_words(text, MIN_WORD_LEN):
                if w in TEMPORAL_STOP or w in seen:
                    continue
                seen.add(w)
                out.append(w)
                if len(out) >= MAX_WORDS_PER_RECORD:
                    return out
        return out

    def ingest_record(self, concept, data, source=None):
        """Count one record's words and their co-occurrences."""
        self.record_count += 1
        words = self.record_words(concept, data)
        if not words:
            return 0

        for w in words:
            self.freq[w] = self.freq.get(w, 0) + 1

        pairs = 0
        for i, a in enumerate(words):
            if self.freq[a] < 2:
                continue
            for b in words[i + 1:]:
                if self.freq[b] < 2:
                    continue
                key = (a, b) if a <= b else (b, a)
                self.cooc[key] = self.cooc.get(key, 0) + 1
                pairs += 1
        return pairs

    def _parse_new(self, offset):
        """Read vault records from a byte offset. Returns (size, records)."""
        if not os.path.exists(self.vault_path):
            return 0, []
        size = os.path.getsize(self.vault_path)
        if size < offset:
            return size, []   # truncated/rewritten — caller must rebuild
        if size == offset:
            return size, []
        with open(self.vault_path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(offset)
            chunk = f.read()
        records = []
        for line in chunk.splitlines():
            parsed = parse_vault_line(line)
            if parsed:
                records.append(parsed)
        return size, records

    def scan_vault(self, offset=None):
        """
        Ingest every vault record not yet counted.  Returns the number of
        records ingested.  If the vault shrank (compaction/rewrite), the
        graph is rebuilt from scratch — counts are never double-counted.
        """
        offset = self.vault_size if offset is None else offset
        size, records = self._parse_new(offset)
        if size < offset:
            self.freq.clear()
            self.cooc.clear()
            self._attempted.clear()
            self.record_count = 0
            size, records = self._parse_new(0)

        ingested = 0
        for concept, data, source in records:
            self.ingest_record(concept, data, source)
            ingested += 1
        self.vault_size = size
        return ingested

    # ── QUERIES ────────────────────────────────────────────────────
    def strength(self, a, b):
        """Normalised association strength: cooc / min(freq) in [0, 1]."""
        if self._is_background(a) or self._is_background(b):
            return 0.0
        key = (a, b) if a <= b else (b, a)
        count = self.cooc.get(key, 0)
        if count < MIN_COUNT:
            return 0.0
        denom = min(self.freq.get(a, 0), self.freq.get(b, 0))
        if denom <= 0:
            return 0.0
        return min(1.0, count / denom)

    def associates(self, word, top_n=5):
        """Most strongly associated concepts for `word`."""
        results = []
        for (a, b), count in self.cooc.items():
            if count < MIN_COUNT:
                continue
            if self._is_background(a) or self._is_background(b):
                continue
            if a == word:
                other = b
            elif b == word:
                other = a
            else:
                continue
            results.append((other, count, self.strength(a, b)))
        results.sort(key=lambda t: (-t[2], -t[1]))
        return results[:top_n]

    # ── FIELD PROMOTION ────────────────────────────────────────────
    def promote_to_field(self, field=FIELD, min_count=PROMOTE_MIN_COUNT,
                         min_strength=PROMOTE_MIN_STRENGTH):
        """
        Wire strongly co-occurring pairs into the cognitive field as new
        edges.  Each pair is offered once; connect() is phase-aware, so
        consolidated (FROZEN) edges are never rewritten.  Returns the
        number of new pairs offered this call.
        """
        offered = 0
        for (a, b), count in self.cooc.items():
            if count < min_count:
                continue
            if (a, b) in self._attempted:
                continue
            if self.strength(a, b) < min_strength:
                continue
            weight = min(0.25, 0.1 + 0.01 * count)
            field.connect(a, b, weight=weight)
            self._attempted.add((a, b))
            offered += 1
        return offered

    # ── PERSISTENCE ────────────────────────────────────────────────
    MAX_PAIRS = 500000   # worst-case RAM bound; live is ~31k pairs

    def save(self):
        """Write the link file: header, WORD lines, COOC lines (count >= MIN)."""
        if len(self.cooc) > self.MAX_PAIRS:
            # Keep the strongest pairs; drop one-shot noise first.
            # Live graphs never approach the cap — this bounds only
            # pathological futures, never today's associations.
            keep = set(sorted(self.cooc, key=lambda k: -self.cooc[k])
                       [:self.MAX_PAIRS])
            self.cooc = {k: c for k, c in self.cooc.items() if k in keep}
        pairs = [k for k, c in self.cooc.items()
                 if c >= MIN_COUNT
                 and not self._is_background(k[0])
                 and not self._is_background(k[1])]
        try:
            with open(self.links_path, "w", encoding="utf-8") as f:
                f.write(
                    f"--- AURA TEMPORAL LOBE (v1) | VAULT_SIZE: {self.vault_size} "
                    f"| RECORDS: {self.record_count} "
                    f"| WORDS: {len(self.freq)} | PAIRS: {len(pairs)} ---\n"
                )
                for w in sorted(self.freq):
                    f.write(f"WORD: {w} {self.freq[w]}\n")
                for a, b in sorted(pairs):
                    count = self.cooc[(a, b)]
                    f.write(
                        f"COOC: '{a}' <-> '{b}' | COUNT: {count} "
                        f"| STRENGTH: {self.strength(a, b):.4f}\n"
                    )
        except Exception as e:
            print(f"[Temporal] Save friction: {e}")

    def load(self):
        """Restore the graph from temporal_links.txt."""
        freq = {}
        cooc = {}
        vault_size = 0
        record_count = 0
        with open(self.links_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("---") and "VAULT_SIZE:" in line:
                    for field in ("VAULT_SIZE:", "RECORDS:"):
                        if field not in line:
                            continue
                        try:
                            value = int(line.split(field)[1].split("|")[0].strip())
                        except (ValueError, IndexError):
                            value = 0
                        if field == "VAULT_SIZE:":
                            vault_size = value
                        else:
                            record_count = value
                elif line.startswith("WORD: "):
                    try:
                        parts = line[len("WORD: "):].rsplit(" ", 1)
                        freq[parts[0]] = int(parts[1])
                    except (ValueError, IndexError):
                        continue
                elif line.startswith("COOC: "):
                    try:
                        pair_part = line.split("|")[0][len("COOC: "):]
                        left, right = re.findall(r"[a-zA-Z]+", pair_part)[:2]
                        count_part = line.split("COUNT:")[1].split("|")[0].strip()
                        count = int(count_part)
                        key = (left, right) if left <= right else (right, left)
                        cooc[key] = count
                    except (ValueError, IndexError):
                        continue
        self.freq         = freq
        self.cooc         = cooc
        self.vault_size   = vault_size
        self.record_count = record_count
        self._attempted.clear()

    # ── DAEMON ─────────────────────────────────────────────────────
    def run(self):
        """Live watch loop: ingest vault growth, promote, save (throttled)."""
        print("--- AURA TEMPORAL LOBE: CO-OCCURRENCE STATISTICS ACTIVE ---")
        last_save = time.time()
        while True:
            try:
                n = self.scan_vault()
                if n:
                    print(
                        f"[Temporal] Ingested {n} records — "
                        f"{len(self.freq)} words, {len(self.cooc)} tracked pairs."
                    )
                    try:
                        promoted = self.promote_to_field()
                        if promoted:
                            print(f"[Temporal] Wired {promoted} pair(s) into the field.")
                    except Exception as e:
                        print(f"[Temporal] Promotion friction: {e}")
                if n and time.time() - last_save >= SAVE_INTERVAL:
                    self.save()
                    last_save = time.time()
            except Exception as e:
                print(f"[Temporal] Friction: {e}")
            time.sleep(CYCLE_SECONDS)


def run_temporal_lobe():
    lobe = TemporalLobe()
    if os.path.exists(TEMPORAL_LINKS):
        try:
            lobe.load()
            print(f"[Temporal] Link file restored ({len(lobe.freq)} words).")
        except Exception as e:
            print(f"[Temporal] Link file unreadable ({e}) — rebuilding.")
            lobe = TemporalLobe()
    ingested = lobe.scan_vault()
    print(
        f"[Temporal] Boot scan complete: {ingested} new records, "
        f"{len(lobe.freq)} words, {len(lobe.cooc)} tracked pairs."
    )
    lobe.save()
    lobe.run()


if __name__ == "__main__":
    run_temporal_lobe()
