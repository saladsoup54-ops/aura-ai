# ukft_question.py — AURA Question Understanding (V5 R4)
# ==================================================
# The bridge between her speech and her knowledge.  A question is
# classified by intent, its entities are resolved against the
# knowledge graph (asserted + inferred edges), and it compiles to a
# concrete graph operation.  Answer COMPOSITION is R5's job; this
# module only decides what a question MEANS and what the graph has to
# say about it.
#
#   - Intents: WHAT/WHO (describe), WHERE, WHEN, WHY, HOW_MANY,
#     VERIFY ("is X a Y"), COMPARE — classified deterministically,
#     comparison forms first so "is hashing faster than binary
#     search" is never read as a yes/no question.
#   - Entity resolution: longest node-span matches against asserted
#     AND inferred nodes; leftovers stay visible as unresolved words
#     so R5/R6 can answer honestly instead of guessing.
#   - Verification walks is_a paths (including R3's transitive
#     conclusions) — a question about a derived fact succeeds.
#   - There is deliberately no temporal layer: WHEN compiles to a
#     flagged empty result, never a confabulation.
# ==================================================

import re
import time

from aura_constants import INFERENCES, KNOWLEDGE_GRAPH
from ukft_time import resolve_time

QUESTION_TAIL = {"did", "do", "does", "have", "has", "had", "is", "are",
                 "was", "were", "the", "a", "an", "of", "to", "in", "on",
                 "at", "for", "with", "and", "or", "many", "much",
                 "what", "who", "where", "when", "why", "how"}

DESCRIBE_RELS = {"is_a"}
KIN_RELS = {"kin:son_of", "kin:daughter_of", "kin:father_of",
            "kin:child_of", "kin:parent_of", "kin:wife_of",
            "kin:husband_of", "kin:mother_of", "kin:brother_of",
            "kin:sister_of"}
WHERE_RELS = {"located_in", "contains"}
WHY_RELS = {"causes", "caused_by"}
PROPERTY_RELS = {"has_property:has", "has_property:lacks"}

COMPARATOR_WORDS = {
    "greater": "greater_than", "less": "less_than",
    "larger": "larger_than", "smaller": "smaller_than",
    "heavier": "heavier_than", "lighter": "lighter_than",
    "faster": "faster_than", "slower": "slower_than",
}

NUMERAL_HEADS = {"one", "two", "three", "four", "five", "six", "seven",
                 "eight", "nine", "ten", "eleven", "twelve", "many",
                 "several", "few", "numerous", "various", "different"}


