# ukft_answer.py — AURA Answer Composition (V5 R5)
# ==================================================
# Proofs become speech.  R4 turns a question into graph results; R5
# renders them into sentences whose CONTENT is the proof trail, never
# a trigram sample — a sampled sentence can drift, a template cannot.
# Relation semantics give the sentence forms ("X is a Y", "X causes
# Y"); the grammar skeleton shapes them into well-formed speech.
#
#   - Asserted edges render directly; inferred edges add a one-step
#     "because" clause (the full trail stays in inferences.txt — the
#     file is the proof of record, speech gives the justification).
#   - When asserted and inferred edges cover the same pair, the
#     asserted one speaks — the inverse is redundant, not information.
#   - Low confidence hedges ("I believe that ..."); unresolved
#     entities, temporal gaps and unverified claims answer honestly
#     ("I do not know"), never by confabulation.
#   - compose() returns None only when there is nothing to prove —
#     that is the sole case where the associative trigram pipeline
#     may answer instead.
# ==================================================

import re

from aura_constants import INFERENCES

from ukft_grammar import GrammarSkeleton

MIN_GRAMMAR_SCORE = 0.5
HEDGE_CONF = 0.70
MAX_SENTENCES = 3

REL_WORD = {
    "kin:father_of": "father", "kin:son_of": "son",
    "kin:daughter_of": "daughter", "kin:child_of": "child",
    "kin:parent_of": "parent", "kin:ancestor_of": "ancestor",
    "kin:descendant_of": "descendant", "kin:wife_of": "wife",
    "kin:husband_of": "husband", "kin:mother_of": "mother",
    "kin:brother_of": "brother", "kin:sister_of": "sister",
}

LIST_THRESHOLD = 4   # describe answers with this many same-anchor
LIST_SHOWN = 5       # kin edges render as one compact list instead
                     # of three truncated sentences ("who are the sons
                     # of Japheth" has seven answers, not three).

COMPARE_WORDS = {
    "greater_than": "greater than", "less_than": "less than",
    "larger_than": "larger than", "smaller_than": "smaller than",
    "heavier_than": "heavier than", "lighter_than": "lighter than",
    "faster_than": "faster than", "slower_than": "slower than",
    "more_massive_than": "more massive than", "equal_to": "equal to",
}

LIST_PLURAL = {
    "kin:son_of": "sons", "kin:daughter_of": "daughters",
    "kin:father_of": "fathers", "kin:mother_of": "mothers",
    "kin:brother_of": "brothers", "kin:sister_of": "sisters",
    "kin:wife_of": "wives", "kin:husband_of": "husbands",
    "kin:child_of": "children", "kin:parent_of": "parents",
    "kin:ancestor_of": "ancestors",
    "kin:descendant_of": "descendants",
}


def art(word):
    """Indefinite article for a noun phrase (u-words are consonant-sound)."""
    if not word:
        return "a"
    if word[0] == "u" and (len(word) < 2 or word[1] not in "aeiou"):
        return "a"
    return "an" if word[0] in "aeiou" else "a"


def name(word):
    """Capitalize single-word names; never touch articles/short words."""
    if word and len(word) > 2 and " " not in word and word.isalpha():
        return word.capitalize()
    return word


# Asserted/inferred edges that describe the same pair must not BOTH
# speak — the inferred inverse is redundant, not information.
REL_FAMILIES = [
    lambda r: r.startswith("kin:"),
    lambda r: r in ("located_in", "contains"),
    lambda r: r in ("causes", "caused_by"),
    lambda r: r in ("part_of", "has_part"),
    lambda r: r.startswith("has_property:") or r.startswith("property"),
    lambda r: r.startswith("compare:"),
    lambda r: r == "is_a",
]

HONEST_IDIOMS = ("I do not know", "I have no record")


