# ukft_trigram.py — AURA Vault-Trained Trigram Engine (Phase 3-A)
# ================================================================
# Real language from absorbed data.  The engine trains trigram (and
# bigram) statistics on every vault record — the concept title and the
# DATA sentences — and generates new sentences by sampling the learned
# distributions, seeded with the query's concepts.
#
#   Training   — incremental: byte-offset resume like the temporal lobe,
#                with a freq>=2 gate so rare words never bloat the graph.
#   Generation — trigram -> bigram -> unigram backoff, weighted random
#                sampling, so the same question produces different
#                wording every time (Phase 3 gate) while the seeded
#                concepts keep the answer topically coherent.
#   Persistence — trigram_model.txt (VOCAB / BIGRAM / TRIGRAM lines +
#                 VAULT_SIZE header); rebuilt transparently on rewrite.
# ======================================================

import os
import random
import re
import time

from aura_constants import TRIGRAM_MODEL, VAULT_FILE
from aura_vault_io import (parse_vault_line, repair_hyphenation,
                           HYPHEN_STOP as FRAG_STOP, is_junk_text)

S_START = "<S>"
S_END   = "<E>"

# ── TUNING ────────────────────────────────────────────────────────
MIN_WORD_FREQ        = 3     # generation vocabulary floor
MAX_SENTENCE_TOKENS  = 40    # sentence length cap during training
MAX_GENERATED_WORDS  = 28    # generation length cap
MIN_SENTENCE_WORDS   = 6     # <E> suppressed until this many words spoken
PERSIST_MIN_COUNT    = 1     # bigrams/trigrams below this are not saved
CYCLE_SECONDS        = 10    # vault watch cadence
SAVE_INTERVAL        = 60.0  # seconds between model saves while growing
ATTESTED_MIN_COUNT   = 2     # whole-word attestations before fragments join

SINGLE_CHAR_OK = {"a", "i"}


def _clean_token(w):
    w = w.lower()
    if w in SINGLE_CHAR_OK:
        return w
    # ASCII only: Unicode letters ("χ", "á") glued to words pass
    # str.isalpha() but are corpus noise to the language model.
    if len(w) >= 2 and w.isascii() and w.isalpha():
        return w
    return None


def _join_fragments(tokens, attested):
    """
    Rejoin plain-space syllable splits ("mar riage" -> "marriage",
    "je ru sa lem" -> "jerusalem").  A group of 2-4 adjacent fragments is
    joined, longest first, only when the concatenation exists as a whole
    word elsewhere in the corpus AND the group is not all function words
    ("may be" must never collapse).  Longest-first prevents a suffix pair
    like "sa lem" from gluing into the attested word "salem" before the
    full "jerusalem" join gets a chance.
    """
    out = []
    i = 0
    n = len(tokens)
    while i < n:
        joined = None
        for k in range(4, 1, -1):
            if i + k > n:
                continue
            group = tokens[i:i + k]
            if all(t in FRAG_STOP for t in group):
                continue
            cand = "".join(group)
            if cand in attested:
                joined = cand
                i += k
                break
        if joined:
            out.append(joined)
        else:
            out.append(tokens[i])
            i += 1
    return out


def _sentences(text, attested=None):
    """
    Split DATA text into token lists (3+ tokens each).  Hyphenation and
    syllable splits from PDF extraction are rejoined so the model learns
    whole words, not fragments.
    """
    out = []
    for chunk in re.split(r"[.!?\n]+", text):
        # Scanned-page OCR garbage carries no language to learn.
        if is_junk_text(chunk):
            continue
        toks = [_clean_token(w) for w in repair_hyphenation(chunk).split()]
        toks = [t for t in toks if t]
        if attested:
            toks = _join_fragments(toks, attested)
        if len(toks) >= 3:
            out.append(toks[:MAX_SENTENCE_TOKENS])
    return out


