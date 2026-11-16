# ukft_eval.py — AURA Evaluation Harness (V5 R7)
# ==================================================
# What gets measured gets built — and stays built.  This harness turns
# the V5 compliance gates into repeatable measurements:
#
#   Gate R-A — relation precision: a deterministic sample (census when
#              the file is small) of extracted_relations.txt written
#              out for Architect judgement; the rate is computed from
#              the recorded judgements.
#   Gate R-B — curated question answering: QA pairs generated from the
#              knowledge graph (definitions, genealogy, mechanisms),
#              every correct answer required to be proof-backed by an
#              asserted or inferred edge.
#   Gate R-C — contradiction detection: contradictions planted in a
#              test corpus must be flagged (>= 90%).
#   Gate R-D — honest ignorance: unanswerable questions must answer
#              "I do not know", never confabulate (>= 90%).
#
#   The measurement runs against any graph; the regression suite pins
#   it to a fixture corpus, and `python ukft_eval.py` measures the
#   LIVE files.  Nothing here writes to the vault.
# ==================================================

import random
import sys
import time

from aura_bus import read as bus_read, write as bus_write
from aura_constants import (EVALUATION_REPORT, EXTRACTED_RELATIONS,
                            INFERENCES, KNOWLEDGE_GRAPH, RELATION_AUDIT)

GATE_RB = 0.70   # QA accuracy floor
GATE_RC = 0.90   # contradiction detection floor
GATE_RD = 0.90   # honest-ignorance floor

COMPARE_PHRASES = {
    "greater_than": "greater than", "less_than": "less than",
    "larger_than": "larger than", "smaller_than": "smaller than",
    "heavier_than": "heavier than", "lighter_than": "lighter than",
    "faster_than": "faster than", "slower_than": "slower than",
    "more_massive_than": "more massive than",
    "equal_to": "equal to",
}

NUMERAL_HEADS = {"one", "two", "three", "four", "five", "six", "seven",
                 "eight", "nine", "ten", "eleven", "twelve", "many",
                 "several", "few", "numerous", "various", "different"}


def _name(word):
    if word and len(word) > 2 and " " not in word and word.isalpha():
        return word.capitalize()
    return word


# ── QA PAIR GENERATION ───────────────────────────────────────────
def generate_qa(graph_path=KNOWLEDGE_GRAPH, inferences_path=INFERENCES,
                n=100, seed=42):
    """
    Curated QA pairs derived from the graph itself: every typed edge
    becomes a question the pipeline should answer, and every inferred
    conclusion becomes one too (so the proof trail is exercised).
    Returns [(question, expected, backing_key, origin)].
    """
    from ukft_knowledge_graph import KnowledgeGraph

    kg = KnowledgeGraph(path=graph_path).load()
    rnd = random.Random(seed)
    pairs = []

    def add(x, rel, y, origin):
        expect = None
        exact_kind = "exact" if origin == "asserted" else "exactproof"
        if rel == "is_a":
            expect = ("contains", y)
            question = f"what is {x}"
        elif rel == "kin:father_of":
            question = f"is {x} the father of {y}"
            expect = (exact_kind, f"{_name(x)} is the father of {_name(y)}.")
        elif rel == "kin:son_of":
            question = f"is {x} the son of {y}"
            expect = (exact_kind, f"{_name(x)} is the son of {_name(y)}.")
        elif rel == "kin:daughter_of":
            question = f"is {x} the daughter of {y}"
            expect = (exact_kind, f"{_name(x)} is the daughter of {_name(y)}.")
        elif rel in ("kin:child_of", "kin:parent_of",
                     "kin:ancestor_of", "kin:descendant_of"):
            # Inverses and ancestry chains answer exactly too — the
            # gate must exercise derived kinship, not just assertions.
            word = {"kin:child_of": "child", "kin:parent_of": "parent",
                    "kin:ancestor_of": "ancestor",
                    "kin:descendant_of": "descendant"}[rel]
            question = f"is {x} the {word} of {y}"
            expect = (exact_kind, f"{_name(x)} is the {word} of {_name(y)}.")
        elif rel == "contains":
            question = f"where is the {y}"
            expect = ("contains", x)
        elif rel == "located_in":
            question = f"where is the {x}"
            expect = ("contains", y)
        elif rel == "causes":
            question = f"why does {x} happen"
            expect = ("contains", y)
        elif rel == "caused_by":
            question = f"why does {x} happen"
            expect = ("contains", y)
        elif rel == "part_of":
            question = f"is {x} part of {y}"
            expect = ("contains", y)
        elif rel.startswith("compare:"):
            phrase = COMPARE_PHRASES.get(rel[len("compare:"):])
            if not phrase:
                return
            question = f"is {x} {phrase} {y}"
            expect = (exact_kind, f"{_name(x)} is {phrase} {y}.")
        elif rel == "has_property:has":
            head = y.split()[0] if y else ""
            if head not in NUMERAL_HEADS:
                return
            rest = " ".join(y.split()[1:])
            question = f"how many {rest} does {x} have"
            expect = ("contains", y)
        else:
            return
        pairs.append((question, expect, (x, rel, y), origin))

    for (x, rel, y), (conf, _src) in kg.edges.items():
        add(x, rel, y, "asserted")
    from ukft_inference import InferenceEngine
    try:
        inferred = InferenceEngine(out_path=inferences_path,
                                   contradictions_path="none.txt")
        inferred.load()
    except Exception:
        inferred = InferenceEngine(out_path="missing.txt",
                                   contradictions_path="none.txt")
        inferred.derived = {}
    for (rel, x, y) in inferred.derived:
        add(x, rel, y, "inferred")
    rnd.shuffle(pairs)
    return pairs[:n]


