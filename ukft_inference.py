# ukft_inference.py — AURA Inference Engine (V5 R3)
# ==================================================
# The first real thought.  R2's knowledge graph holds what she has
# asserted; this engine derives what FOLLOWS from it — and flags what
# cannot be true.  Every conclusion carries its proof trail, so an
# answer composed from an inference is traceable back to the asserted
# edges that produced it (R5 will render these trails; R3 only writes
# them).
#
#   Rules (forward chaining to a fixpoint, confidence = min(premises)):
#   - transitivity: part_of, located_in, is_a chain through a middle
#     term ("a is part of b, b is part of c, so a is part of c").
#   - ancestry: father_of chains yield kin:ancestor_of; son_of /
#     daughter_of chains yield kin:descendant_of (father_of is NOT
#     transitive — a father's father is a grandfather, not a father).
#   - inheritance with exceptions: a class's has_property flows down
#     to its is_a subclasses UNLESS the subclass carries an override
#     record (its own has_property on that property — "ostriches are
#     birds, birds have wings, but the ostrich record says it lacks
#     them", so the inheritance is blocked).
#   - inverses: son_of/daughter_of <-> parent_of, father_of/
#     mother_of -> child_of, parent_of <-> child_of, ancestor_of
#     <-> descendant_of, wife_of <-> husband_of; part_of ->
#     has_part, located_in -> contains, causes -> caused_by,
#     has_property -> property_of / property_lacked_by.
#   Contradictions (opposite comparisons, is_a cycles, has-vs-lacks
#   on one pair) are written to contradictions.txt and never inferred
#   over — surfacing them in answers is R5's job.
# ==================================================

import sys
import re
import time
from collections import defaultdict

from aura_bus import read as bus_read, write as bus_write
from aura_constants import CONTRADICTIONS, INFERENCES, KNOWLEDGE_GRAPH

MAX_ROUNDS = 10   # fixpoint safety cap (graphs this small converge fast)

INVERSE_MAP = {
    # Sibling inverses deliberately absent: brother_of(a, b) does not
    # entail brother_of(b, a) from text alone (half-siblings read the
    # same), so siblings derive nothing (audited).
    "kin:father_of": "kin:child_of",
    "kin:mother_of": "kin:child_of",
    "kin:son_of": "kin:parent_of",
    "kin:daughter_of": "kin:parent_of",
    "kin:parent_of": "kin:child_of",
    "kin:child_of": "kin:parent_of",
    "kin:ancestor_of": "kin:descendant_of",
    "kin:descendant_of": "kin:ancestor_of",
    "kin:wife_of": "kin:husband_of",
    "kin:husband_of": "kin:wife_of",
    "part_of": "has_part",
    "located_in": "contains",
    "causes": "caused_by",
    "has_property:has": "property_of",
    "has_property:lacks": "property_lacked_by",
}

TRANSITIVE_RELS = {"part_of", "located_in", "is_a"}

CHILD_RELS = {"kin:son_of", "kin:daughter_of"}

OPPOSITE_COMPARES = {
    "greater_than": "less_than",
    "less_than": "greater_than",
    "larger_than": "smaller_than",
    "smaller_than": "larger_than",
    "heavier_than": "lighter_than",
    "lighter_than": "heavier_than",
    "faster_than": "slower_than",
    "slower_than": "faster_than",
    "more_massive_than": "less_massive_than",
    "less_massive_than": "more_massive_than",
}

PROPERTY_RELS = {"has_property:has", "has_property:lacks"}


def _proof(*steps):
    return "; ".join(
        f"{rel}({x}, {y})" for rel, x, y in steps
    )


