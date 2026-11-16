# ukft_knowledge_graph.py — AURA Knowledge Graph Store (V5 R2)
# ==================================================
# The assertional layer.  R1 mines typed relations out of vault
# prose; R2 persists them as a node/edge graph with integrity checks
# and canonical ordering.  The temporal lobe stays the ASSOCIATIVE
# layer (co-occurrence strengths); this store is what R3's inference
# engine will chain over — every edge carries its source and the
# confidence R1 assigned it.
#
#   - Builds from extracted_relations.txt (R1's audited artifact),
#     never from the vault directly.
#   - Edges deduplicated on (x, rel, y), best confidence kept;
#     self-loops are refused — "X relates to X" is not knowledge.
#   - verify() reports every integrity problem (dangling nodes,
#     malformed lines, out-of-range confidence) without modifying
#     the file.
#   - Queries: neighbors(word, rel=None) and path(a, b) (BFS,
#     directed — relation inverses are R3's job).
# ==================================================

import re
import sys
import time

from aura_bus import read as bus_read, write as bus_write
from aura_constants import EXTRACTED_RELATIONS, KNOWLEDGE_GRAPH


class KnowledgeGraph:
    """Typed node/edge assertions, persisted with integrity checks."""

    def __init__(self, relations_path=EXTRACTED_RELATIONS,
                 path=KNOWLEDGE_GRAPH):
        self.relations_path = relations_path
        self.out_path = path   # file path; `path()` is a query method
        self.nodes = set()     # node -> set()
        self.edges = {}        # (x, rel, y) -> (conf, src)
        self.clamped = []      # quarantined out-of-range confidences
        self.refused = 0       # self-loops refused (set by build/load)

    # ── BUILDING ────────────────────────────────────────────────
    def build(self):
        """
        Read R1's extracted relations (the audited artifact) and turn
        them into graph edges.  Self-loops are refused and counted.
        """
        from ukft_relations import RelationExtractor

        refused = 0
        source = RelationExtractor(out_path=self.relations_path).load()
        for (typ, sub, x, y), (conf, evid, src) in source.relations.items():
            # Canonical hyphen form: "clive hicks-jenkins" and
            # "clive hicks jenkins" are one node (fix-pass — R4
            # tokenizes hyphens away, so hyphenated keys were
            # unresolvable).  R1 evidence keeps its raw text.
            x = " ".join(str(x).replace("-", " ").split())
            y = " ".join(str(y).replace("-", " ").split())
            if x == y:
                refused += 1
                continue
            rel = f"{typ}:{sub}" if sub else typ
            key = (x, rel, y)
            if key not in self.edges or conf > self.edges[key][0]:
                self.edges[key] = (conf, src)
            self.nodes.add(x)
            self.nodes.add(y)
        self.refused = refused
        return self

    # ── PERSISTENCE ─────────────────────────────────────────────
    def save(self):
        from aura_state import deny_live_write
        deny_live_write(self.out_path)
        nodes = sorted(self.nodes)
        edges = sorted(self.edges.items(),
                       key=lambda kv: (kv[0][0], kv[0][1], kv[0][2]))
        out = [f"--- AURA KNOWLEDGE GRAPH (V5 R2) | NODES: {len(nodes)} "
               f"| EDGES: {len(edges)} | TS: {int(time.time())} ---"]
        for node in nodes:
            out.append(f"NODE: {node}")
        for (x, rel, y), (conf, src) in edges:
            out.append(f"EDGE: {x} | {rel} | {y} | CONF: {conf:.2f} "
                       f"| SRC: {src}")
        bus_write(self.out_path, "\n".join(out) + "\n")
        return len(edges)

    def load(self):
        """Read back a saved graph; malformed lines are skipped."""
        self.nodes = set()
        self.edges = {}
        self.refused = 0
        self.clamped = []
        for line in bus_read(self.out_path).splitlines():
            line = line.strip()
            if line.startswith("NODE: "):
                self.nodes.add(line[len("NODE: "):])
            elif line.startswith("EDGE: "):
                parts = dict(
                    p.split(": ", 1)
                    for p in line[len("EDGE: "):].split(" | ")
                    if ": " in p
                )
                head = line[len("EDGE: "):].split(" | ")
                if len(head) < 3:
                    continue
                x, rel, y = head[0], head[1], head[2]
                try:
                    conf = float(parts.get("CONF", "0.0"))
                except (ValueError, TypeError):
                    continue
                if not 0.0 <= conf <= 1.0:
                    # Out-of-range confidences are quarantined, never
                    # trusted: stored clamped so inference cannot mint
                    # certainty from corruption, flagged by verify().
                    self.clamped.append((x, rel, y, conf))
                    conf = min(1.0, max(0.0, conf))
                src = parts.get("SRC", "")
                # First occurrence wins: the writer emits each edge once
                # in canonical order, so a later duplicate is tampering —
                # never let it upgrade (or downgrade) the stored edge.
                if (x, rel, y) not in self.edges:
                    self.edges[(x, rel, y)] = (conf, src)
                self.nodes.add(x)
                self.nodes.add(y)
        return self

    # ── INTEGRITY ───────────────────────────────────────────────
    def verify(self):
        """Return every integrity problem as a list of strings."""
        problems = []
        referenced = set()
        for (x, rel, y), (conf, src) in self.edges.items():
            referenced.add(x)
            referenced.add(y)
            if x == y:
                problems.append(f"self-loop edge: {x} | {rel} | {y}")
            if not 0.0 <= conf <= 1.0:
                problems.append(f"confidence out of range: {conf} "
                                f"on {x} | {rel} | {y}")
            if not x or not y or not rel:
                problems.append("empty field in edge")
            if "|" in x + rel + y:
                problems.append(f"pipe character in edge: {x} | {rel} | {y}")
        for x, rel, y, raw in getattr(self, "clamped", []):
            problems.append(f"confidence out of range: {raw} "
                            f"on {x} | {rel} | {y} (quarantined)")
        dangling = self.nodes - referenced
        for node in sorted(dangling):
            problems.append(f"node not referenced by any edge: {node}")
        return problems

    # ── QUERIES ─────────────────────────────────────────────────
    def neighbors(self, word, rel=None):
        """
        Outgoing edges of a word: list of (rel, y, conf).  A rel
        argument restricts to that relation type (exact match).
        """
        out = []
        for (x, e_rel, y), (conf, _src) in self.edges.items():
            if x == word and (rel is None or e_rel == rel):
                out.append((e_rel, y, conf))
        out.sort()
        return out

    def path(self, a, b):
        """
        Shortest directed edge-path from a to b (BFS).  Returns a list
        of (x, rel, y) hops, [] when a == b, or None when unreachable.
        Relation inverses are R3's business — this is forward-only.
        """
        if a == b:
            return []
        adjacency = {}
        for (x, rel, y), _conf in self.edges.items():
            adjacency.setdefault(x, []).append((rel, y))
        frontier = [a]
        came_from = {}
        seen = {a}
        while frontier:
            current = frontier.pop(0)
            for rel, nxt in adjacency.get(current, []):
                if nxt in seen:
                    continue
                seen.add(nxt)
                came_from[nxt] = (current, rel)
                if nxt == b:
                    hops = []
                    node = b
                    while node != a:
                        prev, rel = came_from[node]
                        hops.append((prev, rel, node))
                        node = prev
                    hops.reverse()
                    return hops
                frontier.append(nxt)
        return None


def build_knowledge_graph(relations_path=EXTRACTED_RELATIONS,
                          out_path=KNOWLEDGE_GRAPH):
    graph = KnowledgeGraph(relations_path, out_path).build()
    written = graph.save()
    problems = graph.verify()
    print(f"[R2] relations ingested (read-only): {relations_path}")
    print(f"[R2] edges written: {written} | nodes: {len(graph.nodes)} "
          f"| self-loops refused: {graph.refused} -> {out_path}")
    if problems:
        print(f"[R2] integrity problems: {len(problems)}")
        for p in problems:
            print(f"      {p}")
    return graph


if __name__ == "__main__":
    rels = sys.argv[1] if len(sys.argv) > 1 else EXTRACTED_RELATIONS
    out = sys.argv[2] if len(sys.argv) > 2 else KNOWLEDGE_GRAPH
    build_knowledge_graph(rels, out)