# ── GATE MEASUREMENTS ────────────────────────────────────────────
def run_qa(pairs, graph_path=KNOWLEDGE_GRAPH, inferences_path=INFERENCES):
    """
    Run QA pairs through the R4+R5 pipeline.  Returns (correct, total,
    proofless) — proofless counts correct answers whose backing edge
    cannot be found asserted or inferred.
    """
    from ukft_answer import AnswerComposer
    from ukft_inference import InferenceEngine
    from ukft_knowledge_graph import KnowledgeGraph
    from ukft_question import QuestionUnderstanding

    qa = QuestionUnderstanding(graph_path=graph_path,
                               inferences_path=inferences_path)
    composer = AnswerComposer(inferences_path=inferences_path)
    kg = KnowledgeGraph(path=graph_path).load()
    try:
        inferred = InferenceEngine(out_path=inferences_path,
                                   contradictions_path="none.txt").load()
    except Exception:
        inferred = InferenceEngine(out_path="missing.txt",
                                   contradictions_path="none.txt")
        inferred.derived = {}

    correct = 0
    proofless = 0
    for question, expect, backing, _origin in pairs:
        body = composer.compose(qa.run(qa.plan(question)))
        if body is None:
            continue
        kind, target = expect
        if kind == "contains":
            ok = target.lower() in body.lower()
        elif kind == "exactproof":
            # Derived answers speak the proof ("X is the child of Y,
            # because ..."): exact stem plus a justification counts.
            stem = target[:-1] if target.endswith(".") else target
            ok = body == target or (
                body.startswith(stem) and ", because" in body)
        else:
            ok = body == target
        if not ok:
            continue
        correct += 1
        x, rel, y = backing
        if (x, rel, y) not in kg.edges and (rel, x, y) not in inferred.derived:
            proofless += 1
    return correct, len(pairs), proofless