class InferenceEngine:
    """
    Derive typed conclusions over a knowledge graph.  Read-only on the
    graph; writes inferences.txt and contradictions.txt.
    """

    def __init__(self, graph=None, graph_path=KNOWLEDGE_GRAPH,
                 out_path=INFERENCES, contradictions_path=CONTRADICTIONS):
        self.graph_path = graph_path
        self.out_path = out_path
        self.contradictions_path = contradictions_path
        self.graph = graph
        self.derived = {}          # (rel, x, y) -> (conf, proof, rule)
        self.contradictions = []   # human-readable conflict lines

    def _get_graph(self):
        if self.graph is None:
            from ukft_knowledge_graph import KnowledgeGraph
            self.graph = KnowledgeGraph(path=self.graph_path).load()
        return self.graph

    def _all_edges(self):
        """Asserted + derived edges: (rel, x, y) -> conf."""
        graph = self._get_graph()
        edges = {}
        for (x, rel, y), (conf, _src) in graph.edges.items():
            edges[(rel, x, y)] = conf
        for (rel, x, y), (conf, _proof, _rule) in self.derived.items():
            edges[(rel, x, y)] = conf
        return edges

    def _add(self, rel, x, y, conf, proof, rule):
        """Record a derived conclusion; skip if asserted or not better."""
        graph = self._get_graph()
        if x == y:
            return False
        if (x, rel, y) in graph.edges:
            return False
        key = (rel, x, y)
        if key in self.derived and self.derived[key][0] >= conf:
            return False
        self.derived[key] = (round(conf, 2), proof, rule)
        return True

    # ── RULES ────────────────────────────────────────────────────
    def _rule_inverse(self, edges):
        for (rel, x, y), conf in list(edges.items()):
            inv = INVERSE_MAP.get(rel)
            if inv:
                self._add(inv, y, x, conf,
                          _proof((rel, x, y)), "inverse")

    def _rule_transitive(self, edges):
        for rel in TRANSITIVE_RELS:
            by_y = defaultdict(list)
            for (r, x, y), conf in edges.items():
                if r == rel:
                    by_y[y].append((x, conf))
            for (r, y, z), c2 in edges.items():
                if r != rel:
                    continue
                for x, c1 in by_y.get(y, []):
                    self._add(rel, x, z, min(c1, c2),
                              _proof((rel, x, y), (rel, y, z)),
                              "transitivity")

    def _rule_ancestry(self, edges):
        # Orientation matters: father_of(x, y) means x PARENT of y;
        # son_of/daughter_of(x, y) means x CHILD of y.  The old mixed
        # joins matched the child side (co-parents filed as
        # ancestor/descendant, siblings as descendant_of).  Correct:
        # ancestor_of(x, z) only when z is genuinely BELOW x through
        # mid (mid's child), descendant_of(x, z) only when z is ABOVE x
        # (mid's parent).  Siblings derive nothing — there is no
        # sibling relation to mint.
        parents = [(x, y, c) for (r, x, y), c in edges.items()
                   if r in ("kin:father_of", "kin:mother_of")]
        children = [(x, y, c) for (r, x, y), c in edges.items()
                    if r in CHILD_RELS]
        for x, mid, c1 in parents:
            for m2, z, c2 in parents:
                if m2 == mid:
                    self._add("kin:ancestor_of", x, z, min(c1, c2),
                              _proof((p_of(x, mid, edges), x, mid),
                                     (p_of(mid, z, edges), mid, z)),
                              "ancestry")
            for c, p, c2 in children:
                if p == mid:
                    self._add("kin:ancestor_of", x, c, min(c1, c2),
                              _proof((p_of(x, mid, edges), x, mid),
                                     (r_of(c, mid, edges), c, mid)),
                              "ancestry")
        for x, mid, c1 in children:
            for m2, z, c2 in children:
                if m2 == mid:
                    self._add("kin:descendant_of", x, z, min(c1, c2),
                              _proof((r_of(x, mid, edges), x, mid),
                                     (r_of(mid, z, edges), mid, z)),
                              "ancestry")
            # Mixed side, mirrored with the ancestor rule above: x is the
            # child of mid, so x descends from whoever fathered mid —
            # father_of(m2, mid) with z == mid.  (Matching m2 == mid here
            # minted SIBLINGS as descendants: x and z children of one
            # father share a parent side-by-side, nothing above.)
            for m2, z, c2 in parents:
                if z == mid:
                    self._add("kin:descendant_of", x, m2, min(c1, c2),
                              _proof((r_of(x, mid, edges), x, mid),
                                     (p_of(m2, mid, edges), m2, mid)),
                              "ancestry")

    def _rule_inherit(self, edges):
        for (r1, x, cls), c1 in edges.items():
            if r1 != "is_a":
                continue
            for (r2, owner, prop), c2 in edges.items():
                if owner != cls or r2 not in PROPERTY_RELS:
                    continue
                # Override record: the subclass's own assertion about
                # this property blocks inheritance (with exceptions).
                if self._has_own_property(x, prop, edges):
                    continue
                self._add(r2, x, prop, min(c1, c2),
                          _proof(("is_a", x, cls), (r2, cls, prop)),
                          "inheritance")

    def _has_own_property(self, x, prop, edges):
        return any((r, x, prop) in edges for r in PROPERTY_RELS)

    # ── CONTRADICTIONS ───────────────────────────────────────────
    def _detect_contradictions(self, edges):
        seen_compare = {}
        seen_reversed = set()
        for (r, x, y), conf in edges.items():
            if r.startswith("compare:"):
                op = r[len("compare:"):]
                key = (x, y)
                ops = seen_compare.setdefault(key, set())
                # Compare against EVERY comparator seen on this pair —
                # a third comparator in between must not hide an
                # earlier opposite ("greater, faster, less" still
                # contradicts on greater/less).
                opp = OPPOSITE_COMPARES.get(op)
                if opp in ops:
                    self.contradictions.append(
                        f"opposite comparison: compare:{opp} vs "
                        f"compare:{op} on ({x}, {y})")
                # Reversed pairs contradict too: greater(a,b) and
                # greater(b,a) cannot both hold — except symmetric
                # relations (equal_to stated both ways is one fact).
                # One report per unordered pair — both are visited.
                for (or_, ox, oy), oconf in edges.items():
                    if or_ == r and ox == y and oy == x and op != "equal_to":
                        ukey = (op,) + tuple(sorted((x, y)))
                        if ukey not in seen_reversed:
                            seen_reversed.add(ukey)
                            self.contradictions.append(
                                f"reversed comparison: compare:{op} on "
                                f"({x}, {y}) vs ({y}, {x})")
                        break
                ops.add(op)
        # is_a cycles of ANY length (a -> b -> c -> a), not just mirrored
        # pairs: inheritance around a loop proves everything about
        # everything.  Each cycle reports once, rotation-normalized.
        # Asserted edges only: transitivity closes every loop into a
        # complete digraph, and reporting the closure would file the
        # same fight once per sub-cycle.
        isa_adj = {}
        for (x, rel, y) in self._get_graph().edges:
            if rel == "is_a" and x != y:
                isa_adj.setdefault(x, []).append(y)
        seen_cycles = set()
        for start in sorted(isa_adj):
            stack = [(start, [start])]
            while stack:
                node, path = stack.pop()
                for nxt in sorted(set(isa_adj.get(node, []))):
                    if nxt == start and len(path) >= 2:
                        rot = min(path[i:] + path[:i]
                                  for i in range(len(path)))
                        key = tuple(rot)
                        if key not in seen_cycles:
                            seen_cycles.add(key)
                            if len(rot) == 2:
                                self.contradictions.append(
                                    f"is_a cycle: {rot[0]} <-> {rot[1]}")
                            else:
                                self.contradictions.append(
                                    "is_a cycle: "
                                    + " -> ".join(rot + [rot[0]]))
                    elif nxt not in path:
                        stack.append((nxt, path + [nxt]))
        for (r, x, prop), conf in edges.items():
            if r == "has_property:has" and (("has_property:lacks", x, prop) in edges):
                self.contradictions.append(
                    f"property conflict: {x} has and lacks {prop}")
        self.contradictions = sorted(set(self.contradictions))

    # ── DRIVER ───────────────────────────────────────────────────
    def infer(self):
        rounds = 0
        while rounds < MAX_ROUNDS:
            edges = self._all_edges()
            before = len(self.derived)
            self._rule_inverse(edges)
            self._rule_transitive(edges)
            self._rule_ancestry(edges)
            self._rule_inherit(edges)
            rounds += 1
            if len(self.derived) == before:
                break
        self._detect_contradictions(self._all_edges())
        return self

    # ── PERSISTENCE ──────────────────────────────────────────────
    def save(self):
        lines = sorted(
            self.derived.items(),
            key=lambda kv: (kv[0][0], kv[0][1], kv[0][2]),
        )
        out = [f"--- AURA INFERENCES (V5 R3) | KNOWN: {len(lines)} "
               f"| TS: {int(time.time())} ---"]
        for (rel, x, y), (conf, proof, rule) in lines:
            out.append(f"INFER: {rel} | X: {x} | Y: {y} | CONF: {conf:.2f} "
                       f"| PROOF: {proof} | RULE: {rule}")
        bus_write(self.out_path, "\n".join(out) + "\n")

        cont = [f"--- AURA CONTRADICTIONS (V5 R3) | KNOWN: "
                f"{len(self.contradictions)} | TS: {int(time.time())} ---"]
        cont.extend(f"CONTRADICTION: {c}" for c in self.contradictions)
        bus_write(self.contradictions_path, "\n".join(cont) + "\n")
        return len(lines)

    def load(self):
        """Read back inferences.txt + contradictions.txt (R4/R5)."""
        self.derived = {}
        self.contradictions = []
        for line in bus_read(self.out_path).splitlines():
            if not line.startswith("INFER: "):
                continue
            head = line[len("INFER: "):].split(" | ")
            if len(head) < 5:
                continue
            rel = head[0]
            parts = dict(p.split(": ", 1) for p in head[1:] if ": " in p)
            x, y = parts.get("X"), parts.get("Y")
            if not x or not y:
                continue
            try:
                conf = float(parts.get("CONF", "0.0"))
            except (ValueError, TypeError):
                continue
            if not 0.0 <= conf <= 1.0:
                # Clamp like R2: a corrupt file must never mint
                # certainty (audited).
                conf = min(1.0, max(0.0, conf))
            self.derived[(rel, x, y)] = (conf, parts.get("PROOF", ""),
                                        parts.get("RULE", ""))
        for line in bus_read(self.contradictions_path).splitlines():
            if line.startswith("CONTRADICTION: "):
                self.contradictions.append(line[len("CONTRADICTION: "):])
        return self