class QuestionUnderstanding:
    """Classify a question and compile it to a graph operation."""

    def __init__(self, graph=None, graph_path=KNOWLEDGE_GRAPH,
                 inferences_path=INFERENCES, attested=None,
                 now_fn=None):
        self.graph = graph
        self.graph_path = graph_path
        self.inferences_path = inferences_path
        self.attested = attested   # corpus word counts (spec: resolve
                                   # against graph AND vocabularies)
        self.now_fn = now_fn       # V6 C1: injectable clock for windows

    def _get_graph(self):
        if self.graph is None:
            from ukft_knowledge_graph import KnowledgeGraph
            self.graph = KnowledgeGraph(path=self.graph_path).load()
        return self.graph

    def _get_inferred(self):
        from ukft_inference import InferenceEngine
        engine = InferenceEngine(out_path=self.inferences_path,
                                 contradictions_path="none.txt")
        try:
            engine.load()
        except Exception:
            engine.derived = {}
        return engine.derived

    def _nodes(self):
        nodes = set(self._get_graph().nodes)
        nodes |= {y for (_r, _x, y) in self._get_inferred()}
        nodes |= {x for (_r, x, _y) in self._get_inferred()}
        return nodes

    # ── INTENT CLASSIFICATION ────────────────────────────────────
    def classify(self, question):
        q = re.sub(r"\s+", " ", question.strip().lower()).strip(" ?.")
        if not q:
            return {"intent": "UNKNOWN", "x": None, "y": None,
                    "comparator": None, "property": None, "relation": None}
        # A leading greeting is social wrapping, not content —
        # "good morning, is unix an operating system" must verify
        # like the bare question does.  A name after the greeting
        # ("hello aura what is dark matter") is the addressee, not
        # the topic — it goes too, but ONLY after a greeting (a
        # bare "matty who is he" leads with the entity itself).
        q2 = re.sub(r"^(good morning|good evening|good afternoon|"
                    r"greetings|hello|hey|hi)\b[,. ]*", "", q).strip()
        if q2 != q:
            q = re.sub(r"^(aura|architect|matty)\b[,. ]*", "",
                       q2).strip()
        else:
            q = q2
        if not q:
            return {"intent": "UNKNOWN", "x": None, "y": None,
                    "comparator": None, "property": None, "relation": None}

        def out(intent, x, y, comparator=None, relation=None):
            return {"intent": intent, "x": x, "y": y,
                    "comparator": comparator, "property": None,
                    "relation": relation}

        m = re.match(
            r"^(?:is|are|was)\s+(.+?)\s+"
            r"(greater|less|larger|smaller|heavier|lighter|faster|slower)"
            r"\s+than\s+(.+)$", q)
        if m:
            return out("COMPARE", m.group(1), m.group(3),
                       COMPARATOR_WORDS[m.group(2)])

        # "more massive than" and "equal to" never fit the than-word
        # list above, so mined edges of those kinds were unaskable
        # (they fell to bare-VERIFY).  Both shapes precede it.
        m = re.match(r"^(?:is|are|was)\s+(.+?)\s+more massive than\s+(.+)$",
                     q)
        if m:
            return out("COMPARE", m.group(1), m.group(2),
                       "more_massive_than")

        m = re.match(r"^(?:is|are|was)\s+(.+?)\s+equal to\s+(.+)$", q)
        if m:
            return out("COMPARE", m.group(1), m.group(2), "equal_to")

        m = re.match(r"^compare\s+(.+?)\s+(?:and|with|to)\s+(.+)$", q)
        if m:
            return out("COMPARE", m.group(1), m.group(2))

        # "is david the father of solomon" — a kin edge check.  The
        # derived inverses (child_of, parent_of) and the ancestry chain
        # (ancestor_of, descendant_of) are also checkable.
        kin_map = {"son": "kin:son_of", "daughter": "kin:daughter_of",
                   "father": "kin:father_of", "mother": "kin:mother_of",
                   "parent": "kin:parent_of", "child": "kin:child_of",
                   "ancestor": "kin:ancestor_of",
                   "descendant": "kin:descendant_of",
                   "wife": "kin:wife_of", "husband": "kin:husband_of",
                   "brother": "kin:brother_of",
                   "sister": "kin:sister_of"}
        m = re.match(
            r"^(?:is|are|was)\s+(.+?)\s+(?:the\s+)?"
            r"(son|daughter|father|mother|parent|child|ancestor|"
            r"descendant|wife|husband|brother|sister)"
            r"\s+of\s+(.+)$", q)
        if m:
            return out("VERIFY", m.group(1), m.group(3),
                       relation=kin_map[m.group(2)])

        # "is the proton located in the nucleus" is a location check,
        # never an is_a verification.
        m = re.match(
            r"^(?:is|are|was)\s+(.+?)\s+(?:located|situated|lying)"
            r"\s+in\s+(.+)$", q)
        if m:
            return out("VERIFY", m.group(1), m.group(2),
                       relation="located_in")

        # "is the nucleus part of the atom" — a part_of edge check.
        m = re.match(r"^(?:is|are|was)\s+(.+?)\s+(?:a\s+)?part of\s+(.+)$", q)
        if m:
            return out("VERIFY", m.group(1), m.group(2),
                       relation="part_of")

        m = re.match(r"^(?:is|are|was)\s+(.+?)\s+(?:a|an)\s+(.+)$", q)
        if m:
            return out("VERIFY", m.group(1), m.group(2))

        m = re.match(r"^(?:is|are|was)\s+(.+?)\s+([a-z][a-z -]*)$", q)
        if m:
            d = out("VERIFY", f"{m.group(1)} {m.group(2)}", None)
            d["bare"] = True
            return d

        m = re.match(r"^what\s+(?:is|are|was|were)\s+(.+)$", q)
        if m:
            return out("WHAT", m.group(1), None)

        m = re.match(r"^who\s+(?:is|are|was|were)\s+(.+)$", q)
        if m:
            return out("WHO", m.group(1), None)

        m = re.match(r"^where\s+(?:is|are|was|were)\s+(.+)$", q)
        if m:
            return out("WHERE", m.group(1), None)

        # Name-first phrasings: "david who is he?", "phyllobium what is
        # it?" — the entity leads the sentence.  Without these the
        # question never reaches the graph and drifts through the
        # trigram instead of being proved.
        m = re.match(r"^(.+?)\s+who\s+(?:is|are|was|were)\s+"
                     r"(?:he|she|it|they)$", q)
        if m:
            return out("WHO", m.group(1), None)
        m = re.match(r"^(.+?)\s+what\s+(?:is|are|was|were)\s+"
                     r"(?:it|this|that)$", q)
        if m:
            return out("WHAT", m.group(1), None)

        # "tell me about X" / "what do you know about X" are describe
        # requests — they compile to the graph when it has facts and
        # fall back to association when it does not.
        m = re.match(r"^(?:tell me (?:more )?about|what can you tell me "
                     r"about|what do you know about)\s+(.+)$", q)
        if m:
            return out("WHAT", m.group(1), None)

        m = re.match(r"^when\b", q)
        if m:
            return out("WHEN", None, None)

        m = re.match(r"^why\b", q)
        if m:
            # Strip the interrogative shell — resolving the whole
            # question stored "why does x happen" as the entity and
            # polluted leftover/gap words with question grammar.
            entity = re.sub(r"^why\s+(does|do|is|are|was|were|did|can|"
                            r"could|would|should|has|have|had)?\s*", "", q)
            return out("WHY", entity or q, None)

        m = re.match(r"^how\s+(?:many|much)\s+(.+)$", q)
        if m:
            return out("HOW_MANY", m.group(1), None)

        return out("UNKNOWN", q, None)

    # ── ENTITY RESOLUTION ────────────────────────────────────────
    def resolve(self, phrase):
        """
        Longest node-span matches left to right.  Returns
        (resolved_nodes, leftover_content_words).
        """
        words = re.findall(r"[a-z]+", phrase)
        nodes = self._nodes()
        matched = []
        consumed = set()
        i = 0
        while i < len(words):
            hit = None
            for k in range(min(4, len(words) - i), 0, -1):
                cand = " ".join(words[i:i + k])
                if cand in nodes:
                    hit = (cand, k)
                    break
            if hit:
                if hit[0] not in matched:
                    matched.append(hit[0])
                consumed.update(range(i, i + hit[1]))
                i += hit[1]
            else:
                i += 1
        # Leftover counts token POSITIONS, not word strings: a word
        # occurring both inside a matched span and at an unmatched
        # position stays leftover for its unmatched occurrence.
        leftover = [w for idx, w in enumerate(words) if idx not in consumed]
        return matched, leftover

    # ── COMPILATION ──────────────────────────────────────────────
    def plan(self, question):
        """
        Compile a question into an operation plan: intent, resolved
        entities, and the graph query that answers it.  No results are
        fetched here — run(plan) executes.
        """
        plan = self.classify(question)
        intent = plan["intent"]
        plan["unresolved"] = []
        plan["resolved"] = []
        plan["attested"] = []
        plan["op"] = None
        plan["property"] = None

        # V6 C1: every plan carries its time window (None when the
        # question names no time).  The graph holds no temporal
        # facts, so WHEN still compiles to its flagged honest gap —
        # the window is for the episodic diary (recall), not proof.
        try:
            now = self.now_fn() if self.now_fn else time.time()
            plan["time_window"] = resolve_time(question, now)
        except Exception:
            plan["time_window"] = None

        if intent == "WHEN":
            plan["op"] = "when"
            plan["flags"] = ["no temporal layer in the graph"]
            return plan

        if intent == "HOW_MANY":
            plan["resolved"], leftover = self.resolve(plan["x"])
            tail = [w for w in leftover if w not in QUESTION_TAIL]
            if plan["resolved"]:
                # A property filter only means something when the
                # entity was found; leftover words are filter terms.
                plan["property"] = " ".join(tail) if tail else None
                plan["unresolved"] = []
            else:
                # No entity: every leftover word is an unknown, and
                # the honest answer must name it, not swallow it.
                plan["property"] = None
                plan["unresolved"] = tail
            plan["op"] = "how_many"
            self._mark_attested(plan)
            return plan

        if intent in ("WHAT", "WHO", "WHERE"):
            plan["resolved"], leftover = self.resolve(plan["x"])
            plan["unresolved"] = [w for w in leftover if w not in QUESTION_TAIL]
            plan["op"] = {"WHAT": "describe", "WHO": "describe",
                          "WHERE": "where"}[intent]
            self._mark_attested(plan)
            return plan

        if intent == "WHY":
            plan["resolved"], leftover = self.resolve(plan["x"])
            plan["unresolved"] = [w for w in leftover if w not in QUESTION_TAIL]
            plan["op"] = "why"
            self._mark_attested(plan)
            return plan

        if intent == "VERIFY":
            if plan.pop("bare", False):
                # Bare "is X Y": the article-less split is ambiguous
                # ("is dark matter real" is not x="dark", y="matter
                # real") — resolve node spans from the whole phrase.
                nodes, leftover = self.resolve(plan["x"] or "")
                plan["resolved"] = nodes
                plan["x"] = nodes[0] if len(nodes) >= 1 else None
                plan["y"] = nodes[1] if len(nodes) >= 2 else None
                plan["unresolved"] = [w for w in leftover
                                      if w not in QUESTION_TAIL]
                self._mark_attested(plan)
                plan["op"] = "verify"
                return plan
            x_nodes, x_left = self.resolve(plan["x"] or "")
            y_nodes, y_left = self.resolve(plan["y"] or "")
            plan["resolved"] = x_nodes + y_nodes
            plan["x"] = x_nodes[0] if x_nodes else None
            plan["y"] = y_nodes[0] if y_nodes else None
            if plan.get("relation"):
                # "father of", "located in" are relation words, not
                # entities — they must not show up as unresolved.
                plan["unresolved"] = []
            else:
                plan["unresolved"] = [w for w in x_left + y_left
                                      if w not in QUESTION_TAIL]
            self._mark_attested(plan)
            plan["op"] = "verify"
            return plan

        if intent == "COMPARE":
            x_nodes, x_left = self.resolve(plan["x"] or "")
            y_nodes, y_left = self.resolve(plan["y"] or "")
            plan["resolved"] = x_nodes + y_nodes
            plan["x"] = x_nodes[0] if x_nodes else None
            plan["y"] = y_nodes[0] if y_nodes else None
            plan["unresolved"] = [w for w in x_left + y_left
                                  if w not in QUESTION_TAIL]
            self._mark_attested(plan)
            plan["op"] = "compare"
            return plan

        plan["op"] = "unknown"
        plan["resolved"], leftover = self.resolve(plan["x"] or "")
        plan["unresolved"] = [w for w in leftover if w not in QUESTION_TAIL]
        self._mark_attested(plan)
        return plan

    def _mark_attested(self, plan):
        """Flag unresolved words the corpus actually knows (spec: entity
        resolution against corpus vocabularies too)."""
        if not self.attested:
            return
        plan["attested"] = [w for w in plan["unresolved"]
                            if self.attested.get(w, 0) >= 2]

    # ── EXECUTION ────────────────────────────────────────────────
    def _combined_edges(self):
        """(rel, x, y) -> (conf, origin) over asserted + inferred."""
        edges = {}
        for (x, rel, y), (conf, _src) in self._get_graph().edges.items():
            edges[(rel, x, y)] = (conf, "asserted")
        for (rel, x, y), (conf, _proof, _rule) in self._get_inferred().items():
            if (rel, x, y) in edges:
                if conf > edges[(rel, x, y)][0]:
                    edges[(rel, x, y)] = (conf, "inferred")
            else:
                edges[(rel, x, y)] = (conf, "inferred")
        return edges

    def _collect(self, edges, x, rels):
        out = []
        for (rel, a, b), (conf, origin) in edges.items():
            if a == x and rel in rels:
                out.append((rel, a, b, conf, origin))
        out.sort()
        return out

    def _collect_incoming(self, edges, x, rels):
        out = []
        for (rel, a, b), (conf, origin) in edges.items():
            if b == x and rel in rels:
                out.append((rel, a, b, conf, origin))
        out.sort()
        return out

    def run(self, plan=None, question=None):
        """
        Execute a plan (or compile + execute a question) and return it
        with "results" attached: [(rel, x, y, conf, origin)].
        """
        if plan is None:
            plan = self.plan(question)
        edges = self._combined_edges()
        op = plan.get("op")
        results = []

        if op == "describe":
            for x in plan["resolved"]:
                results.extend(self._collect(edges, x, DESCRIBE_RELS))
                # Kin runs both ways — a derived child_of(david,
                # solomon) points INTO solomon, and "who is solomon"
                # must see it.
                results.extend(self._collect(edges, x, KIN_RELS))
                results.extend(self._collect_incoming(edges, x, KIN_RELS))
        elif op == "where":
            for x in plan["resolved"]:
                results.extend(self._collect(edges, x, WHERE_RELS))
                results.extend(self._collect_incoming(edges, x, WHERE_RELS))
        elif op == "why":
            for x in plan["resolved"]:
                results.extend(self._collect(edges, x, WHY_RELS))
                results.extend(self._collect_incoming(edges, x, WHY_RELS))
        elif op == "how_many":
            for x in plan["resolved"]:
                for (rel, a, b), (conf, origin) in edges.items():
                    if a != x or rel not in PROPERTY_RELS:
                        continue
                    head = re.findall(r"[a-z]+", b)
                    if head and head[0] in NUMERAL_HEADS:
                        if (plan.get("property")
                                and plan["property"] not in b):
                            continue
                        results.append((rel, a, b, conf, origin))
        elif op == "verify":
            x, y, rel = plan.get("x"), plan.get("y"), plan.get("relation")
            plan["verify_conf"] = 0.0
            plan["verify_origin"] = "asserted"
            if x and y:
                if rel:
                    # Direct edge check — asserted OR derived ("is
                    # solomon the child of david" uses R3's inverse).
                    hit = edges.get((rel, x, y))
                    plan["verified"] = hit is not None
                    if hit:
                        plan["verify_conf"] = hit[0]
                        plan["verify_origin"] = hit[1]
                else:
                    found, best = self._is_a_path(edges, x, y)
                    plan["verified"] = found
                    plan["verify_conf"] = best
            else:
                plan["verified"] = None
        elif op == "compare":
            x, y, comp = plan.get("x"), plan.get("y"), plan.get("comparator")
            for (rel, a, b), (conf, origin) in edges.items():
                if not rel.startswith("compare:"):
                    continue
                if comp and rel != f"compare:{comp}":
                    continue
                if a == x and b == y:
                    results.append((rel, a, b, conf, origin))
                elif a == y and b == x:
                    results.append((rel, a, b, conf, origin))

        plan["results"] = results
        return plan

    def _is_a_path(self, edges, x, y):
        """
        Does x reach y over is_a edges (asserted + derived)?  Returns
        (found, weakest-link confidence) so answers hedge honestly on
        thin chains instead of speaking every verification as certain.
        """
        if x == y:
            return True, 1.0
        adj = {}
        for (rel, a, b), (c, _o) in edges.items():
            if rel == "is_a":
                adj.setdefault(a, []).append((b, c))
        best = {}
        frontier = [(x, 1.0)]
        while frontier:
            current, conf = frontier.pop(0)
            for nxt, c in adj.get(current, []):
                nc = conf if conf < c else c
                if nxt == y:
                    return True, nc
                if nc > best.get(nxt, -1.0):
                    best[nxt] = nc
                    frontier.append((nxt, nc))
        return False, 0.0


def ask(question, graph_path=KNOWLEDGE_GRAPH,
        inferences_path=INFERENCES):
    """Convenience: compile + execute one question."""
    engine = QuestionUnderstanding(graph_path=graph_path,
                                   inferences_path=inferences_path)
    return engine.run(engine.plan(question))


if __name__ == "__main__":
    import sys
    for q in sys.argv[1:] or ["what is arduino", "is unix an operating system"]:
        plan = ask(q)
        print(f"Q: {q}")
        print(f"   intent={plan['intent']} resolved={plan['resolved']} "
              f"unresolved={plan['unresolved']} op={plan['op']}")
        for r in plan.get("results", []):
            print(f"     {r[0]}({r[1]}, {r[2]}) conf={r[3]:.2f} [{r[4]}]")
        if "verified" in plan:
            print(f"   verified={plan['verified']}")
        if not plan.get("results") and "verified" not in plan:
            print("     (no graph results)")