class TrigramEngine:
    def __init__(self, vault_path=VAULT_FILE, model_path=TRIGRAM_MODEL,
                 rng=None):
        self.vault_path = vault_path
        self.model_path = model_path
        self.rng        = rng if rng is not None else random.Random()
        self.vocab      = {}            # word -> record count
        self.bigrams    = {}            # (a,) -> {b: count}
        self.trigrams   = {}            # (a, b) -> {c: count}
        self.vault_size = 0
        self.record_count = 0
        self._unigram_cache = None
        self._whole    = {}            # raw whole-token counts (pre-repair)
        self._attested = set()         # whole words attested in the corpus
        self._attested_ready = False

    # ── ATTESTED VOCABULARY ────────────────────────────────────────
    def rebuild_attested(self):
        """One full pass over the vault to find whole-word attestations."""
        self._whole = {}
        self._attested = set()
        if not os.path.exists(self.vault_path):
            self._attested_ready = True
            return
        with open(self.vault_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parsed = parse_vault_line(line)
                if not parsed:
                    continue
                concept, data, _ = parsed
                for text in (concept, repair_hyphenation(data)):
                    for t in re.findall(r"[a-zA-Z]+", text.lower()):
                        t = _clean_token(t)
                        if t:
                            self._whole[t] = self._whole.get(t, 0) + 1
        self._attested = {w for w, c in self._whole.items()
                          if c >= ATTESTED_MIN_COUNT}
        self._attested_ready = True

    # ── TRAINING ───────────────────────────────────────────────────
    def _train_sentence(self, raw_tokens, end=True):
        toks = []
        for w in raw_tokens:
            t = _clean_token(w)
            if t:
                toks.append(t)
        if not toks:
            return

        seq = [S_START, S_START] + toks + ([S_END] if end else [])

        for w in toks:
            self.vocab[w] = self.vocab.get(w, 0) + 1

        # Context gating: the context words (a, b) must be established
        # in the corpus (whole-count >= 2) before their sequences are
        # tracked — rare words are noise to a language model.  The
        # continuation word c is never gated: variety comes from the
        # long tail of continuations, and gating it starves small
        # corpora into empty distributions.
        for i in range(len(seq) - 2):
            a, b, c = seq[i], seq[i + 1], seq[i + 2]
            if a != S_START and self._whole.get(a, 0) < 2:
                continue
            if b != S_START and self._whole.get(b, 0) < 2:
                continue
            dist = self.trigrams.setdefault((a, b), {})
            dist[c] = dist.get(c, 0) + 1

        for i in range(len(seq) - 1):
            a, b = seq[i], seq[i + 1]
            if a != S_START and self._whole.get(a, 0) < 2:
                continue
            dist = self.bigrams.setdefault((a,), {})
            dist[b] = dist.get(b, 0) + 1

    def train_record(self, concept, data, source=None, count_whole=True):
        self.record_count += 1
        # Update the raw whole-token counts first so growth records can
        # attest new words for the fragment-repair pass — unless the
        # caller just rebuilt those counts over the same range (fresh
        # boot / rewrite rescan), in which case counting again would
        # double every token and attest singletons.
        for text in (concept, repair_hyphenation(data)):
            for t in re.findall(r"[a-zA-Z]+", text.lower()):
                t = _clean_token(t)
                if t and count_whole:
                    self._whole[t] = self._whole.get(t, 0) + 1
                    if self._whole[t] >= ATTESTED_MIN_COUNT:
                        self._attested.add(t)
        # Concept titles are labels, not sentences: trained without the
        # end marker so they never teach "<concept> -> <E>" terminations.
        self._train_sentence(concept.split(), end=False)
        for sentence in _sentences(data, attested=self._attested):
            self._train_sentence(sentence)

    def _parse_new(self, offset):
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
        """Train on every vault record not yet seen. Returns records ingested."""
        offset = self.vault_size if offset is None else offset
        size, records = self._parse_new(offset)
        count_whole = True
        if size < offset:
            self.vocab.clear()
            self.bigrams.clear()
            self.trigrams.clear()
            self.record_count = 0
            self._unigram_cache = None
            self.rebuild_attested()
            count_whole = False   # rebuilt counts cover these records
            size, records = self._parse_new(0)
        elif not self._attested_ready:
            # First scan in this process: fragment repair and context
            # gating need the whole-corpus attestation pass first.
            self.rebuild_attested()
            count_whole = False   # same range, already counted

        ingested = 0
        for concept, data, source in records:
            self.train_record(concept, data, source,
                              count_whole=count_whole)
            ingested += 1
        self.vault_size = size
        self._unigram_cache = None
        return ingested

    # ── GENERATION ─────────────────────────────────────────────────
    def is_trained(self):
        return len(self.vocab) > 0

    def in_vocab(self, word):
        """True when `word` can act as a generation seed."""
        t = _clean_token(word)
        return bool(t) and self.vocab.get(t, 0) >= MIN_WORD_FREQ

    def _unigram(self):
        if self._unigram_cache is None:
            self._unigram_cache = [
                (w, c) for w, c in self.vocab.items()
                if c >= MIN_WORD_FREQ and w not in (S_START, S_END)
            ]
        return self._unigram_cache

    def _sample(self, dist, allow_end=True):
        if not dist:
            return None
        items = list(dist.items())
        if not allow_end:
            items = [(w, c) for w, c in items if w != S_END]
            if not items:
                return None
        return self._sample_items(items)

    def _sample_items(self, items):
        if not items:
            return None
        total = sum(c for _, c in items)
        r = self.rng.random() * total
        for w, c in items:
            r -= c
            if r <= 0:
                return w
        return items[-1][0]

    def _unigram_sample(self):
        cache = self._unigram()
        return self._sample_items(cache) if cache else None

    def _bigram_sample(self, prev, allow_end=True):
        return self._sample(self.bigrams.get((prev,)), allow_end=allow_end)

    def _trigram_sample(self, a, b, allow_end=True):
        return self._sample(self.trigrams.get((a, b)), allow_end=allow_end)

    def _seed_tokens(self, seed_words):
        """First vocab-resident seed words, in order given."""
        tokens = []
        for w in seed_words:
            t = _clean_token(w)
            if t and self.vocab.get(t, 0) >= MIN_WORD_FREQ and t not in tokens:
                tokens.append(t)
                if len(tokens) >= 2:
                    break
        return tokens

    def generate(self, seed_words, max_words=MAX_GENERATED_WORDS):
        """
        Generate one sentence seeded with `seed_words`.
        Returns "" when the model has no usable vocabulary.
        """
        if not self.is_trained():
            return ""

        tokens = self._seed_tokens(seed_words)
        if not tokens:
            first = self._unigram_sample()
            if first is None:
                return ""
            tokens = [first]
        if len(tokens) == 1:
            nxt = self._bigram_sample(tokens[-1])
            if nxt is None or nxt == S_END:
                nxt = self._unigram_sample()
            if nxt and nxt != S_END:
                tokens.append(nxt)

        while len(tokens) >= 2 and len(tokens) < max_words:
            a, b = tokens[-2], tokens[-1]
            # The end marker stays suppressed until a minimum sentence
            # length is spoken — dominant <E> continuations (e.g.
            # "jesus christ.") used to kill the utterance instantly.
            allow_end = len(tokens) >= MIN_SENTENCE_WORDS
            nxt = self._trigram_sample(a, b, allow_end=allow_end)
            if nxt is None:
                nxt = self._bigram_sample(b, allow_end=allow_end)
            if nxt is None:
                nxt = self._unigram_sample()
            if nxt is None or nxt == S_END:
                break
            tokens.append(nxt)

        text = " ".join(tokens).strip()
        if not text:
            return ""
        text = text[0].upper() + text[1:]
        return text + "."

    # ── PERSISTENCE ────────────────────────────────────────────────
    def _prune(self, cap=200000):
        """Worst-case bound on RAM/model size: keep the best-counted
        entries past `cap`.  Live vocab (~25k) never comes close; this
        only caps pathological futures, never today's knowledge."""
        if len(self.vocab) > cap:
            keep = set(sorted(self.vocab, key=lambda w: -self.vocab[w])[:cap])
            self.vocab = {w: c for w, c in self.vocab.items() if w in keep}
            self.bigrams = {k: v for k, v in self.bigrams.items()
                            if k[0] in keep}
            self.trigrams = {k: v for k, v in self.trigrams.items()
                             if k[0] in keep and k[1] in keep}

    def save(self, min_count=PERSIST_MIN_COUNT):
        self._prune()
        try:
            with open(self.model_path, "w", encoding="utf-8") as f:
                f.write(
                    f"--- AURA TRIGRAM MODEL (v1) | VAULT_SIZE: {self.vault_size} "
                    f"| RECORDS: {self.record_count} "
                    f"| VOCAB: {len(self.vocab)} | BIGRAMS: {len(self.bigrams)} "
                    f"| TRIGRAMS: {len(self.trigrams)} ---\n"
                )
                for w in sorted(self.vocab):
                    f.write(f"V: {w} {self.vocab[w]}\n")
                for (a,), dist in sorted(self.bigrams.items()):
                    for b, c in sorted(dist.items()):
                        if c >= min_count:
                            f.write(f"B: {a} {b} {c}\n")
                for (a, b), dist in sorted(self.trigrams.items()):
                    for c, n in sorted(dist.items()):
                        if n >= min_count:
                            f.write(f"T: {a} {b} {c} {n}\n")
        except Exception as e:
            print(f"[Trigram] Save friction: {e}")

    def load(self):
        vocab = {}
        bigrams = {}
        trigrams = {}
        vault_size = 0
        record_count = 0
        with open(self.model_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("---") and "VAULT_SIZE:" in line:
                    for field, kind in (("VAULT_SIZE:", "size"),
                                        ("RECORDS:", "records")):
                        if field not in line:
                            continue
                        try:
                            value = int(line.split(field)[1].split("|")[0].strip())
                        except (ValueError, IndexError):
                            value = 0
                        if kind == "size":
                            vault_size = value
                        else:
                            record_count = value
                elif line.startswith("V: "):
                    try:
                        parts = line[3:].rsplit(" ", 1)
                        vocab[parts[0]] = int(parts[1])
                    except (ValueError, IndexError):
                        continue
                elif line.startswith("B: "):
                    try:
                        a, b, c = line[3:].split()
                        bigrams.setdefault((a,), {})[b] = int(c)
                    except ValueError:
                        continue
                elif line.startswith("T: "):
                    try:
                        a, b, c, n = line[3:].split()
                        trigrams.setdefault((a, b), {})[c] = int(n)
                    except ValueError:
                        continue
        self.vocab      = vocab
        self.bigrams    = bigrams
        self.trigrams   = trigrams
        self.vault_size = vault_size
        self.record_count = record_count
        self._unigram_cache = None
        self._whole = {}
        self._attested = set()
        self._attested_ready = False   # forces a rebuild pass before training


def run_trigram_engine():
    print("--- AURA TRIGRAM ENGINE: VAULT LANGUAGE MODEL ACTIVE ---")
    eng = TrigramEngine()
    if os.path.exists(TRIGRAM_MODEL):
        try:
            eng.load()
            print(f"[Trigram] Model restored ({len(eng.vocab)} words).")
        except Exception as e:
            print(f"[Trigram] Model unreadable ({e}) — rebuilding.")
            eng = TrigramEngine()
    # First scan rebuilds attestation internally (scan_vault covers
    # it) — a separate rebuild here would count the whole vault twice.
    ingested = eng.scan_vault()
    print(
        f"[Trigram] Boot scan complete: {ingested} new records, "
        f"{len(eng.vocab)} words, {len(eng.trigrams)} trigrams."
    )
    eng.save()
    last_save = time.time()
    while True:
        try:
            n = eng.scan_vault()
            if n:
                print(
                    f"[Trigram] Ingested {n} records — "
                    f"{len(eng.vocab)} words, {len(eng.trigrams)} trigrams."
                )
            if n and time.time() - last_save >= SAVE_INTERVAL:
                eng.save()
                last_save = time.time()
        except Exception as e:
            print(f"[Trigram] Friction: {e}")
        time.sleep(CYCLE_SECONDS)


if __name__ == "__main__":
    run_trigram_engine()