def _claim(rel, x, y):
    """Lowercase sentence body for one relation, no punctuation."""
    if rel == "is_a":
        return f"{art(x)} {x} is {art(y)} {y}"
    if rel in REL_WORD:
        return f"{name(x)} is the {REL_WORD[rel]} of {name(y)}"
    if rel == "part_of":
        return f"the {x} is part of the {y}"
    if rel == "has_part":
        return f"the {y} is part of the {x}"
    if rel == "located_in":
        return f"the {x} is located in the {y}"
    if rel == "contains":
        return f"the {x} contains the {y}"
    if rel == "causes":
        return f"{name(x)} causes {y}"
    if rel == "caused_by":
        return f"the {x} is caused by the {y}"
    if rel == "has_property:has":
        return f"{name(x)} has {y}"
    if rel == "has_property:lacks":
        return f"{name(x)} has no {y}"
    if rel == "property_of":
        # Edge order is (property_of, prop, owner): the property
        # belongs to the owner, never the reverse (audited).
        return f"{art(x)} {x} is a property of the {y}"
    if rel == "property_lacked_by":
        return f"{name(y)} has no {x}"
    if rel.startswith("compare:"):
        op = COMPARE_WORDS.get(rel[len("compare:"):], "compared to")
        return f"{name(x)} is {op} {y}"
    return f"{x} relates to {y}"