# ── CONTRADICTION CONSUMPTION (ONE semantic rule, M13/11A) ─────
# R3's writer format above is the contract; these pure helpers decide
# whether a held contradiction concerns the proposition an R4 plan is
# about to answer.  BOTH the R5 composer (VERIFY branch) and the M13
# bridge guard consume this rule — there is exactly one definition of
# contradiction relevance: ENTITY/PARTICIPANTS + RELATION/PREDICATE +
# ANSWERED PROPOSITION.  Same entity tokens with a different predicate
# never guard (a has-vs-lacks record does not block an is_a answer).
_OPPOSITE_RE = re.compile(
    r"^opposite comparison:\s*compare:(\S+)\s+vs\s+"
    r"compare:(\S+)\s+on\s+\((.+),\s*(.+)\)\s*$")
_REVERSED_RE = re.compile(
    r"^reversed comparison:\s*compare:(\S+)\s+on\s+"
    r"\((.+),\s*(.+)\)\s+vs\s+\((.+),\s*(.+)\)\s*$")
_PROPERTY_RE = re.compile(
    r"^property conflict:\s*(.+?)\s+has and lacks\s+(.+?)\s*$")
_CYCLE_RE = re.compile(r"^is_a cycle:\s*(.+?)\s*$")

_CONTRADICTION_PROPERTY_RELS = frozenset({
    "has_property:has", "has_property:lacks",
    "property_of", "property_lacked_by",
})


