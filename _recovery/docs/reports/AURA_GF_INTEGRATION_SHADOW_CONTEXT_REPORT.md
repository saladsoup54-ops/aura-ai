# Phase 6 — Audit Finding #6 Shadow Context (CLOSED)

Date/time: 21 Sept 2026
Status: CLOSED — READY FOR REVIEW.

## 1. What this pass did

Closed original audit Finding #6 ("the assembled context bundle is mostly
shadow") by **classifying every context-bundle field at its
producer → reader → selection-use seam** and by closing the one genuine
cognitive gap the audit surfaced.

### Determination

Each bundle key was traced through `ukft_context.assemble()` → its
production readers in `aura_bridge.py` → whether it can influence the
selected winner (per M5 law, "can change or guard the selected
response").

| Field            | Classification | Reader(s) in selection path                     |
|------------------|----------------|-------------------------------------------------|
| `current_user`   | **CAUSAL**     | `m4_selection_state` (person_bound/ownership), `_m4_owned_answer_bearing`, `m14_filter_recall` ownership guard |
| `people`         | DUPLICATE      | people-speech detectors / `_people_action` / `cognitive_stance` read `PeopleModel` directly |
| `architect`      | DUPLICATE      | architect-briefing reads the model, not the bundle |
| `recent`         | DUPLICATE      | M2 topic/M4 G7 read `EpisodicMemory.recent_topic` |
| `facts`          | DUPLICATE      | person-fact path reads `PeopleModel.people` (see seam below) |
| `thread`         | DUPLICATE      | M4/M14 read G7 working memory |
| `gaps`           | DUPLICATE      | policy/affect read `KnowledgeGaps` |
| `drives`         | DUPLICATE      | affect rendering (advisory), no selection reader |
| `threads`        | DUPLICATE      | agenda briefing reads `AgendaModel` |
| `time_window`    | DUPLICATE      | WHAT-plan resolves own window |
| `day`            | **DEAD**       | zero production readers — RETIRED |
| `session`        | **DEAD**       | zero production readers — RETIRED |
| `open_threads`   | **DEAD**       | zero production readers — RETIRED |

### Dead-field retirement

Removed `day`, `session`, `open_threads` from `ukft_context.py:assemble`.
No production code consumed them (structural grep for the bundle-key
readers returned only `_bundle.get("current_user")`). `tests/verify_c5.py`
updated to assert the live contract keys, not the defunct ones.

### The real gap: person-fact questions fell dark

The audit's reproduction was correct in effect but not mechanism: person-
fact questions ("what does sarah like") returned a `dark`/context winner
while the answer sat in the assembled `facts` list. That is not a shadow-
field bug — it is a missing routing case in the person-action seam.

Fix (smallest correct seam, no store/salience/candidate/mouth change):
`_people_question` now resolves `what-does`, `possessive`, `where`, and
`how-old` frames via `_strip_fact_verb` and routes them through the
existing known-person gate into the existing who-is speech, instead of
letting them fall through to the dark/context path.

## 2. Evidence

Suite: `tests/verify_finding06_shadow_context.py` (newly created, registered
in `tests/run_all.py`).

Key receipts:

- **Bundle-reader structural pin:** the only production bundle read
  feeding selection is `_bundle.get("current_user")`.
- **Hostile-bundle perturbation identity:** injecting fabricated content
  into every shadow field (`time_window`, `people`, `architect`, `recent`,
  `facts`, `thread`, `gaps`, `drives`, `threads`) produces a **winner-
  identical and response-byte-identical** turn with no leakage.
- **current_user linkage pin:** M4 `person_bound` tracks the bundle field
  (clean=True, False when cleared).
- **Person-fact M5 receipt (the failure):** known fact flips
  `dark → people` and the held fact ("likes hiking") is spoken; negative
  controls (unknown person Zorblax, non-person queries, content-free
  queries, fact-absent Sarah) all behave correctly.
- **Sibling-frame resolution:** what-does / possessive / where / how-old
  all resolve to the named person's record.
- **ask()/roleplay() parity + cross-user isolation:** known-fact question
  answered from partition A; stranger B gets no Sarah fact and no
  phantom record.
- **Mouth/register boundary pin:** opener register churn never moves the
  winner.
- **Containment:** all writes remain inside the temp root; pinned
  live-state hashes unchanged.

Pre-existing gates re-run green as regression:
- `tests/run_all.py` — 84/84 (was 83 before this pass added the suite).
- `tests/stress_all.py` — 61/61 stress checks, no failures.
- `tests/verify_m14_episodic_influence.py` — all checks pass, causal
  receipts intact (episodic evidence admits / duplicate suppression guards).
- `tests/verify_isolation.py` — production isolation proof passes in a
  fresh temp root; live tree untouched.

## 3. What was deliberately NOT changed

Per preserve-before-extend and fix-the-mechanism-not-the-sentence:

- No salience, candidate weight, or selector math change.
- No change to the person-fact **content** path — the fix routes through
  the existing who-is speech, so the answer is phrased exactly as before.
- No change to mouth/voice, personality, boundaries, rapport, G7,
  episodic policy, or character packs.
- The `facts` field is still assembled (C5 contract intact); only the
  dead keys were retired. The field is classified DUPLICATE because the
  genuine consumer reads authoritative stores, not the assembled bundle.
- The original `AURA_BRAIN_GF_INTEGRATION_AUDIT.md` was **not modified**
  (controlling historical audit).

## 4. Reviewer context

- M5 stays permanent law for every later change.
- The shadow fields are now **proven inert** (hostile-bundle identity
  receipt), so they are documented as duplicate/sidecar rather than a
  latent hazard. A future pass may still prune them for clarity, but that
  would be cleanup, not a correctness fix.
- `current_user`'s causal status is **pinned at this seam only**; earlier
  receipts (M4, M14) still own the broader proof.
- Finding #4 transactional-writeback mechanism is preserved untouched —
  the staged-model / winner-gated-commit architecture that closed Finding
  #4 continues to isolate bundle perturbations from real persistence.

## 5. DONE checklist (per AGENTS.md law 5 + green-gate)

1. Mechanism understood and preserved — yes (bundle assembly untouched
   except retired keys; person-fact seam extended only).
2. Smallest correct implementation — yes.
3. Relevant regression checks pass — yes (C5 updated).
4. Full shipping regression suites pass — yes (84/84).
5. Stress and isolation green — yes (61/61, isolation all-pass).
6. Live state clean — yes (pinned hashes unchanged).
7. `AURA_CHANGELOG.md` entry exists — yes.
8. Relevant authoritative docs updated — yes (this report; CHANGELOG
   post-pass notes; SYSTEM_WHITEPAPER shadow-context line; C5/C7/C8 are
   code-level and not current-doc sections).
9. Stale contradictory claims searched and resolved — the
   "parts of the assembled context remain shadow/non-causal" line in
   SYSTEM_WHITEPAPER has been updated to the Finding-#6 resolution.

## 6. Files changed

Runtime:
- `ukft_context.py` — retired `day`/`session`/`open_threads` from
  `assemble()`.
- `aura_bridge.py` — extended `_people_question`/`_strip_fact_verb`,
  routing person-fact/attribute/where/age frames through the known-person
  gate.

Tests:
- `tests/verify_finding06_shadow_context.py` — new (10 ARMs).
- `tests/run_all.py` — registered the new suite.
- `tests/verify_c5.py` — updated bundle-key contract.

Docs:
- `AURA_CHANGELOG.md` — two entries.
- `SYSTEM_WHITEPAPER.md` — shadow-context line resolved.

Review packet:
- `_review_packet/` — copies only (see manifest).

Result: AUDIT FINDING #6 SHADOW CONTEXT — CLOSED, READY FOR REVIEW.
