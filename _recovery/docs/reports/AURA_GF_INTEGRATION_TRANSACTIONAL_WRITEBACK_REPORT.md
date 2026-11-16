# AURA GF Integration — Finding #4 Transactional Writeback Report

Date: 21 Sept 2026
Status: READY FOR REVIEW
Scope: original `AURA_BRAIN_GF_INTEGRATION_AUDIT.md` finding #4 only.
The original audit is untouched (controlling history). No later finding started.

## 1. The finding

"Writeback is not transactional. People, agenda, beliefs, lessons, and gaps
can write before winner selection; a losing detector can leave state."

## 2. Ownership contract (proven from code, not assumed)

A. CANDIDATE-OWNED — commit iff its candidate wins: people
commit/stage/learn/display/alias/fact, agenda open/close, belief hold,
teach lesson-record/hold/learn.
B. TURN-OWNED — always legitimate, never gated: mention sightings +
speaker-binding init (occurrence truth, no selection consumer);
knowledge-gap recording — winner-independent `(plan, user_input)` inputs,
explicit "logged either way" code comment (`aura_bridge.py`), pipeline
contract in `ukft_gaps.py` (`answer_curious` logs with no winner concept),
direct unit tests in `verify_r6.py` with no winner; sleep-wake on message
receipt; generic post-turn writeback (G7, episodes, rapport, hearing, field).
Already post-selection by construction (not deferred here): tool
request/queue/confirm/cancel, belief contest staging, confirm/cancel
commits, identity reinforcement (vault branch), mouth phrasing.

## 3. Mechanism

Detectors propose against non-persisting staged models: `persist=False`
added to `PeopleModel`, `BeliefStore`, `AgendaModel`, `LessonLedger`
(default `True` — every existing caller byte-identical). Return contracts
unchanged; `save()` and the two direct pending-slot `bus_write`s become
no-ops when `persist=False`. Detection never touches disk.

After basal selection, `_commit_decision_effects` (with `_commit_people` /
`_commit_teach` helpers) replays only legitimate effects exactly once on
fresh persisting models. Each winner block is fail-open. Losers leave owned
stores byte-identical. Answer branches re-read fresh committed state
(verified: no `_staged_` reference in any answer or commit path).

## 4. Why the interim snapshot/rollback was replaced (executed evidence)

Pre-fix probe ran the exact `_f4_snapshot`/`_f4_restore` paths in a sandbox:
snapshot → legitimate bus-locked mid-window write → restore ⇒ the
third-party bytes were destroyed (file byte-identical to pre-turn).
Rollback is "complete" only in the single-writer case; by construction it
cannot distinguish detector-provisional bytes from legitimate bytes, and the
desktop route runs `manifest_thought` with no turn lock. Additionally raw
`open()` bypasses `aura_bus` per-path locks and the `deny_live_write`
sandbox guard, and `except OSError: pass` allows silent partial rollback.
Replaced for these concrete causes — not for cleanliness.

## 5. Corrections applied during the pass

- `ukft_register.py` Finding-#4-era change (`last_picked` / `record=False`)
  audited: dead code (never passed, never read), register outside the
  finding's scope, wiring it would be mouth-adjacent redesign → REVERTED.
  Register opener behavior byte-identical.
- Knowledge-gap ownership determined from evidence (section 2) — no commit
  rule invented; gaps stay on their existing turn-owned path.
- Reviewer A valid finding adopted: commit-phase persist failure killed the
  turn (detector-phase failures were always fail-open) → per-subsystem
  fail-open guards; re-probed green; folded into the suite (ARM 12b).

## 6. Receipt

`tests/verify_finding04_transactional_writeback.py` (53 checks, pristine
sandbox): 7 losing arms byte-identical, 4 winner positive controls,
exactly-once singularity, same-turn rename visibility, turn-owned gap arms,
pre-commit exception arm, commit-failure fail-open arm, persist=False unit
contract, ask() parity + cross-user isolation, roleplay parity (mouth-down),
structural propose<select<commit pin, temp-root + live-hash pins.

## 7. Gates

- Reviewer A (executable adversarial): ALL PASSED (stale-state, double
  commit, failure degradation, pending lifecycle).
- Reviewer B (21 focused suites): ALL PASSED.
- Full `python tests/run_all.py`: 83/83 green; embedded isolation green;
  live state clean (no litter, people.txt pinned). Note: the Task/subagent
  tool was unavailable (usage limit), so both adversarial passes were
  performed as explicit executable probes + inspection, documented here.
- Safe stress: 61/61 green, 1 existing note.
- Viewer checks green (sanctioned invocation); selftest 40 frames + 17 tabs.
- Snapshots: pre-work `aura_20260921_124318` 20/20; post-work
  `aura_20260921_204959` 20/20. No restore required.

## 8. What is deliberately NOT in this pass

Register opener banking on losing proof turns (cosmetic voice-variety, no
consumer — documented limitation); finding #6 shadow fields; finding #10
`memory_writes`; findings #8/#9/#11/#12/#14; salience/mouth/personality/
boundary/product changes. Findings #1/#2 closed-state intact; Pass 1/1A,
G7, M1–M4, M13, M14, M16 intact.

## 9. Files changed

Runtime: `aura_bridge.py`, `ukft_people.py`, `ukft_belief.py`,
`ukft_agenda.py`, `ukft_teach.py`. Tests: new
`tests/verify_finding04_transactional_writeback.py`, `tests/run_all.py`
(registration). Docs: `AURA_CHANGELOG.md`, `AGENTS.md`,
`AURA_CURRENT_CAPABILITIES.md`, `AURA_WANTED_FEATURES.md`,
`SYSTEM_WHITEPAPER.md`, `tests/README.md`. This report.
Original audit untouched.