def parse_contradiction_records(text):
    """Parse R3 contradiction lines into structured records.

    Consumes ONLY the current R3 writer format. Anything else
    (stale/derived/hand-made lines) is counted as skipped and can never
    guard — fail closed. Returns (records, skipped).
    """
    records, skipped = [], 0
    for line in (text or "").splitlines():
        if not line.startswith("CONTRADICTION: "):
            continue
        body = line[len("CONTRADICTION: "):].strip()
        rec = None
        m = _OPPOSITE_RE.match(body)
        if m:
            rec = {"kind": "compare", "ops": sorted((m.group(1),
                                                     m.group(2))),
                   "pair": (m.group(3).strip(), m.group(4).strip()),
                   "line": body}
        else:
            m = _REVERSED_RE.match(body)
            if m:
                rec = {"kind": "compare", "ops": [m.group(1)],
                       "pair": (m.group(2).strip(),
                                m.group(3).strip()),
                       "line": body}
            else:
                m = _PROPERTY_RE.match(body)
                if m:
                    rec = {"kind": "property",
                           "subject": m.group(1).strip(),
                           "prop": m.group(2).strip(), "line": body}
                else:
                    m = _CYCLE_RE.match(body)
                    if m:
                        raw = m.group(1).strip()
                        if "<->" in raw:
                            nodes = [p.strip() for p in
                                     raw.split("<->")]
                        else:
                            nodes = [p.strip() for p in
                                     raw.split(" -> ")]
                            if len(nodes) >= 2 and \
                                    nodes[-1] == nodes[0]:
                                nodes = nodes[:-1]
                        nodes = [n for n in nodes if n]
                        if len(nodes) >= 2:
                            rec = {"kind": "isa-cycle",
                                   "nodes": nodes, "line": body}
        if rec is None:
            skipped += 1
        else:
            records.append(rec)
    return records, skipped


