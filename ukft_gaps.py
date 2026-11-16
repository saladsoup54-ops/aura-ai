# ukft_gaps.py — AURA Honest Ignorance & Curiosity (V5 R6)
# ==================================================
# "I don't know" is the beginning of curiosity, not the end of an
# answer.  Every honest-ignorance answer — an unresolved entity, an
# unverifiable claim, a temporal question, a known word with no typed
# edges — becomes a knowledge gap in knowledge_gaps.txt, deduplicated
# with counts so repeated questions sharpen the signal.
#
#   - answer_curious() is the R4+R5 pipeline plus gap logging: the
#     answer is unchanged, but the gap behind it is recorded.
#   - curiosity_pass() retargets her existing machinery onto the
#     most-asked unattended gap: the PFC attention director holds the
#     word in focus, and a field pulse makes it a candidate for the
#     discovery engine's bridge hunt — curiosity with a purpose,
#     using the mechanisms she already has.
#   - The Architect's live focus always wins: curiosity never
#     overrides a directive she is holding right now.
# ==================================================

import time

from aura_bus import read as bus_read, write as bus_write
from aura_constants import KNOWLEDGE_GAPS


class KnowledgeGaps:
    """The organism's list of what it does not yet know."""

    MAX_GAPS = 2000   # distinct curiosities; beyond this the stalest
                      # (lowest count) make room — curiosity is attention,
                      # and attention is finite.

    def __init__(self, path=KNOWLEDGE_GAPS):
        self.path = path
        self.gaps = {}   # (kind, words) -> {"count", "attended", "last"}
        self.load()

    # ── PERSISTENCE ─────────────────────────────────────────────
    def load(self):
        self.gaps = {}
        for line in bus_read(self.path).splitlines():
            if not line.startswith("GAP: "):
                continue
            head = line[len("GAP: "):].split(" | ")
            if len(head) < 2:
                continue
            words = head[0]
            parts = dict(p.split(": ", 1) for p in head[1:] if ": " in p)
            try:
                count = int(parts.get("COUNT", "1"))
            except ValueError:
                count = 1
            self.gaps[(parts.get("KIND", "unresolved"), words)] = {
                "count": count,
                "attended": parts.get("ATTD", "0") == "1",
                "last": parts.get("LAST", ""),
            }
        return self

    def save(self):
        lines = sorted(
            self.gaps.items(),
            key=lambda kv: (-kv[1]["count"], kv[0][0], kv[0][1]),
        )
        out = [f"--- AURA KNOWLEDGE GAPS (V5 R6) | KNOWN: {len(lines)} "
               f"| TS: {int(time.time())} ---"]
        for (kind, words), entry in lines:
            out.append(
                f"GAP: {words} | KIND: {kind} | COUNT: {entry['count']} "
                f"| ATTD: {1 if entry['attended'] else 0} "
                f"| LAST: {entry['last']}")
        bus_write(self.path, "\n".join(out) + "\n")
        return len(lines)

    # ── RECORDING ───────────────────────────────────────────────
    def record(self, kind, words, question):
        key = (kind, words)
        if key in self.gaps:
            self.gaps[key]["count"] += 1
            # Fresh evidence of ignorance: the gap becomes curious
            # again even if a previous pass attended to it.
            self.gaps[key]["attended"] = False
        else:
            self.gaps[key] = {"count": 1, "attended": False}
        # One line per gap, always: raw question text (newlines, pipes)
        # would corrupt the line-delimited file.
        self.gaps[key]["last"] = " ".join(
            (question or "").split()).replace("|", "/")[:120]
        while len(self.gaps) > self.MAX_GAPS:
            drop = min(self.gaps,
                       key=lambda k: (self.gaps[k]["count"], k))
            del self.gaps[drop]
        self.save()
        try:
            # V6 C7: unanswered questions feed the epistemic drive.
            from ukft_self import DriveState
            DriveState().adapt("gap")
        except Exception:
            pass
        return True

    def record_plan(self, plan, question, fallback=False):
        """
        Decide whether an executed plan hides a knowledge gap and
        record it.  Gibberish (UNKNOWN intent) is not a gap — there is
        nothing to be curious about.
        """
        intent = plan.get("intent")
        if intent == "UNKNOWN":
            return False
        flags = plan.get("flags") or []
        if any("no temporal" in f for f in flags):
            return self.record("temporal", "", question)
        attested = plan.get("attested") or []
        if attested:
            return self.record("attested_gap",
                               " ".join(attested[:2]), question)
        # An unverifiable claim is a gap about the claim, not about
        # leftover qualifier words ("is dark matter real" gaps on
        # dark matter, never on the word "real").
        if intent == "VERIFY" and plan.get("verified") in (None, False):
            x, y = plan.get("x"), plan.get("y")
            words = (" vs ".join(w for w in (x, y) if w)
                     if x else (" ".join(
                         (plan.get("unresolved") or [])[:2]) or "unknown"))
            return self.record("unverified", words, question)
        unresolved = plan.get("unresolved") or []
        if unresolved:
            return self.record("unresolved",
                               " ".join(unresolved[:2]), question)
        if fallback and plan.get("resolved"):
            # Known entity, no typed edges — the associative pipeline
            # answered, but the assertional layer has a hole.
            return self.record("noedge", plan["resolved"][0], question)
        return False

    # ── CURIOSITY ───────────────────────────────────────────────
    def top_gaps(self, n=5):
        return sorted(self.gaps.items(),
                      key=lambda kv: (-kv[1]["count"], kv[0][0], kv[0][1]))[:n]

    def curiosity_pass(self, field=None, focus_seconds=120):
        """
        Retarget attention onto the most-asked unattended gap: PFC
        focus + field pulse (discovery bait).  Returns the focused word
        or None (nothing usable, or the Architect's focus is live and
        wins).  Under homeostatic INHIBIT the field pulse is skipped —
        attention redirects, excitation does not (piling velocity onto
        an over-tensed field only deepens the inhibition).
        """
        from aura_bus import read as _bus_read
        from aura_constants import HYPO_SIGNAL_FILE
        from aura_field import FIELD
        from ukft_pfc import read_focus, set_focus

        if read_focus():
            return None
        candidates = [kv for kv in self.top_gaps()
                      if not kv[1]["attended"]]
        for (kind, words), entry in candidates:
            # A gap with no usable word (temporal, empty) cannot hold
            # attention — fall through to the next gap, don't give up.
            word = (words or "").split()[0] if words else ""
            if len(word) < 3:
                continue
            set_focus(word, seconds=focus_seconds)
            try:
                if "INHIBIT" not in _bus_read(HYPO_SIGNAL_FILE):
                    target = field or FIELD
                    target.stimulate(word, strength=0.3)
                    # A pulse is velocity; one step lands it in
                    # activation so discovery's field scan sees it.
                    target.step()
            except Exception:
                pass
            entry["attended"] = True
            self.save()
            return word
        return None


def answer_curious(question, graph_path=None, inferences_path=None,
                   gaps=None):
    """
    Full reasoning answer + gap logging: compose the answer, and if it
    is honest ignorance (or the associative fallback), record the gap.
    Returns the answer body (None = associative fallback).
    """
    from aura_constants import INFERENCES, KNOWLEDGE_GRAPH
    from ukft_answer import AnswerComposer
    from ukft_question import QuestionUnderstanding

    qa = QuestionUnderstanding(graph_path=graph_path or KNOWLEDGE_GRAPH,
                               inferences_path=inferences_path or INFERENCES)
    plan = qa.run(qa.plan(question))
    body = AnswerComposer(
        inferences_path=inferences_path or INFERENCES).compose(plan)
    tracker = gaps or KnowledgeGaps()
    tracker.record_plan(plan, question, fallback=body is None)
    return body


if __name__ == "__main__":
    import sys
    for q in sys.argv[1:] or ["what is quasar"]:
        body = answer_curious(q)
        print(f"Q: {q}")
        print(f"[AURA]: {body or '(associative fallback — no proof)'}")
