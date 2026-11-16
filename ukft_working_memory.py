# ukft_working_memory.py — AURA Working Memory Buffer (Phase 3-B, G7 repair)
# ================================================================
# Context held across conversation turns.  The buffer remembers the last
# few exchanges (query, winner, concepts) and resolves referential
# follow-ups — "what about it?", "tell me more" — by carrying the
# previous topic forward.
#
#   - Turns capped at MAX_TURNS (a real working memory is small).
#   - A referential query (no content words after stop filtering) inherits
#     the previous turn's concepts instead of opening a new topic.
#   - Persisted to working_memory.txt so a reboot keeps the thread of
#     conversation.
#
# G7 repair (Sept 2026): the buffer was concept-only — it stored HER
# nothing (no Aura replies), so follow-ups could never be understood
# as dialogue.  A turn now stores BOTH sides (query + response), and
# the module answers genuinely conversational questions over them:
# ordered USER/AURA dialogue, her last open question, pronoun/reference
# resolution against recent referents, and whether the current input
# warrants a conversational continuation.  Long-term memory is
# untouched — this layer holds the CURRENT conversation only.
# ======================================================

import re
import time
from collections import deque

from aura_constants import WORKING_MEMORY
from aura_vault_io import SEED_STOP

MAX_TURNS = 8

# Turns rendered into prompts (bounded — the 3B parrots long briefs).
DIALOGUE_TURNS = 3
# One stored line is capped so a multi-line EXECUTE dump can never
# shred the line-oriented persistence format.
STORE_CHARS = 280

# Third-person pronouns that need a conversational referent.  First
# and second person (I/you/we) are deictic, never resolved.
PRONOUNS = frozenset({
    "it", "its", "that", "this", "these", "those",
    "they", "them", "their", "theirs",
    "he", "him", "his", "she", "her", "hers",
})
GENDERED = frozenset({
    "he", "him", "his", "she", "her", "hers",
})

# Vague noun phrases that behave like pronouns ("that thing" means
# whatever the thread is about, not a new topic).
VAGUE_HEADS = frozenset({
    "thing", "things", "stuff", "one", "ones", "bit",
    "part", "idea", "deal", "situation",
})

# Explicit topic pivots: the speaker is leaving the thread, not
# continuing it ("Anyway, what do you think about AI?").
SHIFT_RE = (r"^(anyway|by the way|btw|on another note|changing the "
            r"subject|that aside|meanwhile|also|oh,? (hey|btw))\b[,. ]*")

# Words never echoed back in a spoken receipt (grounded, not crude).
PROFANITY = frozenset({
    "fuck", "fucked", "fucking", "shit", "shitty", "damn",
    "bitch", "asshole", "dick", "piss", "crap",
})

# Time fillers: thread about "today" is never about today.
TIME_FILLER = frozenset({
    "today", "yesterday", "tomorrow", "tonight", "now",
    "lately", "recently", "morning", "evening", "afternoon",
})

# Never referents: discourse glue, her template verbs, generic
# cognition verbs, contraction fragments ("weve", "whats" — the
# apostrophe stump, never the topic). Without these, "Yeah, that
# is what I am considering" elects 'considering' the topic
# instead of 'Durban'.
REFERENT_SKIP = TIME_FILLER | frozenset({
    "yeah", "yes", "no", "okay", "ok", "well", "oh", "ah",
    "hmm", "hey", "hi", "hello", "please", "thanks", "thank",
    "sorry", "right", "sure", "maybe", "just", "really", "very",
    "still", "also", "even", "ever", "never", "always",
    "considering", "consider", "suppose", "supposing", "guess",
    "wonder", "wondering", "heard", "hear", "stands", "stand",
    "stood", "else", "got", "getting", "going", "thing", "things",
    "weve", "ive", "youve", "theyve", "im", "dont", "cant",
    "wont", "isnt", "arent", "wasnt", "werent", "didnt",
    "doesnt", "couldnt", "shouldnt", "wouldnt", "aint",
    "thats", "whats", "lets", "heres", "theres", "whos",
})