def contradiction_guards_plan(plan, records):
    """Proposition-level guard for an R-track answer plan.

    Returns (proposition_id, record) when the plan's ANSWERED
    proposition intersects a held contradiction, else None. The guard
    attaches to the conflicting relation/predicate, never to bare
    subject tokens.
    """
    if not plan or not records:
        return None
    op = plan.get("op")
    if op == "verify":
        if plan.get("verified") is not True:
            return None
        rel, x, y = (plan.get("relation") or "is_a"), plan.get("x"), \
            plan.get("y")
        if not x or not y:
            return None
        if rel == "is_a":
            for rec in records:
                if rec["kind"] == "isa-cycle" \
                        and {x, y} <= set(rec["nodes"]):
                    return (f"verify:is_a({x}, {y})", rec)
        elif rel in _CONTRADICTION_PROPERTY_RELS:
            for rec in records:
                if rec["kind"] == "property" \
                        and rec["subject"] == x \
                        and rec["prop"] == y:
                    return (f"verify:{rel}({x}, {y})", rec)
        return None
    if op == "compare":
        comp, x, y = plan.get("comparator"), plan.get("x"), \
            plan.get("y")
        results = plan.get("results") or []
        if not comp or not x or not y or not results:
            return None
        answered = any(r[0] == f"compare:{comp}"
                       and {r[1], r[2]} == {x, y} for r in results)
        if not answered:
            return None
        for rec in records:
            if rec["kind"] == "compare" \
                    and set(rec["pair"]) == {x, y} \
                    and comp in rec["ops"]:
                return (f"compare:{comp}({x}, {y})", rec)
        return None
    if op in ("describe", "where", "why", "how_many"):
        results = plan.get("results") or []
        if not results:
            return None
        for rel, a, b, _conf, _origin in results:
            for rec in records:
                if rec["kind"] == "property" \
                        and rel in _CONTRADICTION_PROPERTY_RELS \
                        and a == rec["subject"] and b == rec["prop"]:
                    return (f"edge:{rel}({a}, {b})", rec)
                if rec["kind"] == "isa-cycle" and rel == "is_a" \
                        and {a, b} <= set(rec["nodes"]):
                    return (f"edge:is_a({a}, {b})", rec)
                if rec["kind"] == "compare" \
                        and rel.startswith("compare:") \
                        and rel[len("compare:"):] in rec["ops"] \
                        and {a, b} == set(rec["pair"]):
                    return (f"edge:{rel}({a}, {b})", rec)
        return None
    return None


def r_of(x, y, edges):
    """Which child relation connects x to y (for proof text)."""
    for rel in CHILD_RELS:
        if (rel, x, y) in edges:
            return rel
    return "kin:child_of"


def p_of(x, y, edges):
    """Which parent relation connects x to y (for proof text)."""
    for rel in ("kin:father_of", "kin:mother_of", "kin:parent_of"):
        if (rel, x, y) in edges:
            return rel
    return "kin:parent_of"


def run_inference(graph_path=KNOWLEDGE_GRAPH, out_path=INFERENCES,
                  contradictions_path=CONTRADICTIONS):
    engine = InferenceEngine(graph_path=graph_path, out_path=out_path,
                             contradictions_path=contradictions_path)
    engine.infer()
    written = engine.save()
    print(f"[R3] graph read (read-only): {graph_path}")
    print(f"[R3] inferences written: {written} -> {out_path}")
    print(f"[R3] contradictions written: {len(engine.contradictions)} "
          f"-> {contradictions_path}")
    for c in engine.contradictions:
        print(f"      {c}")
    return engine


if __name__ == "__main__":
    g = sys.argv[1] if len(sys.argv) > 1 else KNOWLEDGE_GRAPH
    o = sys.argv[2] if len(sys.argv) > 2 else INFERENCES
    c = sys.argv[3] if len(sys.argv) > 3 else CONTRADICTIONS
    run_inference(g, o, c)
