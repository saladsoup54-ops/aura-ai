# ukft_mouth.py — AURA Mouth (V6 C9, optional + swappable)
# ==================================================
# A small local model as a CONSTRAINED surface realizer — and
# the LAST output stage for every memory-backed answer (proof,
# people, recall, belief, agenda, confidence).  It receives ONLY
# what her memory already holds (proof facts, record terms,
# thread words), renders one fluent sentence, and is verified
# against those terms: dropped proof words, invented names,
# extra claims, or questions are rejected and the deterministic
# template speaks instead.  The model holds no knowledge and
# contributes none — prompts carry memory, never vault text,
# and never guesses (tested).
#
# Protocol speech (confirm/cancel questions, consent, policy
# lines) and associative guesses never come here: consent
# wording stays exact, and drift has nothing to verify
# against — that road ends in confabulation.
#
# Swappable and unpluggable: MOUTH_ENABLED=False, a dead
# daemon, a timeout, or AURA_NO_MOUTH=1 (the regression
# suites) all yield None, and she behaves exactly as today.
# Transport is Ollama's HTTP API (external, like the TTS
# voice) — no new Python dependency.  request_fn injects for
# tests so no suite ever needs a daemon.
# ==================================================

import os
import re
import time

from aura_constants import MOUTH_ENABLED, MOUTH_MODEL, MOUTH_TIMEOUT, \
    MOUTH_URL

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "of", "to",
    "in", "on", "at", "and", "or", "as", "by", "it", "its",
    "that", "this", "these", "those", "be", "been", "with",
}


def content_words(text):
    """Lowercased words that carry meaning (length + stop filter)."""
    return [w for w in re.findall(r"[a-z]+", str(text).lower())
            if len(w) > 2 and w not in STOPWORDS]


# Discourse glue the test contract sanctions as fluency — "truly"
# (c9, F5), "one" (F5 "one of the children"), "said" (F5 "it is
# said") — and nothing more.  Everything else the model emits must
# already live in the facts (same substring discipline as
# retention, both directions for inflections).  Live-daemon cause
# (16 Sept 2026): "...Maya who teaches my other sister" passed the
# old gate — lowercase, all proof words kept — inventing a family
# member.  "other" is in no fact and no glue, so it now falls
# back to the template.  Precision over recall, as always here.
GLUE_WORDS = {"truly", "one", "said"}


def _closed_vocab(output, vocab):
    """Every output content word is glue or already in the vocabulary."""
    for w in content_words(str(output or "").lower()):
        if w in GLUE_WORDS:
            continue
        if not any(f == w or f in w or w in f for f in vocab):
            return False
    return True


def prompt_for(sentence, facts):
    """The whole prompt: facts first, then the sentence to restate."""
    lines = ["Restate in one fluent sentence using ONLY these facts."]
    lines += [f"Fact: {f}" for f in facts]
    lines.append(f"Sentence: {sentence}")
    return "\n".join(lines)


def verify(output, facts):
    """
    True only when the output keeps every proof word, adds no
    capitalized strangers, asks nothing, and stays short.  The
    template fallback is always safer than a maybe.  Two matching
    disciplines, deliberately: proof-word RETENTION is substring-
    based (inflections like "mountains" for "mountain" are faithful
    fluency), but capitalized STRANGERS match whole-word only —
    "Son" no longer slips inside "Solomon"/"person", which is the
    actual confabulation vector (a fix-pass hardening).
    """
    text = " ".join(str(output or "").split())
    if not text or "?" in text:
        return False
    words = text.split()
    if len(words) > 60:
        return False
    fact_blob = " ".join(facts).lower()
    out_blob = text.lower()
    for w in content_words(fact_blob):
        if w not in out_blob:
            return False
    vocab = set()
    for f in facts:
        vocab.update(content_words(str(f).lower()))
    if not _closed_vocab(out_blob, vocab):
        return False
    fact_words = set(re.findall(r"[a-z]+", fact_blob))
    for m in re.finditer(r"\b[A-Z][a-z]+\b", text):
        # Sentence-initial capitals are grammar, not claims — but
        # only a real boundary counts (index 0, or ". " exactly two
        # back; m.start() == 1 would read text[-1], the string end).
        at_start = m.start() == 0 or (
            m.start() >= 2 and text[m.start() - 2] in ".!?")
        token = m.group(0).lower()
        if not at_start and token not in fact_words:
            return False
    return True