# Capitalized tokens that are sentence grammar, never names ("Yeah"
# at a sentence start is agreement, not a person).
COMMON_CAPS = frozenset({
    "the", "a", "an", "what", "who", "where", "when", "why",
    "how", "is", "are", "was", "were", "do", "does", "did",
    "can", "could", "would", "should", "will", "yeah", "yes",
    "no", "okay", "ok", "well", "so", "but", "and", "then",
    "there", "that", "this", "these", "those", "it", "its",
    "he", "she", "they", "we", "you", "your", "my", "our",
    "hi", "hello", "hey", "good", "thanks", "thank", "please",
    "actually", "really", "just", "still", "now", "today",
    "got", "tell", "shall", "let", "oh", "ah", "hmm", "yesterday",
})


def _clean_stored(text, limit=STORE_CHARS):
    """One flat line: no newlines, no field separators, capped."""
    flat = " ".join(str(text or "").split())
    flat = flat.replace(" | ", " / ")
    if len(flat) > limit:
        cut = flat[:limit].rfind(" ")
        flat = (flat[:cut] if cut > 40 else flat[:limit]).rstrip()
    return flat


def strip_prefix(text):
    """Drop one leading speaker stamp ("[AURA]: ...") for display."""
    return re.sub(r"^\s*(?:\[?AURA\]?:\s*)+", "",
                  str(text or "").strip())