class AnswerComposer:
    """Render executed question plans into proof-seeded sentences."""

    def __init__(self, grammar=None, inferences_path=INFERENCES):
        self.grammar = grammar or GrammarSkeleton()
        self.inferences_path = inferences_path
        self._inferred = None

    def _proofs(self):
        if self._inferred is None:
            from ukft_inference import InferenceEngine
            engine = InferenceEngine(out_path=self.inferences_path,
                                     contradictions_path="none.txt")
            try:
                engine.load()
            except Exception:
                engine.derived = {}
            self._inferred = engine.derived
        return self._inferred

    # ── SENTENCE BUILDING ────────────────────────────────────────
    def _proof_clause(self, rel, x, y):
        """
        One-step justification for an inferred conclusion.  The full
        trail lives in inferences.txt; speech renders the immediate
        premise, anaphorically when it is an is_a step.
        """
        proof = self._proofs().get((rel, x, y), ("", "", ""))[1]
        steps = re.findall(r"([a-z_:]+)\(([^)]+), ([^)]+)\)", proof)
        if not steps:
            return None
        r1, x1, y1 = steps[0]
        if r1 == "is_a" and x1 == x:
            return f", because it is {art(y1)} {y1}"
        return f", because {_claim(r1, x1, y1)}"

    def _sentence(self, rel, x, y, conf, origin, negate=False):
        if negate:
            # Absence of a path is NOT evidence of absence — a missing
            # edge renders honest ignorance, never a confident denial
            # (an open-world graph cannot assert falsehood).
            return self.grammar.shape(f"I do not know that {_claim(rel, x, y)}")
        body = _claim(rel, x, y)
        hedged = conf < HEDGE_CONF
        if origin == "inferred" and not hedged:
            clause = self._proof_clause(rel, x, y)
            if clause:
                candidate = body + clause
                shaped = self.grammar.shape(candidate)
                if shaped and self.grammar.score(shaped) >= MIN_GRAMMAR_SCORE:
                    return shaped
        shaped = self.grammar.shape(body)
        if hedged and shaped:
            body_lower = shaped[0].lower() + shaped[1:]
            m = re.match(r"^([a-z]+)( .*)$", body_lower)
            if m:
                body_lower = name(m.group(1)) + m.group(2)
            shaped = self.grammar.shape(f"I believe that {body_lower}")
        return shaped

    def _list_answer(self, plan, results):
        """
        One compact list for describe questions whose answers share
        a relation and an anchor ("who are the sons of Japheth" has
        seven answers — three truncated sentences would shortchange
        it).  None when no group qualifies; the per-edge path then
        speaks as before.
        """
        if plan.get("intent") not in ("WHAT", "WHO"):
            return None
        if plan.get("op") != "describe":
            return None
        groups = {}
        for rel, x, y, conf, _origin in results:
            if rel not in LIST_PLURAL:
                continue
            groups.setdefault((rel, y), []).append((x, conf))
        for (rel, anchor) in sorted(groups):
            members = groups[(rel, anchor)]
            if len(members) < LIST_THRESHOLD:
                continue
            shown = [name(x) for x, _c in members[:LIST_SHOWN]]
            rest = len(members) - len(shown)
            if rest > 0:
                shown.append(f"and {rest} other"
                             f"{'' if rest == 1 else 's'}")
            body = (", ".join(shown) + f" are the {LIST_PLURAL[rel]} "
                    f"of {name(anchor)}.")
            if min(c for _x, c in members) < HEDGE_CONF:
                body = "I believe that " + body[0].lower() + body[1:]
            shaped = self.grammar.shape(body)
            if shaped and self.grammar.score(shaped) \
                    >= MIN_GRAMMAR_SCORE:
                return shaped
            return body if body else None
        return None

    def _dedupe(self, results):
        """
        Asserted edges out-speak inferred ones about the same pair:
        an asserted located_in silences the inferred contains, an
        asserted father_of silences the inferred child_of.
        """
        kept = []
        for r in results:
            if r[4] == "asserted":
                kept.append(r)
                continue
            rel, x, y = r[0], r[1], r[2]
            pair = frozenset((x, y))
            family = next((f for f in REL_FAMILIES if f(rel)), None)
            if family is None:
                # Unknown relation kind: speak it rather than crash the
                # whole composition on one novel edge.
                kept.append(r)
                continue
            shadowed = any(
                a[4] == "asserted" and family(a[0])
                and frozenset((a[1], a[2])) == pair
                for a in results
            )
            if not shadowed:
                kept.append(r)
        return kept

    def _contradicted(self, plan):
        """
        Proposition-aware contradiction check: ONE semantic rule shared
        with M13 (see ukft_inference.contradiction_guards_plan). The
        held contradiction must concern the proposition/relation being
        answered — ENTITY + PREDICATE + ANSWERED PROPOSITION — never
        mere entity-token overlap. A has-vs-lacks record about (X, P)
        does not block an is_a(X, P) answer; a genuine is_a cycle over
        the asked pair still surfaces.
        """
        try:
            from aura_bus import read as bus_read
            from aura_constants import CONTRADICTIONS
            text = bus_read(CONTRADICTIONS)
        except Exception:
            return False
        try:
            from ukft_inference import contradiction_guards_plan, \
                parse_contradiction_records
            records, _skipped = parse_contradiction_records(text or "")
        except Exception:
            return False
        if not records:
            return False
        try:
            return contradiction_guards_plan(plan, records) is not None
        except Exception:
            return False

    # ── COMPOSITION ──────────────────────────────────────────────
    def compose(self, plan):
        """
        Turn an executed plan into an answer body, or None when no
        proof exists (the associative pipeline may then answer).
        """
        op = plan.get("op")
        results = plan.get("results", [])

        if op == "verify":
            if plan.get("verified") is True:
                rel = plan.get("relation") or "is_a"
                if self._contradicted(plan):
                    return "I have read conflicting things about that."
                # Spoken with the backing edge's real confidence and
                # origin — weak chains hedge ("I believe") instead of
                # sounding certain.  A grammar failure still answers
                # honestly, never drifts (audited).
                return self._sentence(rel, plan["x"], plan["y"],
                                      plan.get("verify_conf", 1.0),
                                      plan.get("verify_origin", "asserted")) \
                    or "I do not know."
            if plan.get("verified") is False:
                rel = plan.get("relation") or "is_a"
                return self._sentence(rel, plan["x"], plan["y"], 1.0,
                                      "asserted", negate=True) \
                    or "I do not know."
            return "I do not know."

        if op == "when":
            return "I have no record of when that happened."

        if op == "unknown":
            return None

        if op == "compare" and not results:
            # Both sides known, no edge: an honest shrug, never the
            # trigram (audited — the contract covers COMPARE too).
            leftovers = plan.get("unresolved") or []
            if leftovers:
                return f"I do not know about {' '.join(leftovers[:2])}."
            return "I do not know."

        results = self._dedupe(results)
        listed = self._list_answer(plan, results)
        if listed:
            return listed
        sentences = []
        for rel, x, y, conf, origin in results[:MAX_SENTENCES]:
            sentence = self._sentence(rel, x, y, conf, origin)
            if sentence and sentence not in sentences:
                sentences.append(sentence)
        if sentences:
            return " ".join(sentences)

        unresolved = plan.get("unresolved") or []
        if unresolved:
            name = " ".join(unresolved[:2])
            return f"I do not know about {name}."
        return None


def answer(question, graph_path=None, inferences_path=INFERENCES):
    """One-call question -> answer body (None = associative fallback)."""
    from aura_constants import KNOWLEDGE_GRAPH
    from ukft_question import QuestionUnderstanding

    qa = QuestionUnderstanding(
        graph_path=graph_path or KNOWLEDGE_GRAPH,
        inferences_path=inferences_path,
    )
    plan = qa.run(qa.plan(question))
    return AnswerComposer(inferences_path=inferences_path).compose(plan)


if __name__ == "__main__":
    import sys
    for q in sys.argv[1:] or ["what is arduino"]:
        print(f"Q: {q}")
        print(f"[AURA]: {answer(q) or '(associative fallback — no proof)'}")
