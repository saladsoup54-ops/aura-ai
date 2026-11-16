# PHASE 12 M14 EPISODIC INFLUENCE REPORT

Date: 21 Sept 2026
Status: M14 COMPLETE AND HARDENED - READY FOR REVIEW
Scope: bounded episodic influence through the existing reasoning candidate.
No episode candidate, salience change, selector redesign, storage redesign,
M16 viewer feature, or automatic memory correction.

## Purpose

Episodic recall already ran inside the R-track when proof was absent, but any
legacy diary match could become the reasoning answer. M14 adds an explicit
policy at the real selection seam so a lived event can affect the chosen
answer only with usable provenance, while unsafe evidence is withdrawn before
candidate selection.

## Mechanism

- `SovereignEgo._recall_answer()` records every episode contributing to its
  pre-mouth recall text and the recall kind.
- `m14_filter_recall()` runs after M4 and before candidate selection. Topic
  and person-trace recall must have visible evidence and whole-token overlap
  with the resolved query.
- `reply` records cannot become lived-event evidence, including through time
  summaries.
- Query-relevant structured R3 contradictions use M13's shared parsed records
  to suppress one-sided episode claims.
- Singular autobiographical requests require every quoted episode to carry
  current-speaker evidence. Prospective modals are exempt only when the modal
  directly governs `I`; polite outer modal framing cannot mask an embedded
  past self-clause.
- Episode text already represented by active G7 context is suppressed instead
  of competing as a duplicate reasoning answer.
- `DriveState.adapt("recall")` runs only after eligible diary recall wins.
- People answers no longer append raw episode traces outside M14; they use the
  people record and G7 thread context.
- A selected eligible episode contributes bounded `past-interaction`
  provenance to `cognitive_stance`. `build_prompt_from_stance()` labels it
  event memory, not objective proof, and never rereads episodic storage.

## Causal Evidence

`tests/verify_m14_episodic_influence.py` contains two M5 receipts through the
real `SovereignEgo.manifest_thought()` selection seam:

- Relevant episode admitted versus unrelated episode suppressed changes the
  winner from vault to reasoning.
- Active-G7 duplicate suppression versus policy bypass guards the winner from
  reasoning to context.

The suite also proves unrelated perturbation stability, reply exclusion,
substring rejection, contradiction selectivity, ownership, shared-prefix
multi-hit handling, prospective-question preservation, suppressed-drive
immutability, people-route containment, stance provenance, and mouth
obedience.

## Files Changed

- Runtime: `aura_bridge.py`, `ukft_people.py`, `ukft_roleplay.py`.
- Tests: `tests/verify_m14_episodic_influence.py`, `tests/run_all.py`.
- Current docs: `AGENTS.md`, `SYSTEM_WHITEPAPER.md`,
  `AURA_CURRENT_CAPABILITIES.md`, `AURA_WANTED_FEATURES.md`,
  `GF_PRODUCT_SPEC.md`, `tests/README.md`, `AURA_CHANGELOG.md`.
- Report: `AURA_PHASE12_M14_EPISODIC_INFLUENCE_REPORT.md`.

## Preserved Behaviour

- M1/M2/M3/M4/M13, Pass 1/1A, and Target Loop Pass 2 remain green.
- Existing candidate names, saliences, selector math, proof priority, honest
  gaps, G7 continuity, current-person isolation, and tool gates are unchanged.
- Historical episodes are not rewritten, promoted to semantic truth, or
  automatically corrected.
- M16 remains unimplemented; observer/viewer code is unchanged.

## Verification

- Pre-work backup: `backups/aura_20260920_204645` (verified).
- Focused M14 suite: green in a declared temporary state root.
- Full shipping regression: 79/79 suites passed; embedded production
  isolation passed; live state clean.
- Safe stress: 61/61 passed, 1 note.
- Viewer checks: passed.
- Viewer selftest: 40 connectome frames and 17 monitor tabs passed.
- No restore required.

## Known Boundaries

- M14 governs assertoric topic/person-trace episode evidence and preserves the
  existing non-assertoric time-summary/people-record treatment. It is not a
  general natural-language ownership theorem.
- Structured R3 contradiction coverage is inherited from M13; arbitrary prose
  contradiction and memory-correction policy remain open.
- Episodic storage, decay, and scheduling were not redesigned.
- Desktop mouth assembly and M16 viewer influence coverage remain separate
  future work.

## Result

M14 EPISODIC INFLUENCE PROVEN, HARDENED, AND READY FOR REVIEW.