def split_claims(body):
    """
    One body into atomic claim-sentences, in order.  Unlike the
    quote ranker there is no length floor here — dropping a short
    claim ("Slate clean.") would lose information; every sentence
    speaks or falls back, none vanish.
    """
    parts = [s.strip() for s in
             re.split(r"(?<=[.!?])\s+", str(body or "").strip())
             if s.strip()]
    return parts if parts else ([str(body or "").strip()]
                                if str(body or "").strip() else [])


def verify_claim(output, claim, terms):
    """
    V7 F5: the per-claim gate.  The rephrase must keep every
    content word of ITS claim (substring retention, inflection-
    tolerant) and add no capitalized strangers beyond the claim
    plus the body's memory terms (whole-word precision).  Same
    question/length discipline as verify().
    """
    text = " ".join(str(output or "").split())
    if not text or "?" in text:
        return False
    if len(text.split()) > 60:
        return False
    claim_blob = str(claim or "").lower()
    out_blob = text.lower()
    for w in content_words(claim_blob):
        if w not in out_blob:
            return False
    vocab = set(content_words(claim_blob))
    for t in terms or []:
        vocab.update(content_words(str(t).lower()))
    if not _closed_vocab(out_blob, vocab):
        return False
    allowed = set(re.findall(r"[a-z]+", claim_blob))
    allowed |= set(re.findall(r"[a-z]+", " ".join(terms or []).lower()))
    for m in re.finditer(r"\b[A-Z][a-z]+\b", text):
        at_start = m.start() == 0 or (
            m.start() >= 2 and text[m.start() - 2] in ".!?")
        if not at_start and m.group(0).lower() not in allowed:
            return False
    return True


class Mouth:
    """One fluent sentence, verified — or silence (template speaks)."""

    def __init__(self, model=MOUTH_MODEL, url=MOUTH_URL,
                 timeout=MOUTH_TIMEOUT, request_fn=None, clock=time.time,
                 enabled=None):
        self.model = model
        self.url = (url or "").rstrip("/")
        self.timeout = timeout
        self.request_fn = request_fn
        self._clock = clock
        self._enabled = MOUTH_ENABLED if enabled is None \
            else enabled
        self._avail = (None, 0.0)   # (result, valid-until)

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
        """The daemon serves our model — cached, best-effort."""
        if not self._enabled or os.environ.get("AURA_NO_MOUTH") == "1":
            return False
        now = self._clock()
        if self._avail[0] is not None and now < self._avail[1]:
            return self._avail[0]
        try:
            resp = self._get("/api/tags", timeout=3)
            names = [m.get("name", "") for m in
                     resp.json().get("models", [])]
            ok = any(n == self.model or n.startswith(self.model + ":")
                     for n in names)
        except Exception:
            ok = False
        self._avail = (ok, now + ttl)
        return ok

    def render(self, sentence, facts):
        """Raw model text, or None on any failure.  Unverified."""
        if not self.available():
            return None
        try:
            resp = self._post("/api/generate",
                              {"model": self.model,
                               "prompt": prompt_for(sentence, facts),
                               "stream": False,
                               "options": {"temperature": 0,
                                           "num_predict": 60}},
                              timeout=self.timeout)
            return (resp.json().get("response") or "").strip() or None
        except Exception:
            return None

    def speak(self, sentence, facts):
        """
        The public path: verified fluency, else None (the caller
        falls back to the deterministic template — today's voice).
        """
        try:
            if not facts:
                return None
            out = self.render(sentence, facts)
            if out and verify(out, facts):
                return out
            return None
        except Exception:
            return None

    def speak_claims(self, body, terms):
        """
        V7 F5: claim-level grounding.  The body splits into atomic
        claims; the model phrases EACH and each is verified
        per-claim; survivors assemble in order while fallen claims
        speak their template — one bad claim costs a claim, never
        the voice, and no information is ever lost.  A single-claim
        body takes the legacy speak() path byte-identically; an
        unavailable mouth returns None without touching the body.
        """
        try:
            if not terms:
                return None
            if not self.available():
                return None
            claims = split_claims(body)
            if len(claims) <= 1:
                return self.speak(body, terms)
            terms = list(terms or [])
            out = []
            for claim in claims:
                try:
                    fluent = self.render(claim, terms)
                except Exception:
                    fluent = None
                if fluent and verify_claim(fluent, claim, terms):
                    out.append(" ".join(fluent.split()))
                else:
                    out.append(claim)
            return " ".join(out) if out else None
        except Exception:
            return None