def contradiction_rate(n=20, seed=7, out_kg=None,
                       out_inf=None, out_cont=None):
    """
    Plant n contradictions in a test corpus and measure how many R3
    flags.  8 opposite comparison pairs, 6 is_a cycles, 6 has-vs-lacks
    conflicts (n=20).  Planted files default to the OS temp dir (with
    the PID in the name) so live gate runs never litter the workspace.
    """
    from ukft_inference import InferenceEngine

    import os as _os
    import tempfile as _tf
    _tmp = _tf.gettempdir()
    _tag = f"pid{_os.getpid()}"
    if out_kg is None:
        out_kg = _os.path.join(_tmp, f"r7_planted_kg_{_tag}.txt")
    if out_inf is None:
        out_inf = _os.path.join(_tmp, f"r7_planted_inf_{_tag}.txt")
    if out_cont is None:
        out_cont = _os.path.join(_tmp, f"r7_planted_cont_{_tag}.txt")

    rnd = random.Random(seed)
    lines = ["--- AURA KNOWLEDGE GRAPH (V5 R2) | NODES: 100 | EDGES: 100 "
             "| TS: 1 ---"]
    planted = []

    for i in range(8):
        a, b = f"gca{i}", f"gcb{i}"
        lines.append(f"NODE: {a}\nNODE: {b}")
        lines.append(f"EDGE: {a} | compare:greater_than | {b} | CONF: 0.9 | SRC: p")
        lines.append(f"EDGE: {a} | compare:less_than | {b} | CONF: 0.9 | SRC: p")
        planted.append(("compare", f"({a}, {b})"))
    for i in range(6):
        a, b = f"cyca{i}", f"cycb{i}"
        lines.append(f"NODE: {a}\nNODE: {b}")
        lines.append(f"EDGE: {a} | is_a | {b} | CONF: 0.85 | SRC: p")
        lines.append(f"EDGE: {b} | is_a | {a} | CONF: 0.85 | SRC: p")
        planted.append(("cycle", f"{a} <-> {b}"))
    for i in range(6):
        a, b = f"hpa{i}", f"hpb{i}"
        lines.append(f"NODE: {a}\nNODE: {b}")
        lines.append(f"EDGE: {a} | has_property:has | {b} | CONF: 0.7 | SRC: p")
        lines.append(f"EDGE: {a} | has_property:lacks | {b} | CONF: 0.7 | SRC: p")
        planted.append(("property", f"{a} has and lacks {b}"))

    with open(out_kg, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    engine = InferenceEngine(graph_path=out_kg, out_path=out_inf,
                             contradictions_path=out_cont).infer()
    engine.save()

    detected = sum(
        1 for _kind, marker in planted
        if any(marker in c for c in engine.contradictions)
    )
    return detected, len(planted)


def honest_questions(n=25, seed=11):
    """Questions whose entities exist nowhere in the corpus."""
    rnd = random.Random(seed)
    forms = [
        lambda w: f"what is {w}",
        lambda w: f"who is {w}",
        lambda w: f"where is the {w}",
        lambda w: f"is {w} a thing",
        lambda w: f"when did {w} happen",
        lambda w: f"how many parts does {w} have",
    ]
    out = []
    for i in range(n):
        word = f"zorba{i}"
        out.append(forms[rnd.randrange(len(forms))](word))
    return out


def honest_ignorance_rate(questions=None, graph_path=KNOWLEDGE_GRAPH,
                          inferences_path=INFERENCES):
    from ukft_answer import AnswerComposer
    from ukft_question import QuestionUnderstanding

    questions = questions or honest_questions()
    qa = QuestionUnderstanding(graph_path=graph_path,
                               inferences_path=inferences_path)
    composer = AnswerComposer(inferences_path=inferences_path)
    honest = 0
    for q in questions:
        body = composer.compose(qa.run(qa.plan(q)))
        if body and (body.startswith("I do not know")
                     or body.startswith("I have no record")):
            honest += 1
    return honest, len(questions)


def sample_relations(relations_path=None, n=200, seed=80,
                     audit_path=RELATION_AUDIT):
    """
    Gate R-A material: a deterministic sample (or census when the file
    is smaller) written out for Architect judgement.
    """
    from ukft_relations import RelationExtractor

    eng = RelationExtractor(out_path=relations_path or
                            EXTRACTED_RELATIONS).load()
    items = sorted(eng.relations.items(), key=lambda kv: kv[0])
    rnd = random.Random(seed)
    sample = rnd.sample(items, min(n, len(items)))
    lines = [f"--- RELATION AUDIT SAMPLE | N: {len(sample)} "
             f"| JUDGE EACH LINE 1 (correct) OR 0 (wrong) | TS: "
             f"{int(time.time())} ---"]
    for i, ((typ, sub, x, y), (conf, evid, src)) in enumerate(sample, 1):
        rel = f"{typ}:{sub}" if sub else typ
        lines.append(f"{i}. [{rel}] {x} -> {y} (conf {conf:.2f})")
        lines.append(f"   evid: {evid}")
    bus_write(audit_path, "\n".join(lines) + "\n")
    return len(sample)


def record_judgement(n_correct, n_total, floor=0.85, report_path=EVALUATION_REPORT):
    """
    Gate R-A close-out: the Architect judged the relation audit sample.
    Records the rate in evaluation_report.txt and returns whether the
    floor was met.
    """
    rate = n_correct / max(1, n_total)
    passed = rate >= floor
    status = "PASSED" if passed else "FAILED"
    lines = [l for l in bus_read(report_path).splitlines()
             if not l.startswith("GATE R-A:")]
    lines.append(f"GATE R-A: relation precision {n_correct}/{n_total} "
                 f"({rate:.0%}, floor {floor:.0%}) | {status} by "
                 f"Architect judgement ({time.strftime('%Y-%m-%d %H:%M:%S')})")
    bus_write(report_path, "\n".join(lines) + "\n")
    print(f"[R7] R-A judgement recorded: {n_correct}/{n_total} "
          f"({rate:.0%}) -> {status}")
    return passed


def report(graph_path=KNOWLEDGE_GRAPH, inferences_path=INFERENCES,
           relations_path=None):
    """
    Run every measurable gate and write evaluation_report.txt.
    Returns the measurements dict.
    """
    pairs = generate_qa(graph_path, inferences_path, n=100)
    qa_correct, qa_total, proofless = run_qa(pairs, graph_path,
                                             inferences_path)
    det, planted = contradiction_rate()
    honest, asked = honest_ignorance_rate(
        honest_questions(), graph_path, inferences_path)
    sampled = sample_relations(relations_path)

    lines = [f"--- AURA V5 EVALUATION (R7) | TS: {int(time.time())} ---"]
    lines.append(f"GATE R-B: QA accuracy {qa_correct}/{qa_total} "
                 f"({qa_correct / max(1, qa_total):.0%}, floor "
                 f"{GATE_RB:.0%}) | proof-backed answers lacking: "
                 f"{proofless}")
    lines.append(f"GATE R-C: contradiction detection {det}/{planted} "
                 f"({det / max(1, planted):.0%}, floor {GATE_RC:.0%})")
    lines.append(f"GATE R-D: honest ignorance {honest}/{asked} "
                 f"({honest / max(1, asked):.0%}, floor {GATE_RD:.0%})")
    # Judged gates survive re-measurement: a fresh report must never
    # erase a recorded Architect verdict back to PENDING.
    kept = [l for l in bus_read(EVALUATION_REPORT).splitlines()
            if l.startswith("GATE R-A:") or l.startswith("GATE I-A:")]
    ra = next((l for l in kept if l.startswith("GATE R-A:")), None)
    ia = next((l for l in kept if l.startswith("GATE I-A:")), None)
    lines.append(ra or f"GATE R-A: relation precision — PENDING Architect "
                      f"judgement of {sampled} sampled relations "
                      f"({RELATION_AUDIT})")
    if ia:
        lines.append(ia)
    bus_write(EVALUATION_REPORT, "\n".join(lines) + "\n")
    return {"rb": (qa_correct, qa_total, proofless),
            "rc": (det, planted), "rd": (honest, asked),
            "ra_sample": sampled}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "judge-ra":
        correct = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        total = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        sys.exit(0 if record_judgement(correct, total) else 1)
    m = report()
    print(f"[R7] QA accuracy: {m['rb'][0]}/{m['rb'][1]} "
          f"(proofless: {m['rb'][2]})")
    print(f"[R7] contradiction detection: {m['rc'][0]}/{m['rc'][1]}")
    print(f"[R7] honest ignorance: {m['rd'][0]}/{m['rd'][1]}")
    print(f"[R7] relation sample for judgement: {m['ra_sample']} -> "
          f"{RELATION_AUDIT}")
    print(f"[R7] report -> {EVALUATION_REPORT}")
