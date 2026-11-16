# ukft_quote.py — AURA Quote-First Fallback (V7 F2)
# ==================================================
# Unproven questions stop generating and start retrieving:
# the best real vault sentence for the question speaks, word
# for word as she crystallized it.  Relevance may miss;
# invention ends.  Quotes bypass the mouth (nothing to
# realize — the words are already hers) and carry no opener
# (receipts and variety for non-proof speech belong to F4
# policy; proofs keep their F1 openers).
#
# Deterministic by law: same anchors + same question give
# the same sentence, every time.  Stability is the point —
# a true sentence does not need three wordings.
# No state: ranking is a pure function, so there is nothing
# to cap, back up, or preflight.
# ==================================================

import re

MAX_CHARS = 240


def query_tokens(query):
    """Content tokens of the question (Broca's rule: len >= 3)."""
    return {w for w in re.findall(r"[a-z]+", (query or "").lower())
            if len(w) >= 3}


def whole_word_hit(query, anchors, stop=()):
    """
    Fix-pass: resonance for the honest-gap fallback must be
    whole-word ("who is zod" resonated on "zodiac" and quoted
    Aquarius instead of staying ignorant).  True when a
    non-stopword query token is a whole word of the top anchor.
    stop carries the caller's stopwords (the bridge passes
    SEED_STOP); empty by default.
    """
    stopset = set(stop or ())
    toks = {w for w in re.findall(r"[a-z]+", (query or "").lower())
            if len(w) >= 3 and w not in stopset}
    if not toks:
        return False
    for title, data in (anchors or [])[:1]:
        words = set(re.findall(
            r"[a-z]+", ((title or "") + " " + (data or "")).lower()))
        if toks & words:
            return True
    return False


def split_sentences(data):
    """Candidate sentences of one memory (Broca's rule: >= 20 chars)."""
    parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", data or "")
             if len(s.strip()) >= 20]
    if parts:
        return parts
    stripped = (data or "").strip()
    return [stripped] if stripped else []


def score_sentence(sentence, tokens):
    """
    How many query tokens the sentence carries: whole-word hits
    count double, substring-only hits single (a fix-pass
    hardening — "son" matching "person" is a weak signal, not a
    match, but still better than nothing for OCR-broken text).
    """
    lowered = sentence.lower()
    words = set(re.findall(r"[a-z]+", lowered))
    score = 0
    for t in tokens:
        if t in words:
            score += 2
        elif t in lowered:
            score += 1
    return score


def messiness(sentence):
    """
    OCR-noise load: digit runs (verse numbers), stub fragments
    and letter-spaced print ("C o m e").  Common two-letter glue
    words (is/a/of/…) never count — clean sentences must score
    near-zero, so mess only ever breaks near-ties toward the
    human sentence.  A preference, never a veto: a noisy true
    sentence still beats silence.
    """
    glue = {"a", "i", "is", "an", "of", "to", "in", "on", "at", "as",
            "by", "it", "or", "so", "up", "us", "we", "he", "me", "my",
            "do", "go", "no", "be", "am", "ox", "ex", "ad", "de", "la"}
    frags = re.findall(r"[A-Za-z]+", sentence or "")
    digits = sum(c.isdigit() for c in (sentence or ""))
    stubs = sum(1 for w in frags
                if len(w) <= 2 and w.lower() not in glue)
    spaced = len(re.findall(r"(?:\b[A-Za-z] ){2,}\b[A-Za-z]\b",
                            sentence or ""))
    return digits + 2 * stubs + 4 * spaced


def _clean_text(text):
    """
    OCR shelf marks are never speech: locus tags (/L50263),
    font-tag tokens (vertstroke/lengthmark composites), and pure
    phonetic slash-segments go; real words (and/or, his/her, w/o)
    stay.  Split-hyphen fragments rejoin only on safe seconds —
    grammatical suffixes and known compounds ("enjoy- ment",
    "play- ers", "after- noon") — never open-ended ("project- or",
    "well- known", "efer- ring" stay broken-honest; a false word
    is confabulation, a visible seam is not).
    """
    text = re.sub(r"\s*/L\d+\s*", " ", text)
    text = re.sub(r"\S*(vertstroke|lengthmark)\S*", " ", text)
    # Pure-phonetic slash segments (always carry non-ASCII) go;
    # "24/7", "and/or", "his/her" have none and stay.
    text = re.sub(r"/[^/]*[^\x00-\x7F][^/]*/", " ", text)
    text = re.sub(
        r"([a-zA-Z]+)- (ing|ed|ers|ment|ness|ly|tion|sion|thing|"
        r"come|tem|noon|bet|where|fully|puters|ever|never|here|"
        r"there)\b",
        lambda m: m.group(1) + m.group(2), text)
    return " ".join(text.split())


def shape_sentence(sentence, max_chars=MAX_CHARS):
    """
    One clean well-formed sentence: OCR marks cleaned, trimmed to
    the length cap on a word boundary (honest ellipsis when no
    boundary exists), capitalized, terminally punctuated.
    """
    text = _clean_text(str(sentence or ""))
    if len(text) > max_chars:
        cut = text[:max_chars].rfind(" ")
        if cut > 40:
            text = text[:cut].rstrip(" ,;:-")
            text += "."
        else:
            text = text[:max_chars - 3].rstrip() + "..."
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    if text and text[-1] not in ".!?":
        text += "."
    return text
    if len(text) > max_chars:
        cut = text[:max_chars].rfind(" ")
        text = (text[:cut] if cut > 40 else text[:max_chars]).rstrip(" ,;:-")
        text += "."
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    if text and text[-1] not in ".!?":
        text += "."
    return text


def best_quote(anchors, query, topic=(), max_chars=MAX_CHARS):
    """
    The single best vault sentence for the question across all
    ranked anchors [(title, data), ...].  Most query tokens wins;
    ties go to the higher-ranked anchor, then the earlier
    sentence — fully deterministic.  A carried topic (the
    working-memory thread behind "tell me more") replaces the
    bare follow-up words — the question IS the topic, exactly
    as the R4 rewrite already assumes.  None only when there is
    nothing to quote (the Broca template then speaks).
    """
    if not anchors:
        return None
    tokens = set(topic) if topic else query_tokens(query)
    best = None
    for title, data in anchors:
        # Provenance counts: a sentence from a memory ABOUT the
        # topic outranks a passing mention elsewhere ("dark matter
        # interacts through gravity" is a dark-matter sentence
        # that happens to name gravity).
        # Fix-pass: cleanliness breaks near-ties — a human sentence
        # outranks verse-number salad with equal hits (each hit is
        # worth 4 mess points; never a veto).
        thead = score_sentence(title or "", tokens)
        for sentence in split_sentences(data):
            total = (score_sentence(sentence, tokens) * 4 + thead * 2
                     - messiness(sentence))
            if best is None or total > best[0]:
                best = (total, sentence)
    if best is None:
        return None
    return shape_sentence(best[1], max_chars=max_chars)
