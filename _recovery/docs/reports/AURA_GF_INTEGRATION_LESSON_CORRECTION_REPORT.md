# Phase 6 — Audit Finding #8 Lesson Correction (CLOSED)

Date/time: 22 Sept 2026
Status: CLOSED — READY FOR REVIEW.

## 1. What this pass did

Closed original audit Finding #8 ("lessons are not a general correction
mechanism") by determining the truthful architectural role of
correction/lesson state, reproducing three concrete pre-fix failures,
and fixing each at its narrowest legitimate seam — with no new truth
store, no salience change, and no reopened findings (#1, #2, #4, #6
untouched; M1–M4, M13, M14, M16, Pass 1/1A/2 preserved).

### Determination: the ledger is audit/history + review, not truth

Every correction class was traced live through user correction →
detector → proposed action → basal selection → Finding-#4 commit →
write → later-turn reader → answer:

| Class | Action | Retained where | Later-turn effect |
|---|---|---|---|
| bare ("no") | teach_bare | lesson "corrected with no counter-claim" | none — asks for the lesson; claims no retention (already truthful) |
| parseable factual, no graph conflict | teach_held | belief held (`architect-correction`, provisional) + lesson "corrected to:" | later VERIFY answers provisionally — graphless too (new #8 seam) |
| known-person counterclaim | teach_noted + person fact | person fact by addition + lesson "noted correction:" | attribute answers prefer best-match recency (new #8 seam); `describe` lists all |
| counterclaim vs strong proof | contest → confirm/cancel | staged pending → contested-held only on confirm | VERIFY provisional-with-deference; proof never overridden (C10 contract intact) |
| unparsed / free text | teach_noted, no fact | lesson text only | none by design — speech now says exactly that (new #8 seam) |
| explicit review request | teach_review | read-only render | counts + latest banked text (already truthful) |

Corrected truth lives only in the existing authoritative stores.
No selection path reads `lessons.txt` (structural confinement pin +
hostile-lesson identity proof). No new semantic-memory supersession
policy was invented: person facts accumulate by addition (explicit
"never silent erasure" contract kept); pure single-keyword ties stay
recency-biased by design and both facts remain listed.

### Pre-fix failures reproduced (preserved here as evidence)

F1 — accepted correction, no later effect (graphless belief silence):
```
Q='is unix an operating system?' -> dark
Q='actually unix is an operating system' -> teach
    "Noted — I had it wrong. I'll hold that."
    beliefs: [(is_a/unix/operating system, architect-correction, held)]
Q='is unix an operating system?' -> dark   # belief ignored
```
Root cause: `_reasoning_answer` returned `None` before the belief
consult whenever `knowledge_graph.txt`/`inferences.txt` were absent —
true for fresh sandboxes AND fresh API partitions (graph files are
per-user and unseeded). The corrected-truth path existed only where a
graph happened to exist.

F2 — accepted person correction, stale answer wins:
```
Q='Actually Sarah likes tea' -> teach "Noted — I'll keep that in mind."
    sarah facts: ['likes hiking', 'likes tea']   # retained...
Q='What does Sarah like' -> people "Sarah likes hiking."  # ...but stale
```
Root cause: `match_attr_fact` returned the FIRST match.

F3 — overstatement with zero retention:
```
Q='Actually the manifold flux drives everything' -> teach
    "Noted — I'll keep that in mind."   # nothing was kept but text
    lessons: [('' , 'noted correction: ...')]
Q='what drives everything' -> dark, identical to pre-correction
```

### The three seams

1. `aura_bridge.py::_reasoning_answer` — when graph files are absent,
   plan the question (pure parsing, no files touched) and consult
   `_belief_verify`; return the provisional answer with the standard
   `belief-provisional` M3 receipt on a hit, else `None` exactly as
   before. Fresh-user API turns and sandboxes now answer from held
   correction-beliefs; graph-present behavior is untouched.
2. `ukft_people.py::match_attr_fact` — best-match scoring (distinct
   keyword hits, then earliest hit position, then most recent)
   replaces first-match. Attribute-led predicates beat incidental
   mentions regardless of order; accepted corrections surface on
   ties; nothing erased.
3. `aura_bridge.py` teach_noted → `("teach_noted", text, fact|None)`:
   the detector already learned person facts in passing — now it
   carries `(display, fact)` so speech states exactly what was
   retained ("Noted — Sarah likes tea."), while banked-only text
   states exactly that ("banked as a lesson, but I can't answer
   from it yet..."). Same presence bid, no commit-path change
   (read-only kind), self-record ensure preserved.

## 2. Evidence

Suite: `tests/verify_finding08_lessons_correction.py` (new, 50
checks, registered in `tests/run_all.py`).

- **TRUE M5 receipt f8_correction_belief:** identical store/state/
  input; control bypasses `_belief_verify` → `dark` (re-lives F1
  every run); treatment → `reasoning` + provisional answer with the
  `belief-provisional` receipt. `influenced_decision: True`.
- **TRUE M5 receipt f8_person_recency:** identical store (both facts
  held) and input; control first-match → stale "hiking"; treatment
  → corrected "tea". `describe` still lists both (no-erasure pin).
- **Banked-only honesty:** unparsed correction banks the lesson,
  leaves truth stores byte-identical, and the later equivalent
  question is byte-identical to the pre-correction baseline.
- **Review truth:** "what have you learned" renders counts + the
  banked correction text.
- **False-authority guard:** vs-proof counterclaim asks
  confirm/cancel with ZERO pre-confirm belief/lesson writes; after
  confirm, later VERIFY stays provisional with deference ("graph is
  right"). Proof is never overridden — beliefs answer only when the
  graph is silent (unchanged `_belief_verify` guards).
- **Stale-lesson no-hijack:** hostile banked lesson moves neither
  winner nor response on VERIFY and open questions; ledger reads
  structurally confined to `_teach_action`/`_answer_teach`/
  `_commit_teach`.
- **Finding-#4 preserved:** detector stages with zero disk trace;
  real commit boundary with a non-teach winner leaves teach-owned
  files byte-identical; single winner-gated commit site (source
  pin); one win banks once; repeats dedupe (belief overwrite +
  lesson exact-dedupe; noted repeats bounded ≤1 extra row from live
  G7 topic variance, stable after the second, answers unchanged).
- **Persistence/parity/isolation (API route):** correction via ask,
  later answers via fresh-module ask AND mouth-down roleplay
  (belief + person paths on both routes); stranger gets no belief,
  no correction, no lessons, no correction-owned state.
- **Containment:** temp-root only; pinned live hashes unchanged.

## 3. Adversarial review

- **Reviewer A** (false corrections, stale lessons, duplicates,
  losing writes, repeats, free text): 2 valid non-blockers, both
  resolved — (1) single-stem collisions ("live performer" vs
  "lives in Berlin") fixed by position-aware scoring + both-order
  regression arm (residual pure ties documented recency-biased);
  (2) noted-repeat topic variance pinned as bounded/stable in-suite.
  Proof-override, tuple arity, dual-parse inputs, file-free
  planning, and double-learn all dismissed with evidence.
- **Reviewer B** (Finding-#4, isolation, M13, authority, M14,
  roleplay, validity): clean — no valid findings.

## 4. What was deliberately NOT changed

- No saliences, candidate weights, or selector math.
- No belief→graph writes; no proof override; VERIFY-scoped
  provisionality kept (open DESCRIBE-from-belief would make beliefs
  a second truth source — explicitly refused).
- No person-fact erasure or supersession policy (would need an
  explicit Architect decision; none required — recency + full
  retention closes the failure).
- No mouth/voice, personality, boundaries, rapport, G7, episodic,
  agenda, tool, or pack changes.
- The original `AURA_BRAIN_GF_INTEGRATION_AUDIT.md` was **not
  modified**.

## 5. DONE checklist

1. Mechanism understood and preserved — yes (belief/ledger/person
   contracts kept; three narrow seams only).
2. Smallest correct implementation — yes.
3. Relevant regression checks pass — yes (C2/C5/C8/C10/G1/G3/M3/M4/
   M14/F2/F4/F6 green).
4. Full shipping regression — yes (85/85).
5. Stress and isolation green — yes (61/61, isolation all-pass,
   viewer selftest OK).
6. Live state clean — yes.
7. `AURA_CHANGELOG.md` entry exists — yes.
8. Authoritative docs updated — yes (this report; AGENTS.md
   frontier; CAPABILITIES closed-list; WHITEPAPER lesson line;
   tests/README + root mirror).
9. Stale claims resolved — "lessons as correction" removed from all
   open-seam lists.

## 6. Files changed

Runtime:
- `aura_bridge.py` — file-absent belief branch in
  `_reasoning_answer`; `teach_noted` 3-tuple + honest speech;
  docstring updates.
- `ukft_people.py` — `_stem_attr_word` (unchanged, F6) +
  `match_attr_fact` best-match scoring + docstring.

Tests:
- `tests/verify_finding08_lessons_correction.py` — new (10 ARMs).
- `tests/run_all.py` — registered (85 suites).
- `tests/README.md` — suite description.

Docs:
- `AURA_CHANGELOG.md` — appended entry (append-only).
- `AGENTS.md`, `AURA_CURRENT_CAPABILITIES.md`,
  `SYSTEM_WHITEPAPER.md`, `README.md` — Finding #8 closed wording.

Review packet:
- `_review_packet/` — fresh, copies only (see manifest).

Result: AUDIT FINDING #8 LESSON CORRECTION — READY FOR REVIEW.