class WorkingMemory:
    def __init__(self, path=WORKING_MEMORY, max_turns=MAX_TURNS):
        self.path      = path
        self.max_turns = max_turns
        self.turns     = deque(maxlen=max_turns)

    # ── REFERENTIAL DETECTION ──────────────────────────────────────
    @staticmethod
    def content_words(query):
        """Query words that can carry meaning (stop words stripped)."""
        return [w for w in re.findall(r"[a-zA-Z]+", query.lower())
                if w not in SEED_STOP]

    def is_referential(self, query):
        """True when the query has no content of its own."""
        return not self.content_words(query)

    # ── TURN BUFFER ────────────────────────────────────────────────
    def remember(self, query, concepts, winner, response=""):
        """
        Record a turn.  Referential queries inherit the previous turn's
        concepts so the thread of conversation is carried, not restarted.
        `response` is HER spoken line for this turn (stored so the next
        turn can be understood as dialogue, not as an isolated query).
        """
        if self.is_referential(query) and self.turns:
            concepts = self.turns[-1]["concepts"]
        self.turns.append({
            "ts":       time.time(),
            "query":    _clean_stored(query),
            "response": _clean_stored(response),
            "winner":   winner,
            "concepts": [c for c in concepts if c],
        })

    def amend_last_response(self, response):
        """Replace the last turn's stored reply (the immersive voice
        speaks AFTER the engine template was stored — her remembered
        words must be what she actually said)."""
        if not self.turns:
            return
        self.turns[-1]["response"] = _clean_stored(response)
        self.save()

    def recent_concepts(self, limit=6):
        """Most recent concepts first, deduplicated."""
        out = []
        for turn in reversed(self.turns):
            for c in turn["concepts"]:
                if c not in out:
                    out.append(c)
                    if len(out) >= limit:
                        return out
        return out

    def recent_topic(self, limit=3):
        """
        The content words of the most recent NON-referential turn — the
        actual topic being discussed.  recent_concepts() mixes in the
        matched anchor's title words ("dokumen", "pub"), which are noise
        when a follow-up needs to name the topic.
        """
        for turn in reversed(self.turns):
            words = self.content_words(turn["query"])
            if words:
                return words[:limit]
        return []

    def last_winner(self):
        return self.turns[-1]["winner"] if self.turns else None

    # ── PERSISTENCE ────────────────────────────────────────────────
    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                f.write(f"--- AURA WORKING MEMORY (v1) | TURNS: {len(self.turns)} ---\n")
                for t in self.turns:
                    f.write(
                        f"TURN: {t['ts']:.0f} | WINNER: {t['winner']} | "
                        f"CONCEPTS: {' '.join(t['concepts'])} | QUERY: {t['query']} | "
                        f"RESP: {t.get('response', '')}\n"
                    )
        except Exception:
            pass

    def load(self):
        """Restore turns from disk; missing file is a clean no-op.
        Pre-G7 lines without RESP still load (her reply is empty)."""
        if not __import__("os").path.exists(self.path):
            return
        # Reset first: loading twice (constructor + explicit load, as
        # the stress battery does) must not duplicate every turn.
        # Keep the deque (not a bare list) so the cap survives reloads.
        self.turns = deque(maxlen=self.max_turns)
        try:
            with open(self.path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line.startswith("TURN: "):
                        continue
                    m = re.match(
                        r"^TURN: (\S+) \| WINNER: (.*?) \| CONCEPTS: (.*?)"
                        r" \| QUERY: (.*)$",
                        line.rstrip("\n"))
                    if not m:
                        continue
                    try:
                        ts = float(m.group(1))
                        winner = m.group(2).strip()
                        concepts = m.group(3).split()
                        query, response = self._split_query_resp(m.group(4))
                    except (ValueError, IndexError):
                        continue
                    self.turns.append({
                        "ts": ts, "query": query,
                        "response": response,
                        "winner": winner, "concepts": concepts,
                    })
        except Exception:
            pass

    @staticmethod
    def _split_query_resp(qr):
        """New lines carry 'QUERY: <q> | RESP: <r>'; legacy lines
        carry the query alone.  Split on the LAST separator so a
        literal in either half cannot corrupt the parse."""
        if " | RESP: " in qr:
            query, response = qr.rsplit(" | RESP: ", 1)
            return query.strip(), response.strip()
        return qr.strip(), ""

    # ── DIALOGUE (G7: both sides of the conversation) ─────────────
    def last_response(self):
        """Her last spoken line, stamp-stripped, or ''."""
        if not self.turns:
            return ""
        return strip_prefix(self.turns[-1].get("response", ""))

    def open_question(self, limit=140):
        """Her last line when it was a question (the pending thread
        a short answer resolves against), else ''."""
        resp = self.last_response().strip()
        if resp.endswith("?"):
            return resp[:limit].strip()
        return ""

    def recent_dialogue(self, n=DIALOGUE_TURNS):
        """Ordered [{speaker, text}] for the last n turns, oldest
        first — USER and AURA lines interleaved, exact recent wording
        kept.  Turns with an empty reply (legacy files) contribute
        the user line only."""
        out = []
        for t in list(self.turns)[-n:]:
            if t.get("query"):
                out.append({"speaker": "user", "text": t["query"]})
            resp = strip_prefix(t.get("response", ""))
            if resp:
                out.append({"speaker": "aura", "text": resp})
        return out

    def dialogue_before_current(self, n=DIALOGUE_TURNS):
        """Dialogue excluding the turn just stored (the live prompt
        already carries the current message separately)."""
        lines = self.recent_dialogue(n + 1)
        if not lines:
            return []
        # Drop the newest turn: its trailing USER line (+ her reply).
        drop = 0
        for entry in reversed(lines):
            drop += 1
            if entry["speaker"] == "user":
                break
        return lines[:-drop] if drop < len(lines) else []

    def dialogue_block(self, n=DIALOGUE_TURNS, width=120):
        """Prompt-ready block: 'USER: ...' / 'AURA: ...' lines."""
        lines = []
        for entry in self.recent_dialogue(n):
            who = "USER" if entry["speaker"] == "user" else "AURA"
            text = " ".join(str(entry["text"]).split())
            if len(text) > width:
                cut = text[:width].rfind(" ")
                text = (text[:cut] if cut > 20 else text[:width]).rstrip()
            lines.append(f"{who}: {text}")
        return "\n".join(lines)

    # ── REFERENTS (what pronouns point at) ────────────────────────
    def candidate_referents(self, extra_names=(), limit=6):
        """Most-likely-first [(phrase, is_name)] for the recent
        thread.  Scored, not positional: HIS query words weigh
        double (her template echoes must not elect 'considering'
        the topic), recent turns weigh more, time fillers are
        penalized.  Only the last 3 turns count — stale turns
        cannot hijack 'it'."""
        known = {str(x).lower() for x in (extra_names or []) if x}
        scores, qscores, last_seen, flags = {}, {}, {}, {}
        turns = list(self.turns)[-3:]

        def looks_name(raw, sent_start, sent_len):
            low = (raw or "").lower()
            if low in known:
                return True
            if sent_start and sent_len > 3:
                # Long sentences open with grammar, not names.
                return False
            return bool(re.match(r"^[A-Z][a-z]+$", raw or "")) \
                and low not in COMMON_CAPS and low not in SEED_STOP

        for ti, turn in enumerate(turns):
            # Recency DOUBLES per turn: the newest turn's topic owns
            # pronouns absolutely (six repeated older turns must not
            # outvote the thread being spoken about right now).
            rec = 2 ** ti
            for pos, (raw, low, start, slen) in enumerate(
                    self._sent_tokens(turn.get("query", ""))):
                if low in PROFANITY or len(low) < 2:
                    continue
                scores[low] = scores.get(low, 0) + 2 * rec
                qscores[low] = qscores.get(low, 0) + 2 * rec
                last_seen[low] = (ti, pos)
                if looks_name(raw, start, slen):
                    flags[low] = True
            for pos, (raw, low, start, slen) in enumerate(
                    self._sent_tokens(
                        strip_prefix(turn.get("response", "")))):
                if low in PROFANITY or len(low) < 2:
                    continue
                scores[low] = scores.get(low, 0) + 1 * rec
                last_seen[low] = (ti, pos)
                # Her receipts open with the topic capitalized by
                # construction ("Car — ...") — never a name from
                # position alone; known people still count.
                if looks_name(raw, True, 99):
                    flags[low] = True
        for w in REFERENT_SKIP:
            scores.pop(w, None)
            qscores.pop(w, None)
        # Score, then query-support (his words outrank her echoes),
        # then shorter (heads over modifiers: 'engine', not
        # 'running'), then recency.
        ranked = sorted(scores,
                        key=lambda w: (-scores[w], -qscores.get(w, 0),
                                       len(w),
                                       -last_seen.get(w, (0, 0))[0],
                                       -last_seen.get(w, (0, 0))[1]))
        out = []
        for w in ranked:
            if w in {p.lower() for p, _ in out}:
                continue
            is_name = bool(flags.get(w, False))
            out.append((w if not is_name else self._name_form(w),
                        is_name))
            if len(out) >= limit:
                break
        return out

    @staticmethod
    def _content_tokens(text):
        """[(raw, lowered)] content words — case preserved so names
        survive (content_words lowercases everything)."""
        out = []
        for tok in re.findall(r"[A-Za-z][A-Za-z']*", str(text or "")):
            low = tok.lower()
            if low not in SEED_STOP:
                out.append((tok, low))
        return out

    @staticmethod
    def _sent_tokens(text):
        """[(raw, lowered, sent_start, raw_len)] — sent_start means
        RAW sentence-initial ('Car — ...' opens a sentence; 'Sarah'
        in 'I spoke to Sarah' does not, even though stop-words
        precede it).  raw_len counts every word (pre stop-filter),
        so short exclamations ('Sarah took it') still name heads."""
        for sent in re.split(r"[.!?]+\s*", str(text or "")):
            raw_all = re.findall(r"[A-Za-z][A-Za-z']*", sent)
            for ri, tok in enumerate(raw_all):
                low = tok.lower()
                if low in SEED_STOP:
                    continue
                yield tok, low, ri == 0, len(raw_all)

    def _name_form(self, lowered):
        """Best display form of a name seen lowercase: scan recent
        dialogue for its capitalized shape, else title-case."""
        for turn in reversed(list(self.turns)[-3:]):
            for text in (turn.get("query", ""),
                         strip_prefix(turn.get("response", ""))):
                for tok in re.findall(r"[A-Za-z][A-Za-z']*", str(text)):
                    if tok.lower() == lowered \
                            and re.match(r"^[A-Z][a-z]+$", tok):
                        return tok
        return lowered[:1].upper() + lowered[1:]

    @staticmethod
    def pronouns_in(text):
        """Third-person pronouns present in the input, in order."""
        return [w for w in re.findall(r"[a-zA-Z]+", str(text or "").lower())
                if w in PRONOUNS]

    @staticmethod
    def vague_nps(text):
        """Vague noun phrases ('that thing') behaving as pronouns."""
        return re.findall(
            r"\b(that|the|this)\s+(thing|things|stuff|one|ones|bit|"
            r"part|idea|deal|situation)\b",
            str(text or ""), re.IGNORECASE)

    def resolve(self, text, extra_names=()):
        """Bind pronouns/vague NPs to recent referents.

        Returns (expanded, bindings): `expanded` is the input with
        each bound pronoun replaced by its phrase (for context-aware
        retrieval); `bindings` maps pronoun -> phrase for the trace.
        Gendered pronouns bind to NAMES only (never to a topic word);
        it/that/this/they bind to the top referent, name or topic.
        Unresolvable pronouns stay unbound — ambiguity must ask,
        never guess."""
        bindings = {}
        referents = self.candidate_referents(extra_names=extra_names)
        known = {str(x).lower() for x in (extra_names or []) if x}
        names = sorted(
            (p for p, is_name in referents if is_name),
            key=lambda p: p.lower() not in known)
        top, top_is_name = (referents[0] if referents
                            else ("", False))

        def _phrase():
            # Names stand alone ("Sarah"); topics take "the".
            return top if (top_is_name or top[:1].isupper()) \
                else "the " + top

        for p in self.pronouns_in(text):
            if p in bindings:
                continue
            if p in GENDERED:
                if names:
                    bindings[p] = names[0]
            elif top:
                bindings[p] = _phrase()
        if self.vague_nps(text) and top:
            bindings.setdefault("that~np", _phrase())
        expanded = str(text or "")
        for np_match in re.finditer(
                r"\b(that|the|this)\s+(thing|things|stuff|one|ones|bit|"
                r"part|idea|deal|situation)\b", expanded, re.IGNORECASE):
            if top:
                expanded = (expanded[:np_match.start()] + _phrase()
                            + expanded[np_match.end():])
                break
        for p, phrase in bindings.items():
            if p == "that~np":
                continue
            expanded = re.sub(r"\b" + re.escape(p) + r"\b", phrase,
                              expanded, count=1, flags=re.IGNORECASE)
        bindings.pop("that~np", None)
        if top and self.vague_nps(text):
            bindings["that thing"] = _phrase()
        return expanded, bindings

    # ── CONTINUATION (should the dialogue answer, not the vault?) ─
    def is_shift(self, text):
        """An explicit pivot away from the thread ('Anyway, ...')."""
        return bool(re.match(SHIFT_RE, str(text or "").strip(),
                             re.IGNORECASE))

    @staticmethod
    def substance_words(text):
        """Content words with vowels — real words, not 'qzxwv'.
        Gibberish keeps the honest dark fallback; substance earns a
        conversational receipt."""
        return [w for w in WorkingMemory.content_words(str(text or ""))
                if len(w) >= 3 and re.search(r"[aeiouy]", w)
                and w not in PROFANITY]

    def continuation_warranted(self, text, bindings=None):
        """True when the input is visibly part of the ongoing
        exchange: elliptical, pronominal, answering her question,
        pivoting — or carrying substance the thread can receipt
        ('Durban' after 'moving' beats 'no resonance').  Plain
        gibberish never counts ('qzxwv qzxwv' stays dark even
        mid-thread)."""
        if not self.turns:
            return False
        if self.is_referential(text):
            return True
        if bindings:
            return True
        if self.pronouns_in(text):
            return True
        # Answering her question counts — but gibberish ('qzxwv')
        # answers nothing and stays dark even with one pending.
        if self.open_question() and len(
                re.findall(r"[A-Za-z]+", str(text or ""))) <= 12 \
                and (self.substance_words(text)
                     or self.is_referential(text)):
            return True
        if self.is_shift(text):
            return True
        if self.substance_words(text):
            return True
        return False

    def clarification_needed(self, text):
        """Referential input with NO thread to resolve against (or a
        gendered pronoun with no name anywhere): asking beats the
        dark fallback."""
        if self.turns:
            pros = [p for p in self.pronouns_in(text) if p in GENDERED]
            if pros:
                names = [p for p, is_name
                         in self.candidate_referents() if is_name]
                if not names:
                    return True
            return False
        return bool(self.is_referential(text) or self.pronouns_in(text)
                    or self.vague_nps(text))

    def understanding_line(self, limit=160):
        """One short line for prompts: thread + pending question."""
        topic = " ".join(self.recent_topic(4) or [])
        bits = []
        if topic:
            bits.append("thread: " + topic)
        asked = self.open_question()
        if asked:
            bits.append("she asked: " + asked)
        line = "; ".join(bits) if bits else "new thread"
        return line[:limit]
