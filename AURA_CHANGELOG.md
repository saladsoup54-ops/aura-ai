# AURA CHANGELOG

This is the append-only record of meaningful Aura GF changes from Phase 5
onward. Earlier history is preserved in `AURA_PHASE4_CLEANUP_REPORT.md`, the
Phase-2/Phase-3 audit documents, and `_reference/`. Do not fabricate old
entries. If an entry becomes wrong, append a correction instead of rewriting
history.

## 2026-09-19 — Phase 5 Documentation/Governance Normalization

Date/time: 2026-09-19

What changed:
- Rewrote `AGENTS.md` as the current agent manual, with current law/state near
  the top and historical build record separated from current instructions.
- Rewrote `SYSTEM_WHITEPAPER.md` to describe current architecture, capability
  categories, the legacy-dominant selection problem, and the M5->M16 brain
  integration roadmap.
- Rewrote `GF_PRODUCT_SPEC.md` to distinguish built, partial, code-complete but
  not live-proven, not-yet-built, and open Architect decisions.
- Converted `AURA_GOVERNANCE_PROPOSAL.md` from proposal wording to current
  governance while keeping unresolved strategy choices open.
- Rewrote `AURA_WANTED_FEATURES.md` so the NOW work is understandable in plain
  English with M-numbers beside it.
- Created this append-only changelog.

Why it changed:
- Current documents mixed pre-birth fork notes, stale milestone plans, and live
  reality.
- Future agents need current truth without treating historical notes as law.
- The project needed permanent anti-stale rules: no silent changes,
  changelog-required work, and same-pass documentation updates.

Files touched:
- `AGENTS.md`
- `SYSTEM_WHITEPAPER.md`
- `GF_PRODUCT_SPEC.md`
- `AURA_GOVERNANCE_PROPOSAL.md`
- `AURA_WANTED_FEATURES.md`
- `AURA_CHANGELOG.md`

Intended behavioural effect:
- None. This was a documentation/governance-only pass.

Behaviour intentionally preserved:
- Runtime code unchanged.
- Cognition unchanged.
- Selection unchanged.
- Tests unchanged.
- Live state unchanged.
- Cleanup state unchanged.

Tests/checks run:
- No runtime test suite was required because this pass edited documents only.
- Document-only checks performed: cross-document stale-language search and
  consistency review for current status, brain-vs-mouth wording, rapport depth,
  Discord status, character packs, gist scheduling, dynamic gates, memory rules,
  CPU/current floors vs open future strategy, DONE definition, next brain work,
  and future document-update responsibility.

Result:
- Authoritative current documents now agree that Phase 4 cleanup is complete,
  current next work is brain integration, and future meaningful passes require:
  CHANGE -> TEST -> CHANGELOG -> RELEVANT DOC UPDATE -> CROSS-CHECK.

Known limitations / unfinished work:
- No M1-M16 implementation was performed.
- `AURA_CURRENT_CAPABILITIES.md` remains the current capability map from Phase
  3C; it was not changed in this pass because the synchronization did not
  alter capability truth.
- Historical/reference documents under `_reference/` remain intentionally
  outdated as historical evidence.

Unresolved Architect decisions:
- Permanent prohibition vs future allowance of adult/explicit companion
  capability.
- Future GPU/hosted inference.
- Future cloud mouth/model hosting.
- Whether Aura-derived non-companion products are in scope.
- Exact first-words implementation under the never-precede-brain constraint.
- Semantic-memory correction operator surface and approval policy.

Documentation check:
- Current authoritative documents affected by this pass were updated in the
  same pass. Historical/reference documents were not rewritten.

## 2026-09-19 — Phase 5A Observer Classification Wording Correction

Date/time: 2026-09-19

PREVIOUS CLAIM:
- `AGENTS.md` listed observer emitter/viewer/export inside a section labelled
  "Working and causal".
- `SYSTEM_WHITEPAPER.md` listed observer tooling under "Working / Causal
  Systems" even though the bullet said observer-only.

ACTUAL FINDING:
- Observer emitter/viewer/export is working observability infrastructure, but
  it is not causal to Aura's response selection. It reports evidence states
  such as RAN, OUTPUT PRODUCED, OUTPUT USED, and INFLUENCED DECISION. It may
  report causal evidence from other systems; it does not itself create causal
  influence.

CORRECTION:
- `AGENTS.md` now separates systems causal to response selection from working
  observer-only infrastructure.
- `SYSTEM_WHITEPAPER.md` now places observer emitter/viewer/export under an
  explicit "Observer Only / Observability" classification.

Files touched:
- `AGENTS.md`
- `SYSTEM_WHITEPAPER.md`
- `AURA_CHANGELOG.md`

Intended behavioural effect:
- None. Documentation-only correction.

Behaviour intentionally preserved:
- Runtime unchanged.
- Tests unchanged.
- State unchanged.
- Cognition and selection unchanged.

Tests/checks run:
- No runtime tests required. Cross-read of affected documents only.

Known limitations / unfinished work:
- Observer remains observer-only unless future architecture explicitly changes
  that and M5 proves influence.

## 2026-09-19 — Phase 6 M5 Causal-Influence Harness (M5 PROVEN)

Date/time: 2026-09-19

What changed:
- Created `tests/m5_harness.py`: test-only causal probe instrument. Runs the
  real `BasalGanglia.select` with fresh selector state (no hysteresis
  carryover), builds structured causal receipts (subsystem, ran,
  output_produced, output_used, baseline/perturbed values and winners,
  guard_triggered, influenced_decision, evidence), and hard-refuses outside
  `AURA_TEST_MODE=1` with a valid temp state root. Production never imports
  it; production behaviour is identical with or without this file.
- Created `tests/verify_m5_causal.py`: focused shipping M5 suite in the
  project's normal check() style, covering identical input/state baselines,
  selector-level and ego-level positive controls, observer negative control,
  produced-but-unused (mood) disconnection proof, four-state distinctness,
  live-mode override refusal (in-process + child process), temp-root
  containment, pinned live-state hashes, and mouth-exclusion proof.
- Registered the suite in `tests/run_all.py` as
  ("M5 - causal influence harness", "verify_m5_causal.py"), keeping the
  production isolation proof last.
- Updated `tests/README.md`, `SYSTEM_WHITEPAPER.md`,
  `AURA_CURRENT_CAPABILITIES.md`, `AURA_WANTED_FEATURES.md`, and `AGENTS.md`
  in the same pass (see Documentation check below).

Why it changed:
- M5 is the first brain-integration pass: build the measuring instrument
  before rewiring the brain. CALLED != CONNECTED requires proof that
  changing a subsystem's output can change or guard the selected response.
- Exact selection seam traced from current code (not documentation):
  `SovereignEgo.manifest_thought` (`aura_bridge.py:2211`) builds
  `candidates` (2394-2436) plus `context = {"vault_support", "inhibited"}`
  (2437-2440), then `self.ganglia.select(candidates, context)` (2448)
  yields the winner that drives the winner branch (2451-2557). The
  mouth/roleplay path (`aura_master.py:215-298`) runs after selection and
  is excluded from the causal decision by construction (proven: no
  `Roleplay` reference in `manifest_thought` source).

Files touched:
- `tests/m5_harness.py` (new, test-only)
- `tests/verify_m5_causal.py` (new, shipping suite)
- `tests/run_all.py` (suite registration only)
- `tests/README.md`, `SYSTEM_WHITEPAPER.md`, `AURA_CURRENT_CAPABILITIES.md`,
  `AURA_WANTED_FEATURES.md`, `AGENTS.md`, `AURA_PHASE6_M5_REPORT.md`,
  `AURA_CHANGELOG.md` (docs)

Intended behavioural effect:
- None on production. No runtime, salience, scoring, weighting, or selection
  code was changed. No M1/M2/M3/M4/M13/M14/M16 work was performed.

Behaviour intentionally preserved:
- Candidate saliences, `vault_support`/`inhibited` modulation, hysteresis,
  winner branches, grounding, mouth/roleplay, writeback, and all product
  behaviour unchanged.
- Observer emitter/viewer/export remain observer-only (negative control
  proves observer output cannot move the winner; nothing was wired into
  selection to satisfy the test).

Tests/checks run:
- Pre-change snapshot: `python ukft_backup.py` -> `backups/aura_20260919_145813`
  (verify latest: ok 20, bad 0). Live pins captured before/after.
- Baseline before change: `python tests/run_all.py` -> 69/69 green, live clean.
- Focused M5 suite in fresh-temp-dir sandbox workflow
  (AURA_TEST_MODE=1, AURA_STATE_ROOT=temp, PYTHONPATH=repo, AURA_NO_MOUTH=1):
  ALL M5 CAUSAL-INFLUENCE CHECKS PASSED.
- Full suite after change: `python tests/run_all.py` -> 70/70 green
  (69 prior + new M5), LIVE STATE clean, embedded isolation proof green.
- Stress via safe temp-root workflow: 61/61 green.
- Viewer: `tests/verify_view.py` green + `aura_synapse_view.py --selftest`
  OK (40 connectome frames + 17 monitor tabs).
- Live-state hashes identical before/after (vault 81bb663e, people b20bb929,
  graph 3784bfc7, episodic ad9985b4, backups tree unchanged). No test
  residue in live root/users/observer/backups.

Result:
- M5 PROVEN. The harness detects real influence (two positive controls
  flip winners) and real disconnection (observer + mood cannot move the
  winner). Selection seam, test seam, and evidence vocabulary are now
  covered by a shipping regression suite.

Positive/negative controls used:
- Positive A (selector): temporal vault_support 0.0 -> 0.3 flips winner
  voice -> vault with identical candidates (subsystem: 2-C -> 2-D support).
- Positive B (ego, real seam): `_reasoning_answer` None -> proof string
  flips winner vault -> reasoning for identical input/fixture
  ("tell me about dark matter").
- Negative: differing observer emission bursts leave winner unchanged
  (voice -> voice); `BasalGanglia.modulate`/`select` source provably reads
  only `vault_support`/`inhibited`.
- Disconnection: `tone_for` outputs differ (warm vs quiet) yet winner
  unchanged and no selection consumer exists.

Known limitations / systems still unproven:
- PROVEN CAUSAL (M5 receipt): temporal vault_support modulation; reasoning
  candidate (path-conditional: only when `_reasoning_answer` is non-None,
  i.e. proof/gap present and social/identity gates pass).
- PROVEN NON-CAUSAL: observer telemetry (observer-only); mood/affect tone
  (advisory, no selection consumer).
- UNPROVEN / PARTIAL (unchanged, for M1-M4/M13/M14/M16): G7 thread
  suppression of vault, G9 binding influence on selection, rapport/depth
  influence, contradiction gating, episodic boost/suppress policy, field-edge
  influence, legacy vault-resonance dominance quantification.
- `guard_triggered` receipt path exists but no guard case was needed: both
  positive controls prove winner flips.

Unresolved Architect decisions:
- Unchanged (see Phase 5 entry).

Documentation check:
- `SYSTEM_WHITEPAPER.md`: now records the M5 harness, the exact seam, and
  what is proven vs unproven.
- `AURA_CURRENT_CAPABILITIES.md`: M5 evidence section added; existing rows
  untouched (most rows still await M5 proof).
- `AURA_WANTED_FEATURES.md`: M5 marked complete; M1 is the first unfinished
  NOW item.
- `AGENTS.md`: Current Frontier advanced M5 -> M1; M5 kept as permanent law.
- `AURA_GOVERNANCE_PROPOSAL.md`: no wording change needed; M5 remains
  headline law (checked).
- `tests/README.md`: new suite documented.
- Full report: `AURA_PHASE6_M5_REPORT.md`.

## 2026-09-19 — Phase 6A M5 Harness Hardening + Doc Truth Fix

Date/time: 2026-09-19

PREVIOUS CLAIM (Phase 6 entry stands; this appends corrections):
- M5 harness described as fully hardened with an identical-state control.
- `AURA_CURRENT_CAPABILITIES.md` / `SYSTEM_WHITEPAPER.md` / `AGENTS.md`
  grouped many systems under broad "Working / Causal" wording.
- `GF_PRODUCT_SPEC.md` still listed the M5 harness under
  "Not Yet Built / Not Yet Proven".

ACTUAL FINDING (reviewer audit):
- `tests/m5_harness.py` had a fail-open fallback: when `aura_state` could
  not be imported (`_st is None`), `require_test_env()` accepted
  `AURA_TEST_MODE=1` and returned `os.getcwd()` without proving a valid
  temporary non-live state root/CWD.
- The ego-level positive control ran baseline and perturbed sequentially
  in one suite sandbox with only a selected file reset list; full
  starting-state identity was not proven (writeback outside the reset
  list could leak between runs).
- Authoritative docs overclaimed M5 status (broad causal groupings) and
  the product spec was stale on M5.

CORRECTION:
- Harness is now FAIL CLOSED: `aura_state` unavailable (or its checks
  unrunnable) raises `HarnessRefusal` — no fallback, no weakened path,
  even with test mode on. `require_test_root()` truth stays
  authoritative. Regression coverage: in-process validator-absent probe
  plus a true import-failure child (repo stripped from `sys.path`).
- Ego control rebuilt on independent sub-sandboxes (`m5_ego_base` /
  `m5_ego_pert` / `m5_ego_repeat` under the temp root), each seeded from
  one canonical fixture with `newline="\n"` deterministic bytes. The
  suite asserts the full starting file manifest (every file + sha1)
  equals the canonical single-file manifest on both runs, sub-paths are
  disjoint, seed vaults are unmutated, and each run writes back only
  into its own dir (per-run CWDs; lobe I/O is CWD-relative). Only
  intended difference: `_reasoning_answer` None vs proof. Winners still
  vault -> reasoning; criterion remains winner change.
- Docs narrowed to actual receipts: `GF_PRODUCT_SPEC.md` lists the M5
  harness under Built and M1-M4/M13/M14/M16 as not yet proven;
  `AURA_CURRENT_CAPABILITIES.md` splits M5 PROVEN CAUSAL from WORKING /
  CONNECTED — M5 UNPROVEN (nothing demoted to broken);
  `SYSTEM_WHITEPAPER.md` splits M5 PROVEN RESPONSE-SELECTION CAUSAL from
  WORKING / CONNECTED / FUNCTIONAL BUT M5 UNPROVEN; `AGENTS.md` snapshot
  narrowed identically.
- Mood wording made precise everywhere: PROVEN NON-CAUSAL TO THE CURRENT
  RESPONSE-SELECTION SEAM / ADVISORY on the tested path — no claim about
  other future uses. Observer stays observer-only.

Files touched:
- `tests/m5_harness.py` (fail-closed gate + `HarnessRefusal`)
- `tests/verify_m5_causal.py` (independent fixtures, full-manifest
  checks, fail-closed regressions, precise mood wording)
- `GF_PRODUCT_SPEC.md`, `AURA_CURRENT_CAPABILITIES.md`,
  `SYSTEM_WHITEPAPER.md`, `AGENTS.md`
  (`AURA_GOVERNANCE_PROPOSAL.md` checked — no change needed)
- `AURA_PHASE6A_M5_HARDENING_REPORT.md`, `AURA_CHANGELOG.md`

Intended behavioural effect:
- None on production. No runtime, salience, scoring, selection,
  cognition, or product code changed. No M1-M4/M13/M14/M16 work.

Behaviour intentionally preserved:
- All Phase 6 controls still pass unchanged in result (voice->vault;
  vault->reasoning; observer/mood cannot move the winner).

Tests/checks run:
- Pre-change snapshot `backups/aura_20260919_164820` verified ok 20/20;
  live pins captured before/after.
- Focused M5 suite in fresh-temp-dir sandbox workflow: ALL PASSED
  (including new fail-closed + full-manifest checks).
- Full suite, stress (safe temp-root), isolation via run_all only,
  viewer checks/selftest, live-hash compare, residue check: see report.

Known limitations:
- Same as Phase 6, plus: `guard_triggered` receipt path still without a
  guard-case exercise (no suitable guard exists yet; flips suffice).

## 2026-09-19 — Workflow Rule: Permanent Review-Packet Step

Date/time: 2026-09-19

What changed:
- `AGENTS.md` gains a permanent `REVIEW PACKET — EVERY MEANINGFUL PASS`
  rule: after tests, changelog, doc update, and cross-check, each
  meaningful pass builds a disposable `_review_packet/` folder (pass
  report, `_REVIEW_MANIFEST.md`, copies of every changed file, standard
  reviewer-context copies, relevant-only extras; live state, vaults,
  people, observer trace, backups, logs, corpora, and caches excluded by
  default). The packet is not authoritative state, never an execution
  source, and deletable at any time.
- Headline law 12 now reads CHANGE -> TEST -> CHANGELOG ->
  RELEVANT DOC UPDATE -> CROSS-CHECK -> BUILD REVIEW PACKET -> REPORT.
- This pass's own packet (`_review_packet/` with manifest
  `REVIEW_PACKET_WORKFLOW_RULE`) is the first built under the rule.

Why it changed:
- The Architect was manually collecting files for review. One
  disposable folder per pass replaces that cherry-picking with a fixed,
  auditable packet contract.

Files touched:
- `AGENTS.md`
- `AURA_CHANGELOG.md`
- `_review_packet/` (disposable copies only, not authoritative state)

Intended behavioural effect:
- None. Documentation/workflow-only. No runtime, cognition, test,
  selection, state, or product behaviour changed.

Behaviour intentionally preserved:
- Everything runtime. No test, launcher, or document imports or reads
  from `_review_packet/`.

Tests/checks run:
- Docs/workflow-only change: no runtime suites required. Verified by
  read-back: the new AGENTS.md section matches the specified rule
  verbatim in content, and law 12 carries the extended DONE chain.
  No repository ignore/exclusion file exists (no git tooling in this
  tree), so per the rule no ignore wiring was introduced.

Known limitations:
- `_review_packet/` is excluded from ignore tooling only if such
  tooling is introduced later.

## 2026-09-19 — Phase 6B Permanent Review-Packet Workflow

Date/time: 2026-09-19

What changed:
- `AGENTS.md` `REVIEW PACKET` rule rewritten to the full permanent
  spec: Architect drag-one-folder review workflow, fresh-recreate
  packet creation (remove only the previous `_review_packet/`, never
  touch originals, copy never move), always-include list (manifest,
  pass report, every changed file, six standard context files),
  include-when-relevant list (spec, governance, boundaries, mechanism
  runtime/test/audit files), `runtime/`+`tests/` grouping with real
  original paths in the manifest, full manifest field list, extended
  never-include list (identity_core, knowledge_graph, users_probe,
  large generated artifacts added), and the seven-point safety NEVER
  list. Verified in-rule: backups use an explicit named-file list
  (`ukft_backup.py: BACKUP_FILES`), suites run explicit file lists,
  state roots resolve explicit paths — no directory walk can adopt
  the packet as organism state.
- This pass's demonstration packet rebuilt fresh at `_review_packet/`
  (prior workflow-rule packet replaced, originals untouched).

Why it was added:
- The Architect never manually gathers files for external review
  again: finish pass, drag `_review_packet/` into the reviewer, get
  the review, delete the folder.

Files changed:
- `AGENTS.md` (rule text only)
- `AURA_CHANGELOG.md` (this entry)
- `AURA_PHASE6B_REVIEW_PACKET_REPORT.md` (new pass report)
- `_review_packet/` (disposable copies only, not authoritative state)

Intended behavioural effect:
- Zero. No runtime, cognition, selection, test, state, or product
  change. No M1 work.

Behaviour intentionally preserved:
- Everything executable. No runtime code, test, launcher, or document
  imports or reads from `_review_packet/` (verified: no `.py`
  reference; packet copies hash-identical to originals).

Tests/checks run:
- Workflow/documentation-only: no suites required or run. Read-back
  verified the new rule sections; packet contents and hashes verified;
  live state untouched (no snapshot needed for doc copies, no state
  written, no Aura interaction).

Known limitations:
- `_review_packet/` relies on convention + the safety NEVER list until
  repository ignore tooling exists to exclude it formally.

Full report: `AURA_PHASE6B_REVIEW_PACKET_REPORT.md`.

## 2026-09-19 — Phase 7 M1 Memory Relevance / Coherence Gate (M1 PROVEN)

Date/time: 2026-09-19

What changed:
- `aura_bridge.py`: new M1 gate — pure deterministic
  `m1_relevance(resolved_query, concept, data)` /
  `m1_filter_relevant(resolved_query, relevant)` beside
  `PatternEngine`. An anchor competes only on query-coverage,
  anchor-title-aboutness, phrase-coherence, or multi-word topicality
  (all against the RESOLVED current query, or the G7 thread-topic
  query that resolved a contentless follow-up). `manifest_thought`
  filters `relevant` right after the referential-retry block (with a
  topic-judged rescue when a referential input's anchors all fail);
  emptied list withdraws the vault candidate. Per-turn evidence on
  `ego.last_m1` (anchor, resolved query, pass, score, reason).
- `tests/verify_m1_relevance.py` (new, shipping; registered in
  `tests/run_all.py`): weak-overlap rejection over several wordings,
  strong-recall preservation, direct-question eligibility, hijack
  refusal, resolved-query consumption, no-hardcoding scan, M5 receipt
  (admit-all vs gate: vault wins vs guarded to dark), vault-beats-
  weaker, salience-untouched, mouth-exclusion, hash pins.

Why it changed:
- Vault memories sharing one incidental word (or substring) with the
  message could win selection at 0.8 with no relevance proof
  (sunflowers->wine-grower class). MEMORY ACTIVATION != MEMORY
  SELECTION: activation stays broad, selection now requires coherence.

Files touched:
- `aura_bridge.py` (M1 functions + hook + `last_m1` init)
- `tests/verify_m1_relevance.py` (new), `tests/run_all.py` (one line)
- `AURA_CHANGELOG.md`, `SYSTEM_WHITEPAPER.md`,
  `AURA_CURRENT_CAPABILITIES.md`, `AURA_WANTED_FEATURES.md`,
  `AGENTS.md`, `GF_PRODUCT_SPEC.md`, `tests/README.md`,
  `AURA_PHASE7_M1_REPORT.md`
  (`AURA_GOVERNANCE_PROPOSAL.md` checked — M-rule wording unchanged)

Intended behavioural effect:
- Irrelevant vault memories can no longer win on weak overlap; the
  turn falls through to legitimate context/field/dark/voice winners.
- Relevant memories (title-aboutness, full query coverage, shared
  phrase, multi-word topicality, thread-topic follow-ups) compete
  exactly as before at unchanged saliences.

Behaviour intentionally preserved:
- Vault static salience still 0.8 when relevant (asserted in-suite).
  Voice/recap/people/reasoning hierarchy, G7 continuation (now via
  relevance, incl. the 3a/3b/3full thread paths), support/inhibited
  modulation, hysteresis, grounding, mouth, writeback, observer.

Tests/checks run:
- Pre-change snapshot `backups/aura_20260919_172316` (ok 20/20);
  baseline `tests/run_all.py` 70/70 green, live clean.
- Focused M1 in fresh-temp sandbox: ALL PASSED (incl. pre-fix record:
  gate bypassed -> wine-quote vault win; real gate -> dark).
- Hardened M5 suite: ALL PASSED (dark-matter ego control passes the
  M1 gate via title-aboutness).
- Full suite after change: first run 68/71 — three collateral
  failures at the exact frontier (3a single-seed god quote, 3b/3full
  referential follow-ups). Diagnosed honestly: gate too strict on
  single-entity data-only queries + judged retry-ranked anchors
  against bare follow-ups. Fixed generally (query-coverage rule;
  topic-basis + rescue, documented as G7 resolution not M2).
  Final full run: 71/71 green, LIVE STATE clean, isolation green.
- Stress (safe temp-root): 61/61 green. Viewer + selftest OK.
- Live pins identical before/after (vault 81bb663e, people b20bb929,
  graph 3784bfc7, episodic ad9985b4). No residue.

Result:
- M1 PROVEN. M5 receipt: OUTPUT USED + GUARD TRIGGERED /
  INFLUENCED DECISION for the relevance gate.

Known limitations / still unproven:
- Single-word queries fully covered by one incidental data word
  (e.g. "valley" vs a valley-mentioning anchor) still pass by
  coverage; the query has no further content to be incoherent with.
  Documented boundary, not a failure of the stated rule.
- No thread-negative suppression (M2), no reasoning priority (M3),
  no contradiction gating (M13), no episodic policy (M14) — untouched.

Unresolved Architect decisions: unchanged.

## 2026-09-19 — Phase 8 M2 Active-Thread Suppression (M2 PROVEN)

Date/time: 2026-09-19

What changed:
- `aura_bridge.py`: new M2 negative suppression — pure
  `m2_thread_state(memory, raw_input)` (existing G7 `recent_topic` +
  `is_shift`, no second memory system) and `m2_filter_thread`
  withdrawing M1-admitted anchors incoherent with the active thread
  (thread-coherence reuses `m1_relevance` against the thread topic).
  Escapes recorded, never suppressed: no active thread, explicit
  pivot (`is_shift`), query-named anchors (M1 coverage/title-
  aboutness vs the resolved query). Separate per-turn evidence on
  `ego.last_m2` (thread_topic, thread_match, suppression_applied,
  suppression_reason); M1 evidence untouched. Hooked after the M1 +
  rescue block in `manifest_thought`.
- `tests/verify_m2_thread_suppression.py` (new, shipping; registered
  in `tests/run_all.py` before isolation): unit thread-state/filter
  checks, ego-level emotional (bad-day) and object (car/night)
  continuations, pronoun continuation kept on-thread (Sarah vault
  wins), anyway + plain explicit switches release (vault wins),
  single-turn no-thread idle, M5 receipt (bypassed vault wins vs
  M2-active guarded to context), no-hardcoding scan, safety/hash/
  mouth proofs.
- Pre-flight doc correction (recorded honestly): `AURA_WANTED_FEATURES.md`
  listed M2 twice (first copy carried M1's technical meaning, numbering
  duplicated "3."). Merged to ONE correct M2 entry; no meaning invented.

Why it changed:
- M1-admitted memories could still hijack continuing conversations
  (a work-stress log answering "pissed off at work" inside the user's
  own bad-day thread). The active thread now says: resonant but not
  of THIS conversation — sit out. Continuity without imprisonment:
  deliberate switches and explicit requests always release.

Files touched:
- `aura_bridge.py` (M2 functions + hook + `last_m2` init)
- `tests/verify_m2_thread_suppression.py` (new), `tests/run_all.py`
- `AURA_WANTED_FEATURES.md` (M2 dedup + M2 done/M3 next),
  `AURA_CHANGELOG.md`, `SYSTEM_WHITEPAPER.md`,
  `AURA_CURRENT_CAPABILITIES.md`, `AGENTS.md`, `GF_PRODUCT_SPEC.md`,
  `tests/README.md`, `AURA_PHASE8_M2_REPORT.md`
  (`AURA_GOVERNANCE_PROPOSAL.md` checked — M-rule wording unchanged)

Intended behavioural effect:
- Off-thread vault memories no longer take over continuing turns;
  turns fall through to legitimate context/field/dark/voice winners.
- On-thread memories, single-turn recall, explicit switches, and
  direct requests compete exactly as before at unchanged saliences.

Behaviour intentionally preserved:
- M1 gate byte-identical in meaning (asserted in-suite; M1 suite
  green unmodified). No universal vault penalty (single-turn and
  on-thread vault wins proven). No reasoning priority (M3), no
  rapport/mood/person inputs (M4), no thread-positive boosting —
  only narrow negative suppression from existing thread signal.

Tests/checks run:
- Pre-change snapshot `backups/aura_20260919_181313` (ok 20/20);
  baseline 71/71 green, live clean, pins captured.
- Focused M2 in fresh-temp sandbox: ALL PASSED (one honest red en
  route: switch fixtures triggered the recap layer at 0.92 above
  vault — escape worked but recap won; fixtures reworded to
  non-recap explicit switches so the test proves vault-level
  release; mechanism untouched).
- M1 suite: ALL PASSED unmodified. Hardened M5: ALL PASSED.
- Full suite: 72/72 green, LIVE STATE clean, isolation green.
- Stress (safe temp-root): 61/61 green. Viewer + selftest OK.
- Live pins identical before/after. No residue.

Result:
- M2 PROVEN. M5 receipt: RAN + OUTPUT PRODUCED + OUTPUT USED +
  GUARD TRIGGERED / INFLUENCED DECISION for thread suppression.

Known limitations / still unproven:
- M3 reasoning priority, M4 general context scoring, M13
  contradiction gating, M14 episodic policy, M16 viewer coverage.
- Suppression is binary withdraw; graded thread-boost is M4 territory.

## 2026-09-19 — Phase 9 M3 Reasoning / Proof Priority (M3 PROVEN)

Date/time: 2026-09-19

What already existed (audited before editing; preserved, not duplicated):
- Reasoning candidate 0.95 above vault 0.8 with support zeroed while
  any proof/gap/addressed action exists (`aura_bridge.py`).
- VERIFY/COMPARE/WHEN honest gaps returned instead of associative
  drift; open questions with vault resonance fall back to association.
- Social/greeting suppression of gaps; recall/belief provisional paths.
- Hysteresis margin too small to trap proof (0.225 displaces at 0.05).

What was actually missing (found by pre-change sandbox probes):
- A VERIFY/COMPARE/WHEN honest gap stole explicitly requested held
  memory: "when did I buy my car" lost to "I have no record of when
  that happened" while the vault held the purchase answer.

What changed (smallest explicit policy):
- `aura_bridge.py`: `_explicit_memory_request` (structural word sets:
  memory triggers, or first-person + past-aux grammar — never fixture
  phrases). In `_reasoning_answer`'s gap block, a gap for a
  VERIFY/COMPARE/WHEN query that is an explicit memory request yields
  (returns None) when the vault holds an M1-coherent answer; the turn
  returns to the pipeline where vault speaks only if still eligible
  there. Proofs untouched (always win). World-knowledge claims
  ("is zod a planet") keep their gaps. No salience changed anywhere.
- `ego.last_m3` structured evidence (reasoning_present,
  reasoning_kind: proof/honest-gap/gap-yielded-to-memory/
  diary-recall/belief-provisional/none, vault_present,
  priority_applied, priority_reason); reset per call, init per ego.
- `tests/verify_m3_reasoning_priority.py` (new, shipping; registered
  in `tests/run_all.py` before isolation).

Why it changed:
- Thought must beat tempting association — except when "thought" is
  ignorance and the user explicitly asked for held experience. Both
  directions are now proven causally.

Files touched:
- `aura_bridge.py` (exemption + last_m3 only)
- `tests/verify_m3_reasoning_priority.py` (new), `tests/run_all.py`
- `AURA_WANTED_FEATURES.md` (M3 done/M4 next), `AURA_CHANGELOG.md`,
  `SYSTEM_WHITEPAPER.md`, `AURA_CURRENT_CAPABILITIES.md`, `AGENTS.md`,
  `GF_PRODUCT_SPEC.md`, `tests/README.md`,
  `AURA_PHASE9_M3_REPORT.md`
  (`AURA_GOVERNANCE_PROPOSAL.md` checked — M-rule wording unchanged)

Intended behavioural effect:
- Proofs (and eligible gaps) still outrank vault exactly as before.
- Explicit memory requests with held answers are answered from memory
  instead of honest ignorance. Nothing else moves.

Behaviour intentionally preserved:
- All pre-existing priority, support-zeroing, hysteresis, social,
  recall, belief, M1, M2 behaviour (M1/M2 suites green unmodified;
  greeting/voice/recap/people hierarchies byte-identical in logic).

Tests/checks run:
- Pre-change snapshot `backups/aura_20260919_183455` (ok 20/20);
  baseline 71/71 green (M2), live clean, pins captured.
- Pre-change probes (throwaway, sandbox): proof>vault,
  proof>boosted, proof-after-vault-incumbent, VERIFY-gap>vault-quote,
  greeting-voice all ALREADY correct — preserved, now locked by the
  suite. Gap-steals-memory (E2) confirmed broken pre-change.
- Focused M3 in fresh-temp sandbox: ALL PASSED (three honest en-route
  reds, all test-expectation errors about pre-existing voice/recap
  ownership above vault — mechanism untouched; one added a
  resonant-but-distinct vault anchor so the M5 baseline wins vault).
- M1/M2/hardened-M5 suites: ALL PASSED unmodified.
- Full suite: 73/73 green, LIVE STATE clean, isolation green.
- Stress (safe temp-root): 61/61 green. Viewer + selftest OK.
- Live pins identical before/after. No residue.

Result:
- M3 PROVEN. M5 receipts: proof flip (bypassed vault wins vs real
  proof wins) and exemption flip (gap steals vs vault answers) —
  both INFLUENCED DECISION.

Known limitations / still unproven:
- M4 general context scoring, M13 contradiction gating, M14 episodic
  policy, M16 viewer coverage.
- Exemption detects explicit requests structurally; genuinely
  ambiguous cases keep today's hierarchy (voice/recap above vault).
- Single-word-coverage boundary from M1 unchanged.

## 2026-09-19 — Phase 9A M3 Hardening / Review Correction
  (M3 stays PROVEN; M4 NOT STARTED)

Date/time: 2026-09-19

PREVIOUS CLAIM (Phase 9 entry above stands; corrections appended here):
- M3 receipts ran baseline/perturbed sequentially in one sub-sandbox.
- Any first-person + past-auxiliary question counted as an explicit
  memory request for the gap exemption (M1 relevance only).
- `last_m3` reset inside `_reasoning_answer` described as per-turn.

ACTUAL FINDING (review):
- Same-dir sequential runs do not meet hardened M5 fixture law
  (writeback can leak between runs).
- "Was my car made in Germany?" ("my"+"was") plus M1 title-aboutness
  ("My Car") would yield the gap to a model description that answers
  nothing asked — subject-naming is not answer-bearing. Same class:
  "Did my car come from France?", "Was my old laptop built in Japan?",
  "Has my visa been approved?". Additionally, did/has-shaped factual
  questions classify UNKNOWN (not VERIFY), so no gap body even formed
  and vault answered misleadingly with no exemption logic involved.
- Identity/executive turns skip `_reasoning_answer`, so the previous
  turn's `last_m3` stayed visible.

CORRECTION (smallest structural fixes inside M3; M1/M2 untouched):
- Both M3 receipts rebuilt on independent baseline/perturbed
  sub-sandboxes deployed from ONE canonical fixture (vault + graph +
  built inferences); complete starting manifests proven identical
  (locked_patterns + knowledge_graph + inferences + m3_cont), paths
  disjoint, writeback isolated per dir. Receipts now lawfully claim
  same query/state/vault/graph/thread.
- `_explicit_memory_request` returns "trigger" (direct instruction:
  M1 relevance suffices, unchanged) vs "autobiographical" (inferred:
  additionally requires `_m3_answer_bearing` — query content shared
  with anchor DATA beyond the subject title). Positives preserved:
  "when did I buy my car" (residue "buy"), trigger-word requests,
  direct recall. World/self claims without bearing keep gaps.
- UNKNOWN-intent aux-first factual questions ("did/has/...") with no
  proof and no answer-bearing vault resonance now earn an honest
  "I do not know." instead of a misleading quote. Guarded narrowly:
  recall instructions, voice-owned social turns, open/imperative
  phrasings ("what is gravity", "tell me about god"), and
  answer-bearing resonance keep existing paths.
- `last_m3` resets at the top of every `manifest_thought` (no early
  returns exist before selection, verified) via `_fresh_m3()`;
  `_reasoning_answer` keeps its in-turn sets. Regression: proof turn
  then identity ("who are you") and executive ("focus on Mars")
  turns both read kind "none", never stale proof.
- Phase 9 wording narrowed accordingly (no claim that every
  first-person past-tense question is a memory request; per-turn
  reset now true). No other authoritative meaning changed;
  `AURA_GOVERNANCE_PROPOSAL.md` checked unchanged.

Files touched:
- `aura_bridge.py` (exemption kinds, answer-bearing, UNKNOWN-gap
  rule, fresh-m3 reset)
- `tests/verify_m3_reasoning_priority.py` (independent-subsandbox
  receipts, 4 false-positive regressions, staleness sequence)
- `AURA_CHANGELOG.md`, `SYSTEM_WHITEPAPER.md`,
  `AURA_CURRENT_CAPABILITIES.md`, `AURA_PHASE9A_M3_HARDENING_REPORT.md`
  (WANTED/AGENTS/spec/README already correct at M3-done granularity)

Intended behavioural effect:
- Honest gaps now also guard aux-first UNKNOWN factual claims
  without answer-bearing memory. Everything else byte-identical in
  logic: full suite 73/73 green with zero other-suite fallout.

Tests/checks run:
- Focused M3 (fresh temp root): ALL PASSED, incl. new checks (one
  en-route red honestly fixed: exemption comment contained the
  substring "car" tripping the no-hardcoding scan; reworded).
- M1, M2, hardened M5: ALL PASSED unmodified in meaning.
- Full `tests/run_all.py`: 73/73 green, LIVE STATE clean, isolation
  green. Stress 61/61. Viewer + selftest OK. Live pins identical.
  No residue. Pre-change snapshot for the pass:
  `backups/aura_20260919_183455` (ok 20/20; Phase 9 snapshot).

Result:
- M3 HARDENED. Both receipts satisfy hardened M5 fixture law with
  INFLUENCED DECISION.

## 2026-09-19 — Phase 9B M3 Answer-Bearing Semantic Hardening
  (M3 stays PROVEN; M4 NOT STARTED)

Date/time: 2026-09-19

PREVIOUS CLAIM (Phase 9/9A entries stand; corrections appended here):
- Any query-data residue beyond the title proved answer-bearing.
- The broad SovereignVoice MEMORY_TRIGGERS set equalled a direct
  recall instruction for M3.

ACTUAL FINDING (review):
- "My car was made in 1996." shares "made" yet does not answer
  "Was my car made in Germany?" — one residual word permits
  predicate/qualifier mismatch.
- "know/learned/read/absorbed" appear in factual questions where
  held memory must still prove it answers ("do you know if ...",
  "have I learned enough ...", "did I read that tax file").

CORRECTION (structural, inside M3; M1/M2 untouched):
- `_m3_answer_bearing`: residue (query content outside the title)
  must be FULLY covered by anchor data (all of it, not any of it).
  Same-predicate/right-qualifier ("was my car made in 1996") still
  surfaces; wrong-qualifier cases keep gaps.
- `_M3_DIRECT_TRIGGERS` (remember/recall/memory/memories/vault):
  only direct instructions bypass bearing via M1-only relevance.
  know/learned/read/absorbed rejoin normal evidence (trigger-word
  "remember" and autobiographical-with-bearing positives preserved).
- UNKNOWN aux-first factuals without answer-bearing resonance keep
  the honest gap (covers did/has shapes the VERIFY block never saw).
  Bearing-True UNKNOWN claims still speak from memory.
- Suite hygiene fix found en route: shared subdirs let prior turns'
  writeback leak into later runs' resolution/thread state; every
  `run_ego` call now starts thread-free (working/episodic state
  wiped, fixtures untouched).

Files touched:
- `aura_bridge.py` (bearing rule, direct-trigger set, UNKNOWN rule)
- `tests/verify_m3_reasoning_priority.py` (qualifier-pair cases,
  trigger-narrowing cases, per-run isolation)
- `AURA_CHANGELOG.md`, `AURA_PHASE9B_M3_HARDENING_REPORT.md`
  (all other authoritative docs already correct at M3-done
  granularity; governance checked unchanged)

Intended behavioural effect:
- Gaps guard more misleading associations (predicate-mismatched and
  aux-first UNKNOWN claims); fully-accounted memories still answer.
  Full suite 73/73 with zero other-suite fallout proves locality.

Tests/checks run:
- Focused M3 (fresh temp root): ALL PASSED (diagnosed honestly:
  comment-substring scan trip; "read" is a noise word so
  read-fixtures rebuilt on "finish"; voice owns "do you know"
  meta-questions pre-existing; shared-subdir contamination fixed by
  per-run isolation).
- M1, M2, hardened M5: ALL PASSED. Full 73/73, LIVE STATE clean
  (people.txt pinned, no root litter), isolation green. Stress
  61/61. Viewer + selftest OK. No residue.

Live-state note (recorded, not hidden):
- Pinned vault/graph/episodic hashes drifted during the long gate
  window vs the Phase 9 snapshot: vault +290B, graph +2922B
  (append accretion), episodic -19B (normal cap fade), people.txt
  byte-identical. No test process runs unsandboxed (guards would
  raise; focused-suite start/end pins matched); her own backup lobe
  snapshotted mid-window (`backups/aura_20260919_192416`, verify
  20/20). Verdict: ambient organism churn, NOT test damage — so NO
  restore (restoring would erase genuine accretion). Hard gates
  (people pin, root litter) clean throughout.
- Process note: no fresh snapshot preceded 9B's first runtime edit
  (law-6 letter miss); mitigation — Phase 9 snapshot
  `backups/aura_20260919_183455` verified intact 20/20 plus her
  mid-window auto-snapshot; no restore was or is indicated.

Result:
- M3 HARDENED (semantics). Both receipts still satisfy hardened M5
  fixture law with INFLUENCED DECISION.

## 2026-09-19 — Phase 9C M3 Semantic-Predicate Preservation
  (M3 stays PROVEN; M4 NOT STARTED)

Date/time: 2026-09-19 21:01 +02:00

PREVIOUS CLAIM (Phase 9/9A/9B entries remain historical):
- Phase 9B correctly removed know/learned/read/absorbed from M3's
  direct-trigger bypass and said they rejoined answer-bearing evidence.

ACTUAL FINDING (review):
- `_m3_answer_bearing` still tokenized through `_m1_tokens`, whose
  intentionally global `NOISE_WORDS` removes all four words. Subject
  overlap could therefore look fully answer-bearing even when memory
  did not say the user read, learned, or absorbed the subject.

CORRECTION (smallest M3-only semantic layer; M1/M2 untouched):
- Added `_M3_PREDICATE_WORDS` and `_m3_tokens`: M1 content words remain
  the base, while know/learned/read/absorbed are restored only for M3's
  predicate-bearing comparison. `_m1_tokens` and `NOISE_WORDS` did not
  change.
- `_m3_answer_bearing` still requires full residue coverage, now using
  the M3 tokens on query, title, and data. The direct-recall set remains
  remember/recall/memory/memories/vault; no material predicate became a
  bypass.
- SovereignVoice's pre-existing broad memory-audit ownership was not
  redesigned. Normal ego runs prove subject-only memories produce the
  0.95 honest-gap winner, while genuinely bearing memories prevent M3
  gap theft and retain the existing 0.9 voice winner. Test-only voice
  suppression then proves each bearing memory wins vault through the
  real ego selection seam. `do you know` remains voice-owned.

Regression coverage:
- Real ego-seam negative/positive pairs use the exact architectural
  words: tax-file read, French learned, and algebra-lesson absorbed.
  Neutral concept titles ensure the predicate must come from memory
  data, not from the title.
- Phase 9B wrong/right qualifier, full-residue, purchase exemption,
  UNKNOWN protection, proof priority, support zeroing, hysteresis,
  stale-evidence reset, independent M5 sandboxes, and thread-free
  `run_ego` hygiene remain green. M1/M2 meaning and saliences unchanged.

Files touched:
- `aura_bridge.py`, `tests/verify_m3_reasoning_priority.py`
- `AGENTS.md`, `SYSTEM_WHITEPAPER.md`, `AURA_CURRENT_CAPABILITIES.md`,
  `GF_PRODUCT_SPEC.md`, `tests/README.md`, `AURA_CHANGELOG.md`,
  `AURA_PHASE9C_M3_HARDENING_REPORT.md`
- `AURA_WANTED_FEATURES.md` and governance checked; no change required.

Safety and tests:
- Fresh pre-edit snapshot created before runtime modification:
  `backups/aura_20260919_204115`; verified 20/20 before work and again
  after gates.
- Focused M3: ALL PASSED. Separate M1, M2, hardened M5: ALL PASSED.
- Full `python tests/run_all.py`: 73/73 suites passed; embedded
  production isolation green; LIVE STATE clean.
- Safe stress: 61/61 passed, 1 note. Viewer checks passed; viewer
  selftest rendered 40 frames and 17 tabs.
- All four pinned live-state hashes exactly matched the pre-edit
  baseline after the gate window; no ambient drift and no restore.

Result:
- M3 HARDENED. M4 remains NOT STARTED.

## 2026-09-19 — Phase 10 M4 Real Context Into Response Selection
  (M4 PROVEN; M13 NEXT)

Date/time: 2026-09-19 22:08 +02:00

Code truth before change:
- G7 reference resolution, M2 negative thread suppression, dedicated people
  ownership, and a fixed context=0.75 candidate were already causal in narrow
  paths. `_assemble_context()` ran every turn, but no bundle field entered
  general competition; `BasalGanglia` received only vault support and
  inhibition. Conversation mode was computed only after context had won.

Mechanism:
- Added one `m4_selection_state` in `aura_bridge.py`, derived from existing
  working-memory topic, bindings, open question, shift semantics, factual
  query mode, current-person record, surviving M1/M2 anchors, and voice kind.
- Strong dialogue evidence (resolved continuation, answering Aura's open
  question, or a continuation opener) bids context at 0.86. Topic overlap or
  ellipsis alone stays at the legacy 0.75. This clears the 0.05 hysteresis
  above vault 0.80 without approaching voice 0.90, recap 0.92, reasoning
  0.95, or addressed/executive 0.99-1.00 owners.
- Explicit pivots keep a weak 0.75 context bid so G7 can park the old thread
  when no factual candidate exists; query-named plain topic changes reuse
  M1/M2 coherence and release old momentum.
- Generic memory audits retain voice ownership. Answer-bearing specific
  recall can guard that broad voice bid only when first-person ownership is
  supported by partition-local first-person memory or the valid current-user
  name/alias. Base saliences and BasalGanglia math were not changed.
- Added per-turn `last_m4` structured evidence and trace inclusion. It resets
  every turn and contains no chain-of-thought.

Proof and regression:
- New shipping `tests/verify_m4_selection_context.py`, registered before
  production isolation, proves positive continuation, active topic/open
  question/reference handling, explicit/plain switches, current person,
  generic audit versus specific recall, proof/gap/held-memory preservation,
  no universal boost, no fixture hardcoding, and no M13/M14 leakage.
- Hardened conversation receipt: independent complete manifest-equal,
  disjoint sandboxes; legacy M4 output selects vault, real M4 output selects
  context. RAN / OUTPUT PRODUCED / OUTPUT USED / INFLUENCED DECISION.
- Hardened person receipt: same literal query and complete manifest-equal
  fixture; changing only valid current-person binding changes/guards
  vault->voice. RAN / OUTPUT PRODUCED / OUTPUT USED / GUARD TRIGGERED /
  INFLUENCED DECISION.
- M2's receipt now holds M4 at the legacy static bid to isolate M2 causality.
  M3 expectations now record the intended M4 release of answer-bearing
  read/learned/absorbed recall; M3 gap semantics are unchanged.

Safety and gates:
- Required pre-edit snapshot `backups/aura_20260919_212640` created and
  verified 20/20 before runtime editing; verified 20/20 again after gates.
- Focused M4, M3, M2, M1, and hardened M5 green.
- Full `python tests/run_all.py`: 74/74 suites green; embedded production
  isolation green; live state clean.
- Safe stress: 61/61 green, 1 informational note. Viewer checks green; viewer
  selftest rendered 40 frames and 17 tabs.
- No restore: no test/runtime damage was detected.

Scope boundary:
- `current_user` is the only `_assemble_context()` bundle field newly consumed
  by M4. Working-memory thread/open-question/reference truth is read from its
  owning store. Recent episodes/open episode threads remain non-selection for
  M14; contradictions remain non-gating for M13; rapport/mood/drives/agenda
  persistence remain advisory, writeback, or independently owned. M16 viewer
  work was not started.

Result:
- M4 PROVEN. M13 is the first unfinished NOW item.

## 2026-09-19 — Phase 10A M4 Anchor-Local Provenance Hardening
  (M4 stays PROVEN; M13 NOT STARTED)

Date/time: 2026-09-19 23:25 +02:00

Review finding:
- M4's answer-bearing check and current-person check each used real evidence,
  but the person check scanned every M1/M2-surviving anchor. One anchor could
  therefore answer the query while a different anchor supplied a current-user
  name or first-person token. After release, `best_quote()` could also speak a
  different high-resonance, non-answer-bearing anchor.
- The word "ownership" overstated the mechanism: it is bounded lexical
  compatibility, not authenticated historical authorship or provenance.

Mechanism correction:
- Added `_m4_owned_answer_bearing`, which retains `(concept, data)` pairs and
  accepts only answer-bearing anchors whose own text has first-person wording
  or the bound current-user name/key/alias (non-first-person factual queries
  keep their prior compatibility behavior).
- For explicit memory requests released as `specific-recall`, vault bidding,
  reinforcement, and `best_quote()` now receive only that eligible anchor set.
  Thus the answer-bearing evidence, person compatibility, and spoken answer
  share an anchor. Generic audit ownership and all base saliences are unchanged.
- Bindings-only G7 factual-reference continuations are deliberately not
  narrowed by this explicit-memory rule. The first full run exposed that
  boundary with `what about it?`; the condition was corrected and the existing
  gravity continuation now remains on gravity.

Regression coverage:
- Added adversarial real-`SovereignEgo` multi-anchor cases proving an answering
  wrong-person anchor cannot borrow the current user's name or first-person
  wording from another anchor, including a second topic/name variant.
- Added a speaking-provenance case proving a released explicit recall cannot
  quote a non-answer-bearing resonant anchor, plus a direct active-topic-overlap
  assertion. Existing M4 causal receipts and M1/M2/M3/M5 preservation remain
  green.

Files touched:
- Runtime: `aura_bridge.py`.
- Tests: `tests/verify_m4_selection_context.py`, `tests/README.md`.
- Docs: `AGENTS.md`, `SYSTEM_WHITEPAPER.md`,
  `AURA_CURRENT_CAPABILITIES.md`, `AURA_WANTED_FEATURES.md`,
  `GF_PRODUCT_SPEC.md`, `AURA_CHANGELOG.md`,
  `AURA_PHASE10A_M4_HARDENING_REPORT.md`.

Safety and gates:
- Fresh pre-edit snapshot `backups/aura_20260919_225931`, verified 20/20 before
  work and after all gates.
- Focused M4, M3, M2, M1, hardened M5, and Phase 3 full-integration checks
  passed from fresh temporary roots.
- Full `python tests/run_all.py`: 74/74 suites passed; embedded production
  isolation green; LIVE STATE clean.
- Safe stress: 61/61 passed, 1 informational note. Viewer checks passed;
  viewer selftest rendered 40 connectome frames and 17 monitor tabs.
- No restore was required; no test/runtime damage was detected.

Documentation check:
- Current architecture, capability, product, roadmap, agent, and test-contract
  wording now records anchor-local provenance and the lexical/not-authenticated
  meaning of person compatibility. The prior Phase 10 report and changelog
  entry remain unchanged as historical records. Governance and boundary policy
  did not change, so their documents were not edited.

Result:
- M4 remains PROVEN and is hardened against cross-anchor evidence joins and
  wrong-anchor speech. M13 remains the first unfinished NOW item and was not
  started.

## 2026-09-20 — Phase 10B M4 Structural Ownership Eligibility Hardening
  (M4 stays PROVEN; M13 NOT STARTED)

Date/time: 2026-09-20 08:08 +02:00

PREVIOUS BEHAVIOR:
- Owner incompatibility mainly failed to suppress the generic `voice`
  candidate. When the query contained a legacy trigger (`read`, `learned`,
  etc.), `voice=0.90` accidentally beat the wrong-person `vault=0.80`.
  Without such a trigger, M4 could correctly label
  `specific-recall-owner-unproven` while the incompatible vault anchor
  remained eligible and won. Safety therefore depended on wording.

FINDING:
- Ownership is a semantic eligibility rule, not a candidate-ranking accident.
  The pre-fix reproduction (`When did I submit the tax file?`, Bob current,
  Alice-owned answer-bearing anchor, no voice trigger) gave `vault` with
  `gap-yielded-to-memory`, speaking Alice's fact to Bob. Two further
  non-trigger variants also won vault pre-fix. No new phrase list may fix
  this; the mechanism must.

CORRECTION (structural, no grammar redesign, no new triggers):
- M3 VERIFY/COMPARE/WHEN exemption now requires same-anchor ownership for
  autobiographical requests (`_m4_owned_answer_bearing`); otherwise the prior
  honest gap stands.
- M3 UNKNOWN-claim rule likewise requires owned bearing for autobiographical
  queries, so a wrong-person bearing anchor cannot suppress `I do not know`.
- M4 `specific-recall-owner-unproven` now bids `context=0.0` (never filler).
- Post-M4, autobiographical owner-unproven withdraws vault eligibility
  entirely (`relevant` becomes the owned set, hence empty); no fallback to a
  non-bearing anchor. Ordinary recall, G7 bindings continuations, saliences,
  selector math, M1/M2, and direct remember/recall handling are unchanged.

Regression coverage (all real `SovereignEgo`, no production keywords):
- Compatible Alice WHEN query answers vault; same bytes with Bob current gives
  honest reasoning gap (new voice-less M5 receipt RAN/PRODUCED/USED/GUARD/
  INFLUENCED, vault->reasoning).
- Wrong-person non-trigger `Did I repair the laptop?` cannot win vault.
- Split fixtures prove no borrowing across anchors (name or unrelated
  first-person) and no fallback to a non-bearing anchor.
- Same-anchor first-person (`I did repair...`) remains eligible.
- All prior M4 provenance attacks, conversation/person receipts, generic audit,
  G7 Sarah continuation, switches, proof/gap preservation, and M1/M2/M3/M5
  suites remain green.

Files touched:
- Runtime: `aura_bridge.py`.
- Tests: `tests/verify_m4_selection_context.py`, `tests/README.md`.
- Docs: `AGENTS.md`, `SYSTEM_WHITEPAPER.md`,
  `AURA_CURRENT_CAPABILITIES.md`, `AURA_WANTED_FEATURES.md`,
  `GF_PRODUCT_SPEC.md`, `AURA_CHANGELOG.md`,
  `AURA_PHASE10B_M4_HARDENING_REPORT.md` (new).

Safety and gates:
- Fresh pre-edit snapshot `backups/aura_20260919_235205`, verified 20/20
  before work and after all gates.
- Pre-fix suite run reproduced 3 structural vault wins (plus 1 over-broad
  test banned-substring); post-fix M4 green with honest gaps.
- Focused M4/M3/M2/M1/M5 and Phase 3 full-integration green from fresh roots.
- Full `python tests/run_all.py`: 74/74 green; isolation green; LIVE clean.
- Safe stress: 61/61, 1 note. Viewer checks green; selftest 40 frames + 17 tabs.
- No restore required.

Documentation check:
- Architecture/capability/roadmap/agent/product/test-contract wording now
  records eligibility-not-ranking and voice-independence. Phase 10/10A entries
  unchanged as history. Governance/boundaries unchanged, not edited.

Legacy debt noted (narrow, not refactored):
- `MEMORY_TRIGGERS`/`voice.last_kind` still gate generic audits; now
  irrelevant to ownership safety.
- Autobiographical detection still uses `_M3_FIRST_PERSON` + `_M3_PAST_AUX`
  surfaces and exact token agreement (no stemming); first-person anchor sets
  differ slightly (`mine/us/ours` query-side vs `i/me/my/we/our` anchor-side).
- `reason` field still reflects guard state rather than raw ownership.

Result:
- M4 HARDENED — READY FOR M13. M13/M14/M16 not started.

## 2026-09-20 — Phase 11 M13 Contradiction Gating (M13 PROVEN)

Date/time: 2026-09-20 +02:00

PREVIOUS BEHAVIOR (audited from code truth):
- R3 detected semantic contradictions (opposite/reversed comparisons, is_a
  cycles, has-vs-lacks) and `InferenceEngine.save()` wrote them to
  `contradictions.txt`, but NOTHING in the live turn read that file:
  `SovereignEgo.manifest_thought()` never consulted it, and the only reader
  was `AnswerComposer._conflict` (entity-token overlap, VERIFY op only) plus
  a count in the self-model audit. CONTRADICTION DETECTED/STORED did not mean
  CONTRADICTION AFFECTED THE ANSWER.
- Pre-fix reproduction (real R3 fixture, deterministic sandbox): held record
  `opposite comparison: compare:greater_than vs compare:less_than on
  (orion, sirius)` with query `is orion greater than sirius` composed the
  confident proof `Orion is greater than sirius.` and the reasoning
  candidate won; a contested vault anchor (`Zorp multiuser ...` over a
  zorp has-and-lacks multiuser record) won vault and quoted one side as
  settled fact.
- Cortex/field `JUDGEMENT: DISCORDANT` is field-tension state from
  `aura_cortex.py` (deviation from the phase midpoint), unrelated to the
  semantic R-track mechanism; it never armed the guard (regression-pinned).

MECHANISM (smallest, in `aura_bridge.py` only; R3/R4/R5 untouched):
- `parse_contradiction_records()` consumes ONLY the current R3 writer
  format into `{compare, property, isa-cycle}` records; stale/derived lines
  fail closed (skipped, can never guard).
- `m13_proof_guard(plan, records)` attaches the guard to the ANSWERED
  proposition/relation from the existing R4 plan: VERIFY is_a against cycle
  membership, COMPARE against same unordered pair + asked comparator,
  describe/where/why/how_many against rendered result edges. Same subject
  with a different predicate never guards.
- `m13_vault_filter()` withdraws only anchors whole-word-carrying EVERY
  participant token of a subject-named record; arbitrary vault prose is an
  explicit documented boundary (no NLP, no embeddings, no second graph).
- `m13_turn_guard()` runs once per turn after M4: confident proof +
  relevant record -> grounded conflict (reasoning bid withdrawn, dedicated
  `conflict` candidate bids 0.95, winner flips reasoning->conflict);
  no-proof + contested vault anchor -> same conflict wins; honest gaps,
  R5-already-surfaced conflicts, unrelated contradictions, and the M3
  exemption pass through byte-identical. Bounded `last_m13` diagnostic
  state (checked/available/relevant/affected/proposition/guard/count/
  reason/evidence); conflict speaks the existing R5 idiom verbatim and
  bypasses mouth/register. No memory-correction policy decided: conflict
  stays conflict.

Regression coverage (`tests/verify_m13_contradiction_gating.py`,
registered in `tests/run_all.py` before isolation):
- Real-representation parsing (all 4 R3 classes incl. long cycles),
  pre-fix baseline vs guarded perturbation, M5 proof receipt
  (RAN/PRODUCED/USED/GUARD/INFLUENCED, reasoning->conflict) + M5 vault
  receipt + unrelated-contradiction negative control, predicate-specificity
  (proof + vault), multi-record selectivity, empty-state preservation,
  second-pair/second-comparator generality, no auto-resolution across
  wordings/orders, honest gaps, M1/M2/M3/M4 identity beside unrelated
  contradictions, DISCORDANT inertness, no M14 episode vote (behavioral +
  structural), no M16 trace writes, rapport/mood independence, hostile-mouth
  verbatim conflict + structural mouth-exclusion, temp-root safety,
  live-hash pins.

Files touched:
- Runtime: `aura_bridge.py` (M13 section + hook + `last_m13` +
  `conflict` candidate/branch + trace keys; no other runtime file).
- Tests: `tests/verify_m13_contradiction_gating.py` (new),
  `tests/run_all.py`, `tests/README.md`.
- Docs: `AGENTS.md`, `SYSTEM_WHITEPAPER.md`,
  `AURA_CURRENT_CAPABILITIES.md`, `AURA_WANTED_FEATURES.md`,
  `GF_PRODUCT_SPEC.md`, `AURA_CHANGELOG.md`,
  `AURA_PHASE11_M13_CONTRADICTION_GATING_REPORT.md` (new).

Safety and gates:
- Fresh pre-edit snapshot `backups/aura_20260920_083233`, verified 20/20
  before work and after all gates.
- Focused M13 green; R1-R7, M1/M2/M3/M4, hardened M5, Phase 3
  full-integration green from fresh roots.
- Full `python tests/run_all.py`: 81/81 green; isolation green; LIVE clean.
- Safe stress: 61/61, 1 note. Viewer checks green; selftest 40 frames + 17 tabs.
- No restore required.

En-route reds (honest record):
- First focused run: 3 test-expectation failures, all in the new suite's
  own assertions, none in production: two gap checks expected the
  `no-query-relevant-contradiction` reason where the design returns
  `honest-gap-stands` (gaps claim nothing, so nothing is guarded), and one
  M3-exemption receipt assertion targeted a probe that never enters the
  exemption path (voice-audit shape). Corrected to assert designed reasons
  and behavioral vault reachability; M3 internals remain owned by its suite.
- Same-subject predicate probe first hit a gap instead of a proof, so it
  could not prove non-overblocking; fixture gained an uncontested
  faster_than edge on the contested pair, making it a true proof-vs-guard
  test.

Result:
- M13 PROVEN — READY FOR M14. M14 is the first unfinished NOW item.

## 2026-09-20 — Phase 11A M13 VERIFY Proposition-Provenance Hardening
  (M13 HARDENED; M14 NOT STARTED)

Date/time: 2026-09-20 +02:00

BUG (legacy R5 path inconsistent with M13 law):
- `AnswerComposer._conflict(x, y)` decided semantic relevance by
  whole-word entity-token overlap only. A held `property conflict: unix
  has and lacks multiuser` therefore blocked `VERIFY is_a(unix,
  multiuser)` — same entities, different proposition (has_property vs
  is_a). The Phase 11 `already-surfaced-by-r5` bypass then carried that
  false conflict past the new proposition-aware guard untouched.
- Reproduced through code truth pre-fix (deterministic sandbox, REAL R3
  records): R4 plan relation is_a + verified True, property record held,
  no is_a record held, yet R5 emitted `I have read conflicting things
  about that.` and the ego answered conflict. A genuine is_a-cycle
  VERIFY in the same fixture also conflicted (true positive to preserve).

FIX (one semantic rule, smallest mechanism):
- Record format, parser, and proposition guard now live with the R3
  producer in `ukft_inference.py` as `parse_contradiction_records()` +
  `contradiction_guards_plan()` (moved verbatim from the bridge; zero
  semantic change to the rule itself).
- R5 VERIFY consumes the shared rule via `AnswerComposer._contradicted
  (plan)`; the entity-level `_conflict(x, y)` is deleted. No second
  matcher can drift.
- `aura_bridge.py` imports the shared functions and keeps
  `m13_proof_guard` as an alias, so all existing bridge/test imports
  keep working. No M1/M2/M3/M4 code touched.
- Post-fix: property-vs-is_a VERIFY proves (`A unix is a multiuser.`,
  winner reasoning, `no-query-relevant-contradiction`); genuine
  cycle VERIFY still conflicts (via the now-proposition-aware R5 path,
  `already-surfaced-by-r5`); property records still guard only
  property-relation answer paths (how_many receipt: hedged-proof
  baseline vs conflict perturbation).

Regression coverage:
- `tests/verify_r5.py`: the old regression that encoded the false
  property-vs-is_a match now asserts the proof; a genuine-cycle
  VERIFY assertion preserves legitimate surfacing.
- `tests/verify_m13_contradiction_gating.py` §17: single-rule
  structural check (bridge alias identity, R5 consumes the rule,
  `_conflict` gone), Cases 1-5 incl. full ego seam for false-positive
  VERIFY, genuine-cycle VERIFY, compare-record-vs-is_a VERIFY, and the
  how_many property-path guard/control receipt; re-assertion of the
  Phase 11 proof/vault/negative setups. No fixture-phrase special
  cases; no new contradiction classes; R3 production unchanged.

Files touched:
- Runtime: `ukft_inference.py` (shared rule home),
  `ukft_answer.py` (VERIFY consumes it, `_conflict` removed),
  `aura_bridge.py` (import + alias, duplicates removed).
- Tests: `tests/verify_r5.py`, `tests/verify_m13_contradiction_gating.py`,
  `tests/README.md`.
- Docs: `AGENTS.md`, `SYSTEM_WHITEPAPER.md`,
  `AURA_CURRENT_CAPABILITIES.md`, `AURA_CHANGELOG.md`,
  `AURA_PHASE11A_M13_HARDENING_REPORT.md` (new). Phase 11 entry/report
  left unchanged as history.

Safety and gates:
- Fresh pre-edit snapshot `backups/aura_20260920_091433`, verified 20/20
  before work and after all gates.
- Focused M13 (incl. §17), R1-R7, M1/M2/M3/M4, M5, Phase 3 full green.
- Full `python tests/run_all.py`: 81/81 green; isolation green; LIVE clean.
- Safe stress: 61/61, 1 note. Viewer checks + selftest OK.
- One en-route red: an early no-op edit accidentally joined two lines in
  `ukft_inference.py` (`r_of` docstring/code); caught immediately by the
  smoke import, repaired, and covered by the green gates. No restore.

Result:
- M13 HARDENED — READY FOR M14. M14/M16 not started.

## 2026-09-20 - Brain <-> GF Integration Read-Only Audit

Date/time: 2026-09-20 16:34 +02:00

Scope:
- Read-only pre-M14 architecture audit of episodic memory, G7 context,
  people/current-person, rapport, beliefs, lessons, agenda, mood, boundaries,
  personality, writeback, and the observer boundary.
- No production code, tests, live state, M14 policy, or M16 observer work was
  changed.

Findings recorded:
- G7, people/current-person, agenda, beliefs, teach intents, episodic
  recording/recall, and generic turn writeback are inside the UKFT turn
  lifecycle, with M5-proven influence limited to the already proven
  M1/M2/M3/M4/M13 subsets.
- Episodic recall can feed the reasoning candidate, but no explicit
  provenance-aware episode boost/suppress policy or isolated M14 causal receipt
  exists. M14 remains the first unfinished NOW item.
- Rapport is persistent and bidirectional and can change final roleplay
  phrasing, but it does not enter the basal selector. Stateless affect is
  phrasing/advisory at the tested seam. Amygdala-to-field winner influence
  remains unknown.
- Character packs are birth-time sidecars that seed brain files; existing-user
  personality is duplicated across profile, prompt tables, boundaries, and
  seeded identity/vault state. Several pack knobs have no established runtime
  consumer.
- Writeback is distributed and non-transactional. Several companion detectors
  can write before selection. The API copies only non-empty files back to a
  partition, so cleared pending people/belief files can fail to persist.
- The desktop organism and GF Brain API have different lifecycles: API turns
  swap partition files through root paths, clear the global field, do not
  restore persisted field state, and do not launch desktop background lobes.
- The normal Discord `BrainModule.roleplay()` route does not emit the observer
  turn sequence, and the API's temporary basal decision log is restored rather
  than retained per user.
- One normal meaningful Discord/GF conversation was traced from input through
  selector, roleplay, and writeback, including an exact map of where the
  experience remains afterward.

Files touched:
- `AURA_BRAIN_GF_INTEGRATION_AUDIT.md` (new audit report).
- `AURA_CHANGELOG.md` (this append-only record).
- `_review_packet/` (fresh disposable copies and manifest only).

Intended behavioural effect:
- None. Documentation/evidence only.

Behaviour intentionally preserved:
- Runtime and candidate saliences unchanged.
- Tests and test contracts unchanged.
- Live root state and user partitions unchanged.
- M14 and M16 not started.

Tests/checks run:
- No runtime tests were run. The task was a read-only architecture audit and no
  runtime/test mechanism changed.
- Static cross-checks covered the two production entry paths, selector seam,
  store writers/readers, field/working/vault involvement, decay,
  sleep/consolidation, retrieval, source-of-truth, partition writeback, current
  authoritative claims, and prior M5 evidence labels.
- Report was re-read after creation; scoped classification labels and required
  lifecycle fields were checked against cited code.

Documentation check:
- No current authoritative architecture, product, policy, roadmap, governance,
  agent, or test-contract claim required a truth change. Current documents
  already describe episodic M14 as unfinished, rapport/mood as non-causal to
  the selector, observer as observer-only, and API/background limitations as
  partial.
- `AUDIT_REPORT_COGNITIVE_PATH.md` contains older superseded conclusions but is
  historical audit evidence, not a current authoritative document; it was not
  rewritten.

Result:
- BRAIN <-> GF AUDIT COMPLETE. READY FOR ARCHITECTURE REVIEW.

## 2026-09-20 - AGENTS.md Brain-Goal Correction (docs only)

Date/time: 2026-09-20 17:07 +02:00

What changed:
- `AGENTS.md` Current Architecture Snapshot now names the original UKFT brain
  as the working core and GF/companion systems as later additions.
- Records the 20 Sept 2026 Brain<->GF audit finding: G7, people/current-person,
  beliefs, agenda, teaching, and episodic recall connect into cognition and
  response selection, but that is not the same as being part of the original
  UKFT brain.
- Sets the current goal as GF EXPERIENCE <-> OLD BRAIN INTEGRATION:
  GF experience -> original UKFT brain -> existing brain lifecycle -> later
  retrieval, starting narrow with real conversation/episodic experience.
- Sets the current sequence to
  M5 ✅ → M1 ✅ → M2 ✅ → M3 ✅ → M4 ✅ → M13 ✅
  → GF EXPERIENCE ↔ OLD BRAIN INTEGRATION ← NOW → M14 → M16.
- Explicitly lists real-but-not-now work: Discord/API redesign, general
  multi-user cleanup, partition overhaul, personality rewrite, rapport
  redesign, complete transactional writeback redesign, M14, M16.
- Records that the Brain<->GF audit was read-only with no
  runtime/test/state changes.

Files touched:
- `AGENTS.md`
- `AURA_CHANGELOG.md`
- `_review_packet/` (fresh disposable copies and manifest only)

Intended behavioural effect:
- None. Documentation-only correction. No integration work started.

Behaviour intentionally preserved:
- Runtime code unchanged.
- Tests unchanged.
- Live state unchanged.
- M14/M16 not started.

Tests/checks run:
- No test suite run: documentation-only pass with no runtime/test mechanism
  change.

Documentation check:
- `AGENTS.md` updated in the same pass. No other authoritative document needed
  changing for this correction.

Result:
- Brain goal preserved for future agents. Integration work not started.

## 2026-09-20 - Roadmap Alignment Correction (docs only)

Date/time: 2026-09-20 17:19 +02:00

CORRECTION:
- `AGENTS.md` already set the frontier to
  M5 ✅ → M1 ✅ → M2 ✅ → M3 ✅ → M4 ✅ → M13 ✅
  → GF EXPERIENCE ↔ OLD BRAIN INTEGRATION ← NOW → M14 → M16,
  but `AURA_WANTED_FEATURES.md` still called M14 the first unfinished NOW
  item and `SYSTEM_WHITEPAPER.md` still listed M14 as the next roadmap step.
  Those two files now agree with `AGENTS.md`: GF EXPERIENCE ↔ OLD BRAIN
  INTEGRATION is the current unfinished NOW work; M14 and M16 are later
  milestones.
- Cross-checked `AURA_CURRENT_CAPABILITIES.md`, `GF_PRODUCT_SPEC.md`,
  `AURA_GOVERNANCE_PROPOSAL.md`, `gf_boundaries.md`, and `tests/README.md`:
  no stale roadmap/current-work wording found there; unchanged.
- Historical phase reports and earlier changelog entries were left unchanged
  as history.

Files touched:
- `AURA_WANTED_FEATURES.md`
- `SYSTEM_WHITEPAPER.md`
- `AURA_CHANGELOG.md`
- `_review_packet/` (fresh disposable copies and manifest only)

Intended behavioural effect:
- None. Documentation-only correction. No integration work started.

Behaviour intentionally preserved:
- Runtime code unchanged.
- Tests unchanged.
- Live state unchanged.
- M14/M16 not started.

Tests/checks run:
- No test suite run: documentation-only pass with no runtime/test mechanism
  change.

Result:
- All current authoritative docs now agree on the frontier. Integration work
  not started.

## 2026-09-20 - GF-Old-Brain Pass 1 Hearing Bridge (M5 stays law)

Date/time: 2026-09-20 +02:00

What changed:
- `aura_bridge.py` only (~30 lines): new `_hearing_ingest` runs each turn's
  input through the REAL thalamic sensory gate (`process_records` with a
  production `ReticularFormation` into the shared `FIELD`), called
  post-selection in the writeback section with a `hear=True` default
  (`hear=False` is the test control arm; all production call sites use the
  default).
- New shipping `tests/verify_brain_gf_pass1.py` (registered in
  `tests/run_all.py` before isolation; `tests/README.md` indexed): gearbox
  fixture proves enter (field nodes/edges, velocity not hand-set activation,
  vault never written) -> react (heartbeat steps activate) -> survive
  (in-process field across turns) -> retrieve (fresh ego, G7/episodic wiped,
  `field` winner names GEARBOX), plus hear=False and field-wiped controls and
  a silent-manifold dark contract.
- Docs: new `AURA_BRAIN_GF_PASS1_REPORT.md`; `AGENTS.md` frontier notes Pass 1
  complete-ready-for-review with desktop double-hear accepted and API
  cross-turn carry absent by existing policy; `SYSTEM_WHITEPAPER.md` Core Flow
  + frontier; `AURA_CURRENT_CAPABILITIES.md` working + partial API limit.

Why it changed:
- GF conversation reached G7/episodic/rapport but never the old brain's
  sensory-field path on the GF route; the old brain never experienced it.
  The bridge connects the experience to existing machinery (gate, physics,
  sleep input, forgetting) instead of a new store, without bypassing the
  dream gate into the vault.

Files touched:
- Runtime: `aura_bridge.py`.
- Tests: `tests/verify_brain_gf_pass1.py`, `tests/run_all.py`,
  `tests/README.md`.
- Docs: `AURA_BRAIN_GF_PASS1_REPORT.md` (new), `AGENTS.md`,
  `SYSTEM_WHITEPAPER.md`, `AURA_CURRENT_CAPABILITIES.md`,
  `AURA_CHANGELOG.md`.
- `_review_packet/` (fresh disposable copies and manifest only).

Intended behavioural effect:
- Field now carries each turn's input words (velocity) for the next turn;
  desktop hears the input twice (async pre-turn + sync post-turn, accepted).
  Current-turn selection is byte-identical by construction (post-selection
  hook); no salience changed.

Behaviour intentionally preserved:
- M1/M2/M3/M4/M13 selection behavior unchanged; vault/cortex/dream paths
  untouched; conversation still never auto-vaults; M14/M16 not started.

Tests/checks run:
- Snapshot `backups/aura_20260920_173926` verified 20/20 before editing.
- New focused suite green; M5/M1/M2/M3/M4/M13 focused green (temp roots).
- Full `python tests/run_all.py`: 76/76 green; isolation green; live clean.
- Safe stress: 61/61, 1 note. Viewer selftest: 40 frames + 17 tabs OK.
- No restore required.

Known limitations / not integrated:
- API-route cross-turn field carry absent (clear per ask, no auto-restore —
  deliberate policy, not redesigned); desktop double-hear accepted; only the
  user input (not Aura's replies/people/beliefs/lessons) is bridged.

Result:
- GF↔OLD BRAIN PASS 1 COMPLETE — READY FOR REVIEW.

## 2026-09-20 - Target Cognitive Loop Documentation (docs only)

Date/time: 2026-09-20

What changed:
- `AGENTS.md`: new permanent section `Target Cognitive Loop — Permanent
  Architecture Intent` after the Current Architecture Snapshot's old-brain
  vs GF boundary note. Records the intended end-state loop (USER → GF
  INTERPRETATION → ORIGINAL UKFT BRAIN → CURRENT UNDERSTANDING / STANCE /
  RESPONSE INTENT → MOUTH → RESPONSE → BRAIN WRITEBACK → NEXT TURN), the
  relevant-systems contribution rule (conversation/context,
  people/current-person, episodic history, beliefs, relationship/rapport,
  personality, boundaries, internal state, relevant memories feed the old
  brain; no blind whole-file dumps into the mouth prompt), the UKFT brain
  as central integration point, the preserved brain-vs-mouth rule, the
  experience/writeback feedback loop, the Pass 1 narrow-crossing
  clarification, the incremental structurally-and-causally-proven
  constraint, and the ONE ORGANISM line.
- `SYSTEM_WHITEPAPER.md`: new concise `Target Cognitive Loop
  (Intended End-State)` section after Core Flow, explicitly labelled as
  target rather than current truth.
- `AURA_TARGET_LOOP_REPORT.md` (new pass report).

Why it changed:
- Future agents must not mistake Pass 1 ("conversation enters FIELD"
  through the real thalamic/field path) for the final architecture. The
  end-state — one organism with a brain-centered loop, not one selector
  surrounded by twenty databases — is now explicit permanent intent.

Cross-check:
- Read all current authoritative documents (`AGENTS.md`,
  `SYSTEM_WHITEPAPER.md`, `AURA_CURRENT_CAPABILITIES.md`,
  `AURA_WANTED_FEATURES.md`, `GF_PRODUCT_SPEC.md`,
  `AURA_GOVERNANCE_PROPOSAL.md`, `gf_boundaries.md`, `tests/README.md`).
- No current wording directly contradicts the target: existing
  selector/candidate/roadmap text describes current truth, which the new
  sections explicitly distinguish from the intended end-state. Only the
  two files above were changed.

Intended behavioural effect:
- None. Documentation-only. No architecture implemented.

Behaviour intentionally preserved:
- Runtime code unchanged.
- Tests unchanged.
- Live state unchanged.
- Pass 1A, M14, M16, rapport redesign, personality redesign, and any
  general brain rewrite not started.

Tests/checks run:
- No test suite run: documentation-only pass with no runtime/test
  mechanism change. Read-back verified both new sections.

Documentation check:
- `AGENTS.md` and `SYSTEM_WHITEPAPER.md` updated in the same pass. No
  other authoritative document needed changing.

Result:
- TARGET COGNITIVE LOOP DOCUMENTED — READY FOR REVIEW.

## 2026-09-20 - GF-Old-Brain Pass 1A Real Turn Persistence (M5 stays law)

Date/time: 2026-09-20 +02:00

Why Pass 1 was incomplete (traced from code truth):
- `BrainModule.ask`/`roleplay` cleared the process-global `FIELD.nodes`
  every turn for isolation, but nothing ever called the existing
  `SovereignEgo.restore_field_state()` — the Pass-1 receipt kept one
  in-process field alive and never met the real boundary.
- `_save_field_state()` ran only on voice/reasoning/conflict/vault
  winners, while `_hearing_ingest` runs after all of them — the heard
  experience (velocity + edges, activation zero) was never persisted.
- `field_state.txt` stored activation only; heard velocity and
  association edges could not cross the boundary.

What changed (smallest lifecycle fix; no selector, salience, or
gate-logic change):
- `aura_bridge.py`: `_save_field_state` now also writes `edge|a|b|weight`
  lines for edges between saved nodes (node lines byte-identical legacy
  format); `restore_field_state` rebuilds nodes then edges. Backward
  compatible both ways. Velocity deliberately not persisted (converted
  by real heartbeat first); phase recomputed by `step()`.
- `ukft_brain_api.py`: both `ask()` and `roleplay()` restore the user's
  `field_state.txt` after the partition swap (clear-first isolation
  kept; missing file is a clean no-op; desktop path untouched), and run
  new `_settle_user_field` after `manifest_thought` returns — fixed
  3-step real `FIELD.step()` heartbeat (`FIELD_SETTLE_STEPS`, Pass-1
  precedent) plus persist before the `from_root` sync, with scoped
  empty-manifold cleanup of root + partition copies. Selection, response,
  and all M-gates are decided before any of this runs.
- `tests/verify_brain_gf_pass1a.py` (new, shipping; registered in
  `tests/run_all.py` before isolation; `tests/README.md` indexed):
  same-user retrieval across fresh module instances with G7/episodic
  neutralized (nodes + restored `gearbox—problem` edge proven),
  cross-user isolation with return-to-A, persistence-deleted dark
  control, roleplay-route sharing into an engine turn, Pass-1 invariants
  (no auto-vault, current-turn winner untouched, saliences intact),
  lifecycle/isolation source guards, temp-root safety, live-hash pins.
- Docs: new `AURA_BRAIN_GF_PASS1A_REPORT.md`; `AGENTS.md` frontier notes
  Pass 1A hardened-ready-for-review; `SYSTEM_WHITEPAPER.md` Core Flow +
  frontier + target-loop clarification; `AURA_CURRENT_CAPABILITIES.md`
  working bridge + corrected API carry wording; `AURA_WANTED_FEATURES.md`
  Pass 1/1A receipts under the still-NOW integration item.

Why this shape:
- User-owned by construction (restored file is the swapped partition
  copy); no global field left alive; no new memory database; existing
  gate/physics/serializer mechanisms reused, minimally extended.
- Desktop double-hear deliberately NOT redesigned: async stimulation is
  not guaranteed (asleep/INHIBIT skips it), so no safe suppression
  exists — left documented.

Files touched:
- Runtime: `aura_bridge.py` (serializer only), `ukft_brain_api.py`
  (restore + settle lifecycle only).
- Tests: `tests/verify_brain_gf_pass1a.py` (new), `tests/run_all.py`,
  `tests/README.md`.
- Docs: `AURA_BRAIN_GF_PASS1A_REPORT.md` (new), `AGENTS.md`,
  `SYSTEM_WHITEPAPER.md`, `AURA_CURRENT_CAPABILITIES.md`,
  `AURA_WANTED_FEATURES.md`, `AURA_CHANGELOG.md`.
- `_review_packet/` (fresh disposable copies and manifest only).

Intended behavioural effect:
- Each GF user's heard experience persists across API turns and is
  retrievable through the old-brain field path next turn; other users
  unaffected; empty manifolds stay empty.

Behaviour intentionally preserved:
- M5/M1/M2/M3/M4/M13 selection behavior unchanged; saliences unchanged;
  vault/cortex/dream paths untouched; conversation still never
  auto-vaults; desktop lifecycle untouched; M14/M16 not started; no
  personality/rapport/people integration; no brain→mouth synthesis.

Tests/checks run:
- Snapshot `backups/aura_20260920_184906` verified 20/20 before editing.
- New focused suite green (all arms, first run).
- Full `python tests/run_all.py`: 77/77 green; isolation green; live clean.
- Safe stress: 61/61, 1 note. Viewer checks + selftest OK
  (40 frames + 17 tabs).
- No restore required.

Known limitations / not integrated:
- API turns still run no sleep consolidation, Ebbinghaus decay, or
  ambient timing — saved warmth persists until later-turn leak steps
  cool it. Only user input bridged. General `from_root` empty-file
  quirk unchanged (field state has scoped cleanup).

Result:
- GF↔OLD BRAIN PASS 1A HARDENED — READY FOR REVIEW.

## 2026-09-20 - Target Loop Pass 2 Brain-Owned Stance/Intent (M5 stays law)

Date/time: 2026-09-20 +02:00

Why this pass exists:
- Pass 1/1A solved input entering the old brain and surviving the turn
  boundary. But on the roleplay path the mouth still reassembled meaning
  after the brain: personality, depth, rapport lane, person facts,
  dialogue, and mirror briefs were gathered from separate files and
  handed to the mouth beside the engine template — a second,
  mouth-side interpretation authority.

What changed (narrow slice: person + rapport/relationship + personality
expression + conversational understanding; no selector/salience change):
- `aura_bridge.py`: new total (fail-open) `SovereignEgo.cognitive_stance`
  forms the brain-owned result from the decision trace, the live people
  model, G7 dialogue, the freshly observed rapport ledger, and passed
  personality/expression config — understanding (reuses
  `_trace_understanding`), person (live model, same-turn writes
  included), relevant history (bounded dialogue + understanding line +
  resolution), stance (ledger rapport line + lane + persona card;
  existing vocabulary only, no new taxonomy), intent (winner/mode/label
  + policy closing question + engine template), plus carried mirror,
  volunteer garnish, felt-affect line, and activity grounding. Stored as
  `ego.last_stance`.
- `ukft_roleplay.py`: new `build_prompt_from_stance` — same prompt via
  `build_prompt`, but every state-derived ingredient comes from the
  stance; static product copy stays mouth-rendered phrasing material.
  Legacy `build_prompt`/`assemble_context`/`mirror_for` signatures
  untouched (desktop route + tests keep them).
- `ukft_brain_api.py`: `roleplay()` consumes the stance as its only
  prompt entry (depth for speak/post-check is the brain's fresh stage);
  the separate lane helper was deleted (lane lives in the stance).
  Desktop master assembly deliberately untouched (different route).
- `tests/verify_loop_pass2.py` (new, shipping; registered before
  isolation; `tests/README.md` indexed): person perturbation (learned
  name vs unbound), relationship perturbation (warm-seeded vs fresh
  ledger, expression identical), personality perturbation (flirty vs shy,
  relationship identical, nothing invented), sidecar-corruption
  mouth-obedience identity (byte-identical prompt), rich-rapport negative
  control (vault-held fact still wins, intent reflects it), legacy
  signature + salience + source + safety pins.
- Docs: new `AURA_TARGET_LOOP_PASS2_REPORT.md`; `AGENTS.md` frontier;
  `SYSTEM_WHITEPAPER.md` Core Flow + frontier + target-loop note;
  `AURA_CURRENT_CAPABILITIES.md` working stance; `AURA_WANTED_FEATURES.md`
  Pass 2 receipt under the still-NOW integration item.

Files touched:
- Runtime: `aura_bridge.py` (stance builder only), `ukft_roleplay.py`
  (new adapter only), `ukft_brain_api.py` (roleplay consumption only).
- Tests: `tests/verify_loop_pass2.py` (new), `tests/run_all.py`,
  `tests/README.md`.
- Docs: as above plus `AURA_CHANGELOG.md`.
- `_review_packet/` (fresh disposable copies and manifest only).

Intended behavioural effect:
- Roleplay prompts now carry brain-interpreted person/stance/intent;
  depth/lane/mirror follow the fresh ledger rather than the pre-turn
  cache. Same winners, same templates, same product copy.

Behaviour intentionally preserved:
- M5/M1/M2/M3/M4/M13 + Pass 1/1A behavior unchanged; saliences
  unchanged; selection untouched; `ask()` path untouched; desktop
  lifecycle untouched; M14/M16 not started; no belief/episodic/mood
  redesign; no memory-database or selector work.

Tests/checks run:
- Snapshot `backups/aura_20260920_192029` verified 20/20 before editing.
- New focused suite green (4 honest en-route reds, all fixture/ordering
  errors in the suite itself, mechanism untouched).
- Full `python tests/run_all.py`: 78/78 green; isolation green; live clean.
- Safe stress: 61/61, 1 note. Viewer checks + selftest OK
  (40 frames + 17 tabs).
- No restore required.

Known limitations / outside the loop:
- Desktop master prompt assembly, episodic policy (M14), viewer
  selection coverage (M16), belief/lesson integration, mood-as-stance,
  volunteering beyond the delight garnish, full history synthesis.

Result:
- TARGET COGNITIVE LOOP PASS 2 COMPLETE — READY FOR REVIEW.

## 2026-09-21 - Phase 12 M14 Episodic Influence (M5 proven)

Date/time: 2026-09-21 +02:00

What changed:
- `aura_bridge.py`: added `m14_filter_recall` and bounded per-turn M14
  evidence. The existing topic/person-trace diary-recall reasoning path now
  requires visible, whole-token-relevant lived-event provenance and suppresses
  reply, query-relevant R3-conflicted, singular wrong-owner, and active-G7
  duplicate evidence before selection. Multi-hit provenance uses the canonical
  spoken episode content; selected-winner-only drive adaptation prevents
  suppressed or outbid recall from mutating state.
- `aura_bridge.py` + `ukft_roleplay.py`: only selected eligible episode
  provenance enters `cognitive_stance`, bounded as `past-interaction`; the
  roleplay prompt labels it event memory rather than objective proof and never
  rereads episodic storage.
- `aura_bridge.py` + `ukft_people.py`: closed the people-winner bypass by
  removing raw episodic traces/count reads from people answers; people records
  and G7 thread context remain.
- Final hardening narrowed prospective-modal exemption to a modal directly
  governing `I`, so polite outer framing cannot admit another person's episode
  as the current speaker's past while `Should I ...?` remains prospective.
- Added shipping `tests/verify_m14_episodic_influence.py` and registered it in
  `tests/run_all.py`. Two M5 receipts prove relevant episode admission changes
  vault->reasoning and duplicate suppression guards reasoning->context.
- Added `AURA_PHASE12_M14_EPISODIC_INFLUENCE_REPORT.md`; updated current
  architecture, capability, roadmap, product, and test documents. M16 is now
  the first unfinished roadmap milestone.

Files changed:
- Runtime: `aura_bridge.py`, `ukft_people.py`, `ukft_roleplay.py`.
- Tests: `tests/verify_m14_episodic_influence.py`, `tests/run_all.py`.
- Docs: `AGENTS.md`, `SYSTEM_WHITEPAPER.md`,
  `AURA_CURRENT_CAPABILITIES.md`, `AURA_WANTED_FEATURES.md`,
  `GF_PRODUCT_SPEC.md`, `tests/README.md`,
  `AURA_PHASE12_M14_EPISODIC_INFLUENCE_REPORT.md`, `AURA_CHANGELOG.md`.

Intended behavioural effect:
- Relevant lived-event evidence may influence the existing reasoning bid;
  unsafe or redundant episode evidence cannot vote. The brain, not the mouth,
  owns the selected event provenance.

Behaviour intentionally preserved:
- No episode candidate, score/salience change, selector rewrite, storage
  rewrite, automatic truth correction, M16 work, or unrelated product change.
- M1/M2/M3/M4/M13, G7, Pass 1/1A, Target Loop Pass 2, tools, boundaries, and
  user isolation remain unchanged.

Tests/checks run:
- Backup `backups/aura_20260920_204645` verified before risky work.
- Focused M14 suite green in a declared temporary root.
- Full `python tests/run_all.py`: 79/79 green; isolation green; live clean.
- Safe stress: 61/61 green, 1 note.
- Viewer checks green; selftest rendered 40 frames + 17 tabs.
- No restore required.

Documentation check:
- Updated every current authoritative document whose M14 status or current
  frontier changed. Governance and boundary policy did not change, so
  `AURA_GOVERNANCE_PROPOSAL.md` and `gf_boundaries.md` were not modified.

Result:
- M14 EPISODIC INFLUENCE COMPLETE AND HARDENED — READY FOR REVIEW.

## 2026-09-21 - M16 Full-Route Observability

Date/time: 2026-09-21 +02:00

What changed:
- `aura_bridge.py` now records an inert same-turn `selection_receipt` containing
  already-computed M1/M2/M3/M4/M13/M14, branch, old-brain field, hearing, and
  selected-winner facts. It does not call observer code or alter selection.
- `observer_telemetry.py` adds the enforced DORMANT/RAN/OUTPUT PRODUCED/OUTPUT
  USED/INFLUENCED DECISION hierarchy and conservative `route_evidence()`
  classification. Influence requires an existing system-specific causal basis.
- `ukft_brain_api.py` instruments the real `BrainModule.roleplay()` route from
  input through winner, stance, mouth, writeback, final response, and completion
  with UUID-backed per-call turn IDs. Standing questions remain no-turn pure
  reads but now emit a complete lifecycle with no invented selector influence
  or writeback-change event.
  Observer disable is checked dynamically and skips classification as well as
  emission.
- `aura_synapse_view.py` consumes explicit M16 receipts, validates supported
  influence bases, renders route evidence, exports it, and groups complete turns
  by `(user_id, turn_id)` rather than turn ID alone. Human-summary wording can
  no longer manufacture a legacy/bypass classification.
- Added shipping `tests/verify_m16_full_route_observability.py`; hardened the
  observer contract and viewer suites; registered M16 before isolation in
  `tests/run_all.py`. The observer contract now invokes the mandatory sandbox
  guard and explicitly refuses non-test mode instead of swallowing a failed
  test-root check.
- Added `AURA_M16_FULL_ROUTE_OBSERVABILITY_REPORT.md`; updated current
  architecture, capability, roadmap, product, and test documents. Corrected the
  roadmap overstatement: Pass 1/1A, Pass 2, M14, and M16 are complete bounded
  milestones, while the full GF-to-old-brain target loop remains in progress.

Why it changed:
- The original Brain/GF audit found that normal Discord/GF `roleplay()` turns
  lacked an observer lifecycle, so viewer/export could not truthfully show
  which systems influenced the selected answer.
- Existing telemetry could show activity but did not enforce the distinction
  between execution, production, use, and causal influence across the full
  route.

Files changed:
- Runtime: `aura_bridge.py`, `observer_telemetry.py`, `ukft_brain_api.py`,
  `aura_synapse_view.py`.
- Tests: `tests/verify_m16_full_route_observability.py`, `tests/run_all.py`,
  `tests/verify_observatory_contract.py`, `tests/verify_view.py`.
- Docs: `AGENTS.md`, `SYSTEM_WHITEPAPER.md`,
  `AURA_CURRENT_CAPABILITIES.md`, `AURA_WANTED_FEATURES.md`,
  `GF_PRODUCT_SPEC.md`, `tests/README.md`,
  `AURA_M16_FULL_ROUTE_OBSERVABILITY_REPORT.md`, `AURA_CHANGELOG.md`.
- `_review_packet/` (fresh disposable copies and manifest only).

Intended behavioural effect:
- Observer traces and viewer/export now tell the truth about the real roleplay
  route. They show lower evidence states when influence is not proven and
  identify the bounded systems that meet existing causal receipt conditions.

Behaviour intentionally preserved:
- No candidate, salience, selector, response, memory-policy, personality,
  rapport, boundary, or writeback mechanism changed.
- Observer remains observer-only, fail-open, and M5-proven non-causal. Turning
  it off leaves the winner and grounded response unchanged.
- M1/M2/M3/M4/M13/M14, Pass 1/1A, Target Loop Pass 2, tools, boundaries, and
  user partition behavior remain unchanged.

Tests/checks run:
- Pre-work snapshot `backups/aura_20260921_080450` verified 20/20.
- Focused M16 suite, observer contract, and viewer checks green in safe test
  workflows.
- Final `python tests/run_all.py`: 81/81 green; embedded isolation green; live
  state clean.
- Safe stress: 61/61 green, 1 existing note.
- Viewer selftest: 40 connectome frames + 17 tabs green.
- Standalone observer-contract execution outside test mode refuses before any
  trace write.
- Final independent implementation review found no issues and returned M16
  COMPLETE AND HARDENED - READY FOR REVIEW.
- Fresh review packet: 17 copied originals verified SHA-256-identical.
- A parallel full-suite/stress attempt transiently reported 79/80 without a
  retained failed-suite identity; the required dedicated full rerun was 80/80.
- No restore required.

Known limitations / unfinished work:
- M16 reports existing causal proof; selected people/belief/agenda/teach
  branches remain OUTPUT USED until dedicated M5 receipts exist.
- M1/M2 same-turn use does not by itself prove a counterfactual and is not
  promoted to influence.
- The existing filesystem-safe partition key can be lossy for punctuation-
  distinct raw IDs; no partition migration was attempted in this observer pass.
- Original audit findings 1, 2, 4, 8-10, 12, 14, and broader portions of 6,
  11, and 15 remain open. See the M16 report reconciliation table.

Documentation check:
- Updated every current authoritative document whose M16 status, observer
  contract, test workflow, product capability, or frontier changed.
- `AURA_GOVERNANCE_PROPOSAL.md` and `gf_boundaries.md` were checked and not
  modified because governance and product boundary policy did not change.
- The historical read-only integration audit was not rewritten; the M16 report
  records current disposition against its numbered findings.

Result:
- M16 FULL-ROUTE OBSERVABILITY COMPLETE AND HARDENED - READY FOR REVIEW.

## 2026-09-21 - Post-M16 Documentation Synchronization (docs only, M16 ACCEPTED)

Date/time: 2026-09-21 +02:00

What changed:
- Recorded M16 review acceptance across current documents: M16 is now
  COMPLETE / PROVEN / HARDENED / ACCEPTED (21 Sept 2026). No runtime, test,
  salience, selector, memory-policy, user-state, or live-state change.
- `AGENTS.md`: frontier now marks M16 accepted, keeps GF EXPERIENCE <->
  OLD BRAIN INTEGRATION IN PROGRESS, and adds the concise post-M16 order:
  finish narrow brain integration from still-open audit findings, then
  conversation normalization, controlled family beta, then product/scale.
  Future thin-client/encrypted-vault/server-brain is labeled target-only.
- `SYSTEM_WHITEPAPER.md`: marked M16 proven/hardened/accepted; added an
  explicit future-production-architecture target section (thin client,
  local encrypted vault/gatekeeper, private server brain, opaque storage
  adapter, per-user autobiography vs shared brain vs aggregated learning);
  replaced generic NEXT/LATER/FUTURE with the four-layer post-M16 roadmap
  while keeping the original audit as the controlling integration map.
- `AURA_CURRENT_CAPABILITIES.md`: rev 7 records M16 acceptance without
  changing capability mechanisms, restates the still-partial integration
  state with open vs closed findings, adds pack-knob and production
  architecture decisions, and adds an explicit NOT CURRENT CAPABILITIES
  section for normalization, family beta, and future deployment.
- `AURA_WANTED_FEATURES.md`: master roadmap now lists M16 accepted, keeps
  item 7 as the first unfinished integration objective, enumerates the
  remaining original-audit findings, and adds conversation normalization,
  controlled family-beta gates/mission, family-to-public product readiness,
  later continuity/public-beta work, future product architecture, and open
  decisions.
- `GF_PRODUCT_SPEC.md`: marked M16 accepted, labeled the loop partial,
  added conversation-normalization, controlled-family-beta, and future
  production-architecture sections, clarified family vs public gates, and
  added population-learning/privacy to open decisions.
- `AURA_BRAIN_GF_INTEGRATION_AUDIT.md`, `AURA_M16_FULL_ROUTE_OBSERVABILITY_REPORT.md`,
  `tests/README.md`, runtime code, tests, and live state unchanged.
- Added `AURA_POST_M16_DOC_SYNC_REPORT.md` for this pass.

Why it changed:
- M16 was reviewed and accepted, but current docs still carried READY FOR
  REVIEW frontier wording and jumped from bounded integration passes to
  generic deployment items. The roadmap needed the actual remaining audit
  work, conversation normalization as the next behavioral objective,
  controlled family beta as a testing stage, and future secure deployment
  clearly separated from current capability.

Files changed:
- Docs: `AGENTS.md`, `SYSTEM_WHITEPAPER.md`, `AURA_CURRENT_CAPABILITIES.md`,
  `AURA_WANTED_FEATURES.md`, `GF_PRODUCT_SPEC.md`,
  `AURA_POST_M16_DOC_SYNC_REPORT.md`, `AURA_CHANGELOG.md`.
- `_review_packet/` (fresh disposable copies and manifest only).

Intended behavioural effect:
- None. Documentation-only synchronization.

Behaviour intentionally preserved:
- Runtime code unchanged.
- Tests unchanged.
- Saliences/selectors/memory policy unchanged.
- User partitions unchanged.
- Live organism state unchanged.
- Original audit and accepted M16 implementation report unchanged.
- Governance/boundary policy unchanged.

Tests/checks run:
- No runtime/test suite run: documentation-only pass with no mechanism change.
- Read-back verification of all edited sections.
- Cross-document consistency search for M16 acceptance, loop-in-progress,
  audit control, normalization, family-beta, future architecture, and
  public-scale timing.
- Packet copy hash verification.

Known limitations / unfinished work:
- Remaining original-audit findings are unchanged and still require narrow
  M5-proven passes.
- Conversation normalization has objectives and failure classes, but no new
  mechanism or regression yet.
- Family beta has gates and mission, but no deployment or operating proof yet.
- Future thin-client/encrypted-vault/server-brain architecture is direction
  only.

Documentation check:
- `AURA_GOVERNANCE_PROPOSAL.md` and `gf_boundaries.md` checked; no policy
  change, so neither was modified.
- `tests/README.md` checked; test-contract wording did not need
  synchronization, so it was not modified.
- Historical/reference documents left historical.

Result:
- POST-M16 DOCUMENTATION SYNCHRONIZATION COMPLETE — READY FOR REVIEW.

## 2026-09-21 - Audit Finding #1 Empty-State Copyback (CLOSED)

Date/time: 2026-09-21 +02:00

What changed:
- `ukft_brain_api.py`: new `EMPTY_COPYBACK_FILES` allowlist
  (`pending_people.txt`, `pending_belief.txt`, `pending_action.txt`) and a
  reworked `from_root` sync-back. An existing root file cleared to empty by
  a pending lifecycle now syncs back as real state; a missing root file
  never deletes partition state; `field_state.txt` keeps its Pass-1A
  settle-owned legacy rule. `to_root`, stash/restore, selection, saliences,
  mouth, and write accounting untouched.
- Added shipping `tests/verify_finding01_empty_copyback.py` and registered
  it in `tests/run_all.py` before the isolation proof; indexed in
  `tests/README.md`.
- Added `AURA_GF_INTEGRATION_EMPTY_STATE_COPYBACK_REPORT.md`; marked
  finding #1 CLOSED in `AGENTS.md`, `SYSTEM_WHITEPAPER.md`,
  `AURA_CURRENT_CAPABILITIES.md`, and `AURA_WANTED_FEATURES.md`. The
  original audit was not rewritten. GF EXPERIENCE <-> OLD BRAIN
  INTEGRATION remains IN PROGRESS.

Why it changed:
- Original audit finding #1: legitimate non-empty -> empty transitions
  (confirm/cancel clearing a pending slot) were lost at sync-back because
  only `size > 0` root files copied back, so stale partition state could
  resurrect next turn. Reproduced pre-fix (3 failures) through real
  `BrainModule.ask()` cancel/confirm turns.

Files changed:
- Runtime: `ukft_brain_api.py` (sync contract only).
- Tests: `tests/verify_finding01_empty_copyback.py`, `tests/run_all.py`,
  `tests/README.md`.
- Docs: `AGENTS.md`, `SYSTEM_WHITEPAPER.md`,
  `AURA_CURRENT_CAPABILITIES.md`, `AURA_WANTED_FEATURES.md`,
  `AURA_GF_INTEGRATION_EMPTY_STATE_COPYBACK_REPORT.md`,
  `AURA_CHANGELOG.md`.
- `_review_packet/` (fresh disposable copies and manifest only).

Intended behavioural effect:
- Cleared pending slots stay cleared across API turns and fresh module
  instances; normal non-empty writes copy back as before.

Behaviour intentionally preserved:
- No candidate, salience, selector, M-gate, memory-policy, mouth, response,
  boundary, or product change. Sync runs after the response is built, so
  current-turn cognition is unaffected; only the next turn reads corrected
  state. Pass-1A field restore/settle/empty behavior identical in `ask()`
  and `roleplay()`. Finding #2, transactional writeback, `memory_writes`
  journaling, and all other findings untouched.

Tests/checks run:
- Pre-work snapshot `backups/aura_20260921_104018` verified 20/20.
- Focused suite pre-fix: 3 failures (stale pending kept + resurrection).
- Focused suite post-fix: ALL PASSED (cancel/confirm/belief/tool clears,
  no-resurrection, missing-root control, cross-user isolation, real 0.99
  selector receipt + source pin, temp-root and live-hash pins).
- Two independent challenge reviews: first PASS; second FAIL with two test-
  validity findings (vacuous salience assert, single-slot proof) — both
  resolved and re-accepted (RESOLUTIONS ACCEPTED).
- Full `python tests/run_all.py`: 81/81 green; embedded isolation green;
  live state clean.
- Safe stress: 61/61 green, 1 existing note.
- Viewer checks green in pristine sandbox; selftest 40 frames + 17 tabs.
- No restore required.

Known limitations / unfinished work:
- Torn non-empty writes are not integrity-checked (pre-existing, needs
  atomic-write hardening later, not this finding).
- `pfc_focus.txt` / `aura_thoughts.txt` remain shared-root channels outside
  the partition swap (pre-existing, out of scope).
- Findings #2, #4, #6, #8-#12, #14 and bounded #6/#11/#15 remain open.

Documentation check:
- `AURA_GOVERNANCE_PROPOSAL.md`, `gf_boundaries.md`, and `GF_PRODUCT_SPEC.md`
  checked; no policy/product change, so none modified.
- Historical audit and M16 report left unchanged.

Result:
- AUDIT FINDING #1 EMPTY-STATE COPYBACK — READY FOR REVIEW.

## 2026-09-21 - Audit Finding #2 Partition Ownership (CLOSED)

Date/time: 2026-09-21 +02:00

What changed:
- `ukft_brain_api.py`: `_get_ego(user_id)` now runs AFTER the
  `to_root` partition swap under the ask lock in BOTH `ask()` and
  `roleplay()`, so no ego is ever born ingesting a foreign pre-swap root
  vault. A swap/ego-birth failure before cognition restores the pre-turn
  root and propagates. `_create_ego_for_user` docstring corrected (eager
  vault load stated; the old lazy-load claim was false).
- Added shipping `tests/verify_finding02_partition_ownership.py` and
  registered it in `tests/run_all.py` before the isolation proof; indexed
  in `tests/README.md`.
- Added `AURA_GF_INTEGRATION_PARTITION_OWNERSHIP_REPORT.md`; marked
  finding #2 CLOSED in `AGENTS.md`, `SYSTEM_WHITEPAPER.md`,
  `AURA_CURRENT_CAPABILITIES.md`, and `AURA_WANTED_FEATURES.md`. The
  original audit was not rewritten. GF EXPERIENCE <-> OLD BRAIN
  INTEGRATION remains IN PROGRESS. Finding #1 stays CLOSED.

Why it changed:
- Original audit finding #2: ego creation preceded the partition swap
  while `PatternEngine` eagerly loads the current root vault and later
  reloads are mtime-gated, so adverse mtime ordering let pre-swap root
  anchors survive. Reproduced pre-fix in pristine sandboxes (8 failures:
  hostile sentinel quoted on newer/equal mtime, old-seed, and full A/B/A
  contamination) through the real API route.

Files changed:
- Runtime: `ukft_brain_api.py` (ordering + early-failure guards only).
- Tests: `tests/verify_finding02_partition_ownership.py`, `tests/run_all.py`,
  `tests/README.md`.
- Docs: `AGENTS.md`, `SYSTEM_WHITEPAPER.md`,
  `AURA_CURRENT_CAPABILITIES.md`, `AURA_WANTED_FEATURES.md`,
  `AURA_GF_INTEGRATION_PARTITION_OWNERSHIP_REPORT.md`,
  `AURA_CHANGELOG.md`.
- `_review_packet/` (fresh disposable copies and manifest only).

Intended behavioural effect:
- The requested user's partition vault is authoritative from ego birth;
  hostile pre-swap root content can no longer own any API turn under any
  mtime ordering.

Behaviour intentionally preserved:
- No candidate, salience, selector, M-gate, memory-policy, mouth, response,
  boundary, or product change. G7 reload, Pass-1A field lifecycle,
  finding-#1 copyback, M16 receipts, and stash/restore semantics unchanged.
  Finding #4 and all later seams untouched.

Tests/checks run:
- Pre-work snapshot `backups/aura_20260921_104018` verified 20/20 (taken
  for finding #1; no state risk introduced since).
- Focused suite pre-fix (hardened profile-persisting setup, pristine):
  8 failures with the hostile-sentinel signature.
- Focused suite post-fix (pristine): ALL PASSED (adverse/equal/normal
  mtime, old-seed ownership, cached A/B/A, roleplay parity, byte-exact
  root restore, source-order invariant, temp-root and live-hash pins).
- Two independent challenge reviews (ownership/cache + lifecycle/
  regression): both CHALLENGE PASS; one adopted hardening (guard also
  covers `to_root`); follow-up confirmation on the test-setup reseed
  discovery: PASS stands.
- Full `python tests/run_all.py`: 82/82 green; embedded isolation green;
  live state clean.
- Safe stress: 61/61 green, 1 existing note.
- Viewer checks green (pristine); selftest 40 frames + 17 tabs.
- No restore required.

Known limitations / unfinished work:
- The mtime gate survives for same-user shapes (equal-mtime content swaps,
  deleted-vault staleness); cross-user pre-swap ingestion is closed.
- First-create `_save_profile` silently misses a missing user dir (fresh
  modules reseed); production heals at end-of-turn save. Logged as a
  discovered profile-durability issue for its own pass — not fixed here.
- Findings #4, #6, #8-#12, #14 and bounded #6/#11/#15 remain open.

Documentation check:
- `AURA_GOVERNANCE_PROPOSAL.md`, `gf_boundaries.md`, and `GF_PRODUCT_SPEC.md`
  checked; no policy/product change, so none modified.
- Historical audit and prior pass reports left unchanged.

Result:
- AUDIT FINDING #2 PARTITION OWNERSHIP — READY FOR REVIEW.

## 2026-09-21 — Audit Finding #4 Transactional Writeback

Date/time: 2026-09-21

What changed:
- Candidate-owned detectors (people, agenda, belief, teach) now propose
  against non-persisting staged models (`persist=False` on `PeopleModel`,
  `BeliefStore`, `AgendaModel`, `LessonLedger`: identical return contracts,
  zero disk trace). Detection never touches disk.
- After basal selection, `_commit_decision_effects` (plus `_commit_people`
  / `_commit_teach` helpers) replays only legitimate effects exactly once
  on fresh persisting models: winner-owned commits plus turn-owned mention
  sightings and speaker-binding init. Each winner block is fail-open, so a
  persist failure degrades instead of killing the turn.
- Removed the interim byte-snapshot/rollback machinery (`_f4_snapshot`,
  `_f4_restore`, `_F4_SNAPSHOT_FILES`): executed pre-fix evidence proved
  restore clobbers legitimate mid-window third-party writes, raw `open()`
  bypasses bus locks and the sandbox guard, and rollback swallows OSError
  silently.
- Ownership now explicit: knowledge-gap recording is turn-owned (a function
  of the executed reasoning plan + input — "logged either way" per the code
  comment; winner-independent inputs; no selection consumer), so it stays
  on its existing path, untouched by the transaction.
- Reverted a peripheral Finding-#4-era `ukft_register.py` change
  (`last_picked` / `record=False`): dead code (never passed, never read),
  register outside the finding's enumerated scope, mouth-adjacent redesign
  avoided.
- New receipt `tests/verify_finding04_transactional_writeback.py`,
  registered in `tests/run_all.py` and `tests/README.md`.

Why it changed:
- `AURA_BRAIN_GF_INTEGRATION_AUDIT.md` finding #4: people, agenda, beliefs,
  lessons, and gaps could write before winner selection; a losing detector
  could leave state.

Files touched:
- `aura_bridge.py`
- `ukft_people.py`
- `ukft_belief.py`
- `ukft_agenda.py`
- `ukft_teach.py`
- `tests/verify_finding04_transactional_writeback.py`
- `tests/run_all.py`
- `tests/README.md`
- `AGENTS.md`
- `AURA_CURRENT_CAPABILITIES.md`
- `AURA_WANTED_FEATURES.md`
- `SYSTEM_WHITEPAPER.md`
- `AURA_CHANGELOG.md`
- `AURA_GF_INTEGRATION_TRANSACTIONAL_WRITEBACK_REPORT.md` (new)
- `_review_packet/` (fresh disposable copies and manifest only)

Intended behavioural effect:
- Losing candidate-owned effects leave their persistent stores
  byte-identical; selected effects commit exactly once; turn-owned
  experience writeback (mentions, gaps, sleep-wake, G7/episodes/rapport/
  hearing/field) intact; controlled failure before commit strands nothing;
  commit-phase persist failure degrades fail-open with the decision intact.

Behaviour intentionally preserved:
- No candidate, salience, selector, M-gate, memory-policy, mouth, response,
  boundary, personality, or product change. Findings #1 and #2 closed-state
  intact; Pass 1/1A, G7, M1-M4, M13, M14, M16 intact. No later-audit redesign
  (finding #6 shadow fields, #10 `memory_writes`, and all later seams
  untouched). Register opener behavior byte-identical (peripheral change
  reverted).

Tests/checks run:
- Pre-work snapshot `backups/aura_20260921_124318` verified 20/20.
- Pre-fix evidence probe (exact `_f4_snapshot`/`_f4_restore` paths):
  restore clobbers a legitimate mid-window bus-locked write (sentinel gone,
  file byte-identical to pre-turn); raw `open()` bypasses bus locks/guard;
  OSError swallowed silently.
- New focused suite (pristine): ALL PASSED — 7 losing arms byte-identical
  (people commit/stage, agenda open/close, belief hold, teach noted/held
  with both tie directions), 4 winner positive controls, exactly-once
  singularity (people/agenda/belief records, lesson dedupe True-then-False),
  same-turn rename visibility, turn-owned gap recorded on reasoning runs and
  absent on executive turns, pre-commit exception propagation with
  byte-identical stores, commit-phase failure fail-open with decision
  intact, persist=False unit contract on all four models, ask() parity with
  cross-user partition isolation, roleplay parity (mouth-down), structural
  propose<select<commit order pin, temp-root and live-hash pins.
- Reviewer A (phantom/double-commit/exception/stale-state, executable):
  ALL PASSED; one valid finding adopted (commit-phase failure killed the
  turn — fixed with per-subsystem fail-open guards, re-probed green,
  folded into the suite as ARM 12b).
- Reviewer B (lifecycle/regression, 21 focused suites): ALL PASSED
  (finding04 + C2/C6/C10/C8/I2/M4/M3/G7/pass1a/finding01/finding02/R6/M5/
  M13/M14/M16/pass2/F1/C3/C5).
- Full `python tests/run_all.py`: 83/83 green; embedded isolation green;
  live state clean.
- Safe stress: 61/61 green, 1 existing note.
- Viewer checks green (sanctioned invocation); selftest 40 frames + 17 tabs.
- Fresh snapshot `backups/aura_20260921_204959` verified 20/20. No restore
  required.

Known limitations / unfinished work:
- Register opener banking on proof-composing losing turns remains as before
  (voice-variety texture, no selection/memory/truth consumer; wiring it into
  the transaction would be mouth-adjacent redesign — explicitly out of scope).
- Findings #6, #8-#12, #14 and bounded #6/#11/#15 remain open.

Documentation check:
- `AGENTS.md`, `AURA_CURRENT_CAPABILITIES.md`, `AURA_WANTED_FEATURES.md`,
  `SYSTEM_WHITEPAPER.md`, `tests/README.md` updated in the same pass.
- `AURA_GOVERNANCE_PROPOSAL.md`, `gf_boundaries.md`, and `GF_PRODUCT_SPEC.md`
  checked; no policy/product change, so none modified.
- Original `AURA_BRAIN_GF_INTEGRATION_AUDIT.md` untouched (controlling
  historical audit); historical pass reports left unchanged.

Result:
- AUDIT FINDING #4 TRANSACTIONAL WRITEBACK — READY FOR REVIEW.

## 2026-09-21 — Audit Finding #6 Shadow Context (CLOSED)

Date/time: 2026-09-21
Suite pass: tests/verify_finding06_shadow_context.py (new); full run_all
  84/84 green; stress 61/61 green; M14 causal + production-isolation green.

What changed:
- Closed original audit Finding #6 by classifying every context-bundle
  field at the producer→reader→selection-use seam:
  - CAUSAL: `current_user` — feeds M4 person_bound/ownership, M3-10B
    eligibility, M14 ownership; no new influence, pinned at this seam.
  - DUPLICATE (detectors/recall/policy/stance read authoritative stores
    directly, not the bundle): `time_window`, `people`, `architect`,
    `recent`, `facts`, `thread`, `gaps`, `drives`, `threads`.
  - DEAD-SHADOW (zero production readers): `day`, `session`,
    `open_threads` — RETIRED from `assemble()` in `ukft_context.py`.
- Closed the genuine cognitive gap the audit flagged: person-fact
  questions about known people (e.g. "what does sarah like") fell dark
  while the answer sat in assembled facts. Extended `_people_question` /
  who-is pattern matching to cover what-does / possessive / where /
  how-old frames via `_strip_fact_verb`, routing through the existing
  known-person gate into the existing who-is speech. No salience,
  candidate, mouth, or store change — smallest correct seam.
- `verify_c5.py` updated to match retired keys (contract now asserts
  the live bundle keys, not the defunct ones).
- `tests/README.md` updated with the Finding #6 suite description.

Why it changed:
- The audit found the assembled bundle was mostly shadow, but a real
  selection path (person-fact recall) was genuinely broken. Per Law 7
  (fix the mechanism, not the sentence), that mechanism gap — not the
  shadow fields themselves — was the actionable defect. The shadow
  fields are now proven inert (hostile-bundle perturbation identity:
  winner + response byte-identical, no leakage), so they are documented
  as duplicate/sidecar and no longer a latent hazard.

Proof:
- Hostile-bundle perturbation identity: winner p3 identical to the
  clean turn; response byte-identical; no mallory leakage.
- current_user linkage pin: M4 person_bound tracks the bundle field
  (clean=True, broken=False when field cleared).
- Person-fact M5 receipt (the failure reproduction): known fact flips
  dark→people and the held fact is spoken; negative controls pass
  (unknown person, non-person, content-free, and fact-absent cases).
- Bundle-reader structural pin: the only production bundle read feeding
  selection is `_bundle.get("current_user")`.
- ask()/roleplay() parity with cross-user partition isolation.
- Mouth/register boundary pin: opener register churn never moves the
  winner.
- Temp-root containment + live-state hash pins; all writes remain
  inside the sandbox.

Result:
- AUDIT FINDING #6 SHADOW CONTEXT — CLOSED, READY FOR REVIEW.

## 2026-09-21 — Post-Finding-#6 Documentation Synchronization

Date/time: 2026-09-21
Docs only, no runtime/test/state change.

What changed:
- `AGENTS.md`: frontier list gains "Audit finding #6 (shadow context)
  CLOSED" and points to the new suite; confirmed no other change needed.
- `AURA_CURRENT_CAPABILITIES.md`: added Finding #6 to the connection
  matrix (shadow bundle fields → proven duplicate/inert; current_user →
  proven causal via M4/M14 receipts).
- `SYSTEM_WHITEPAPER.md`: added a one-line entry under the context
  bundle table noting retired keys and the causal field, with receipt
  pointers.
- `tests/README.md`: Finding #6 suite description added.
- Original `AURA_BRAIN_GF_INTEGRATION_AUDIT.md` untouched (controlling
  historical audit); historical pass reports left unchanged.

Why it changed:
- The bundle-field determination and the person-fact seam closure are
  current product-state facts a new agent must understand immediately.

Result:
- Finding #6 close reflected in all current authoritative documents.

## 2026-09-22 — Audit Finding #6 Re-Review Corrections (three blockers)

Date/time: 2026-09-22
Docs + narrow mechanism truthfulness; classification, dead-key
retirement, Finding #4, and all earlier closed findings untouched.
Earlier Finding-#6 entries stand; this appends corrections only.

What changed:
- Blocker 1 (roleplay parity unproven): added ARM 9b to
  `tests/verify_finding06_shadow_context.py` — a real
  `BrainModule.roleplay()` proof for the person-fact path and
  cross-user isolation using the sanctioned mouth-down pattern
  (`roleplay_fn` down → engine-template fallback, finding #2 ARM 6).
  Both routes now proven; the report's parity claim is now supported.
- Blocker 2 (ARM 5 functional, not causal): rebuilt ARM 5 as a true
  identical-state/input controlled perturbation at the new seam —
  control bypasses `_match_person_fact_frame` (falls to `dark`),
  treatment runs it (`people` + held fact spoken). Store
  snapshot/restore, dialogue/field baseline reset, presence-gate source
  pin, and an M14-shaped `f6_person_fact_routing` receipt recording
  `influenced_decision: True`. No salience, candidate, store, or
  unrelated-state change between arms.
- Blocker 3 (sibling frames could answer unrelated facts): frames now
  return a read-only `who_is_attr` action (no commit path, same
  presence bid, self-record ensure preserved) carrying attribute
  keywords; `PeopleModel.match_attr_fact` (whole-word narrow stem in
  `ukft_people.py`) answers only the requested held fact and honestly
  declines otherwise ("I don't have that noted for X — my notes: …" /
  "no notes yet"). Positive-content and missing-attribute negative
  controls added (including like/live isolation and factless decline).
- `AURA_GF_INTEGRATION_SHADOW_CONTEXT_REPORT.md` corrected (section 7
  records the three blockers and resolutions; earlier sections updated
  to the `who_is_attr` mechanism).

Why it changed:
- External review found the parity claim unsupported, the M5 receipt
  non-causal, and the sibling frames potentially untruthful. Each is
  now proven at the mechanism level per M5 law.

Proof:
- Finding-#6 suite: all checks pass (true M5 dark→people flip,
  roleplay ask-parity on both routes with isolation, truthful
  positives + honest declines).
- Full `tests/run_all.py` 84/84 green; stress 61/61 green; C2/C5/G7/
  M4/M14/finding-#2/finding-#4/G3-roleplay re-run green; viewer
  selftest OK; live state clean.
- Original `AURA_BRAIN_GF_INTEGRATION_AUDIT.md` untouched.

Result:
- AUDIT FINDING #6 SHADOW CONTEXT — READY FOR RE-REVIEW.

## 2026-09-22 — Audit Finding #8 Lesson Correction (CLOSED)

Date/time: 2026-09-22
Suite pass: tests/verify_finding08_lessons_correction.py (new, 50
checks); full run_all 85/85 green (was 84); stress 61/61 green;
C2/C5/C8/C10/G1/G3/M3/M4/M14/finding-#2/finding-#4/finding-#6 re-run
green; viewer selftest OK; live state clean.

What changed:
- Closed original audit Finding #8 by determining the truthful
  architectural role of correction/lesson state and fixing three
  narrow seams — no new truth store, no salience change:
  - The ledger is an AUDIT/HISTORY + REVIEW source, not a second
    truth source. Corrected truth lives only in existing
    authoritative stores (provisional beliefs, person facts by
    addition). Classification per correction class: bare BANKED-ONLY,
    parseable factual CORRECTED-TRUTH (provisional belief), person
    counterclaim PERSON FACT, vs-proof counterclaim PROVISIONAL via
    contest (C10 contract intact), unparseable BANKED-ONLY, review
    REVIEW-ONLY.
  - `aura_bridge.py` `_reasoning_answer`: when graph files are absent
    (fresh sandboxes AND fresh API partitions), the turn now plans
    the question (pure parsing, no files) and lets a held
    correction-belief answer VERIFY provisionally with the standard
    belief-provisional M3 receipt; otherwise associative behaviour
    is byte-identical to before. Pre-fix failure F1 (held belief,
    later VERIFY still dark) now answers.
  - `ukft_people.py` `match_attr_fact`: best-match scoring
    (distinct keyword hits, then earliest position, then most
    recent) replaces first-match — an accepted person-fact
    correction surfaces in later attribute answers (pre-fix failure
    F2 fixed) while attribute-led predicates beat incidental
    mentions regardless of order; pure ties stay recency-biased by
    design; nothing is erased, `describe` still lists all.
  - `aura_bridge.py` teach_noted action is now
    ("teach_noted", text, fact|None): a passed-on person fact is
    acknowledged exactly ("Noted — Sarah likes tea."); banked-only
    text says exactly that ("banked as a lesson, but I can't answer
    from it yet...") — pre-fix failure F3 (overstated "I'll keep
    that in mind") fixed at the mechanism level per action kind.
- Reviewer A (2 valid non-blockers) resolved: attribute-led scoring
  above + noted-repeat boundedness pinned (identical free-text
  repeats grow at most one extra row from live G7 topic variance,
  stable after the second, answers unchanged). Reviewer B clean.
- `tests/README.md` (+ root mirror) gained the Finding #8 suite
  description.

Why it changed:
- The audit found lesson text WRITEBACK-ONLY with overstated
  acknowledgements and no general future-answer influence. The live
  trace proved three concrete failures (F1 graphless belief silence,
  F2 stale-fact-wins, F3 overstatement) with the truth already
  banked in authoritative stores but unreachable or misdescribed.
  Each is now proven at the M5 level; stale lessons are proven
  unable to hijack answers (structural confinement + hostile-lesson
  identity); Finding-#4 semantics preserved (losing teach commits
  nothing, single commit site, exactly-once + idempotent repeats).

Proof:
- Two TRUE M5 receipts (dark→reasoning belief consult;
  stale→corrected person answer) under identical-state/input
  controlled perturbation; pre-fix behavior re-lived in the control
  arms every run.
- Contested counterclaims still route to confirm/cancel with zero
  pre-confirm writes (false-authority guard); proof never overridden
  (belief answers only when the graph is silent).
- Fresh-instance persistence, ask/roleplay parity (mouth-down
  pattern), cross-user isolation, review truth, temp-root
  containment, live-hash pins.
- Original `AURA_BRAIN_GF_INTEGRATION_AUDIT.md` untouched.

Result:
- AUDIT FINDING #8 LESSON CORRECTION — READY FOR REVIEW.

## 2026-09-22 — Audit Finding #9 Trust/Importance (CLOSED)

Date/time: 2026-09-22
Suite pass: tests/verify_finding09_trust_importance.py (new, 46
checks); full run_all 86/86 green (was 85); stress 61/61 green;
C2/C3/C10/G-series/M3/M4/M14/finding-#2/finding-#4/finding-#6/
finding-#8 re-run green; viewer selftest OK; live state clean.
NO PRODUCTION CODE CHANGED — audit-only close.

What changed (tests + docs only):
- Audited BeliefStore trust and PeopleModel importance end to end
  (event → writer → persisted value → decay/update → readers →
  seams → effects) and searched comments, tests, current docs, and
  runtime contracts for intended behavior. Determination: BOTH are
  ADVISORY-HISTORY — computed, persisted, test-readable, with zero
  production behavioral readers.
  - Trust is written only by confirm/cancel contest resolution;
    deference outcomes already live in belief conf/status/prior,
    which the live seams consume; the score is bookkeeping of the
    same event. No speech, contract, or selection path promises
    trust sensitivity, so nothing is broken for lack of readers.
  - Importance is written on commit/mention (+0.1, cap 2.0),
    lazily decayed (30-day half-life, floor 0.2, never deletes);
    the one ranking seam (relation-reference disambiguation) is
    owned by mentions + first_met. Endorsing importance's decay
    semantics in ranking would invent undecided product policy.
  - Hypotheses H1 (trust breaks provisional ties) and H2
    (importance disambiguates people) REJECTED from the
    repository: match() is relation-preferred else max-conf,
    match_words is coverage-then-conf, who_is is exact — no
    same-decision case exists where any contract wants these
    scores to decide.
- New receipt `tests/verify_finding09_trust_importance.py`:
  writer/source pins for both metrics (defaults, bands, deltas,
  keys, caps, floors, half-life); repo-wide structural non-reader
  pins (`trust_of`, `.trust`, SCORE-parse, `importance`/`IMPORT`
  confined to owner stores; rapport-trust separation proven);
  hostile-perturbation identity on every live seam (floored/capped
  trust across VERIFY/contest/confirm; swapped importance across
  who-is/about/attr/relation-ref/current-person — winners and
  responses byte-identical); ambiguity rejections; strong-proof
  non-override under maxed trust; Finding-#8 regression;
  decay boundaries (half, floor, no disappearance, floored person
  still answers); Finding-#4 losing byte-identity; fresh-instance
  persistence; ask/roleplay parity with cross-user isolation;
  temp-root and live-hash pins.
- Adversarial review: A found 3 valid suite-hardening issues
  (structural scan coverage/quote forms; people-isolation string;
  vacuous trust-row pin) — all resolved, no production change.
  B clean.
- `tests/README.md` (+ root mirror) gained the suite description.

Why it changed:
- The audit found both metrics computed/persisted without
  behavioral readers. Forcing them into cognition would invent
  salience multipliers, thresholds, and ranking policy the project
  never decided — explicitly forbidden. Retaining writeback-only
  with proven non-causality is the sanctioned alternative
  (AURA_WANTED_FEATURES), and is what this pass does.

Proof:
- Zero production readers proven by exhaustive repo-wide scans
  (any future reader breaks the pins loudly) plus hostile
  extremes leaving every live decision byte-identical.
- No thresholds given behavioral meaning: suite pins stored
  mechanics only.
- Original `AURA_BRAIN_GF_INTEGRATION_AUDIT.md` untouched.

Result:
- AUDIT FINDING #9 TRUST IMPORTANCE — READY FOR REVIEW.

## 2026-09-22 — Audit Finding #9 Re-Review Hardening (no production change)

Date/time: 2026-09-22
Reviewer found one proof-scope defect and one documentation
precision defect; classification unchanged (ADVISORY-HISTORY).

What changed (tests + report wording only):
- `tests/verify_finding09_trust_importance.py`: the structural
  non-reader pins now walk the full supported runtime source tree
  recursively (root production modules plus legacy tree; tests,
  review packets, archive/reference, partitions, traces, backups,
  corpora, and packs explicitly excluded) instead of root-level
  files only. Added an alias negative control under hostile
  importance at record and turn level ("Tell me about Sally" →
  Sarah, byte-identical under swapped extremes).
- `AURA_GF_INTEGRATION_TRUST_IMPORTANCE_REPORT.md`: corrected
  "who_is is exact" to the actual finding (deterministic
  canonical/alias/display lookup, no importance ranking) and
  recorded this hardening as section 7.

Proof: suite 50/50 green (was 46); full gates re-run below.
Original `AURA_BRAIN_GF_INTEGRATION_AUDIT.md` untouched.

Result:
- AUDIT FINDING #9 TRUST IMPORTANCE — READY FOR RE-REVIEW.

## 2026-09-22 — Audit Finding #10 Memory Writes Journal (CLOSED)

Date/time: 2026-09-22
Suite pass: tests/verify_finding10_memory_writes_journal.py (new, 75
checks, 27 ARMs); full run_all 87/87 green (was 86); stress 61/61
green;
C2/G3/G6/C10/M16/F1/F2/F4/F6/F8/F9 re-run green; viewer selftest OK;
live state clean. Reporting + persisted profile-accounting
behavior changed; cognition/selection/speech unchanged (observer
remains observer-only; rapport canonical depth unchanged except
for the bounded fallback effect of corrected counters, pinned
below).

What changed:
- Replaced size-growth `_extract_memory_writes()` with
  before/after partition-bytes diff (`_snapshot_partition_files` +
  `_diff_partition_files` + `_semantic_kinds`): clears,
  shrinkage, equal-size replacements, and content identity now
  correctly reported. Receipt shape: `file`, `type`, `op` (created/
  modified/cleared/deleted), `kind` (semantic subtype), `count`.
  Misleading `bytes_added` removed.
- Semantic kinds for every USER_STATE_FILES: person_new/fact/
  fact_removed/alias/relation/display/warm; thread_opened/updated/
  closed/evicted; belief_new/contest/trust; lesson_new; vault_anchor;
  person/belief/action_pending; episode/working_memory/identity/
  self_state/rapport/field_state with kind=None.
- Truthful counters via shared `_apply_write_counters()` in both
  ask() and roleplay(): facts_learned (vault anchors + person facts
  only), threads_shared (opened), threads_closed (open→closed),
  lessons_banked (new triples). Mention/alias/relation/display/trust
  moves nothing. Roleplay gains threads_closed parity.
- Observer gating: `writeback_changed` emits only when
  `memory_writes` non-empty — no false "changed" claims. Observer
  remains observer-only.
- Finding-#4 preserved: staged persist=False proposals; losing
  candidates zero receipt + byte identity; winner exactly-once;
  turn-owned writeback intact.
- Finding-#1 preserved: allowlisted pending clear reports cleared;
  missing root never deletes partition state; empty manifold
  handled.
- Finding-#8 regression: correction→VERIFY answers unchanged.
- Finding-#9 regression: trust-only moves remain advisory.
- Observer gating: `writeback_changed` only on non-empty writes.
- New receipt `tests/verify_finding10_memory_writes_journal.py`
  (29 ARMs, 86 checks): old-impl removal pins, F1/F2/F3 proofs,
  growth/identical/mtime/multi-mutation/transient/failed-persist
  controls, Finding-#4 losing/winning, turn-owned, Finding-#1/8/9
  regressions, negative controls, thread open/update/close, lesson
  new/dedupe, accumulated truth, persistence, standing, ask/roleplay
  parity, final-voice writeback, observer truth, cross-user
  isolation, shape/compat pins.
- `tests/verify_finding09_trust_importance.py` SCORE exception
  for journal's read-only parser (pinned to its function).
- `tests/README.md` / root `README.md` suite description.

Why it changed:
- The audit found size-growth heuristic missed clears, shrinkage,
  equal-size replacements. Derived profile counters inherited the
  weakness. The fix replaces the heuristic with a bounded per-turn
  receipt of durable partition mutations — no new store, no
  cognition input, no salience change.

Proof:
- F1 equal-size replacement (unit + real confirm route) caught.
- F2 shrink (cap-eviction add+evict) caught.
- F3 allowlisted clear caught; missing-vs-empty preserved.
- Growth/identical/mtime controls; unit op boundaries; multi-mutation;
  transient exclusion; failed-persist exclusion; Finding-#4
  losing/winning; turn-owned; Finding-#1/8/9 regressions; negative
  controls; thread/lesson/accumulated truth; persistence; standing;
  ask/roleplay parity; final-voice writeback; observer truth;
  cross-user isolation; shape/compat pins.
- 87/87 green; stress 61/61; viewer selftest OK; live state clean.

Result:
- AUDIT FINDING #10 MEMORY WRITES JOURNAL — READY FOR REVIEW.

## 2026-09-22 — Audit Finding #10 Re-Review Hardening (reporting + counters preserved)

Date/time: 2026-09-22
External review found five reporting/proof blockers; byte-diff design accepted, re-review corrects reporting/accounting only.

What changed (reporting/accounting + tests + docs, cognition/selection/speech unchanged):
- BLOCKER A (turn-scoped concurrency): `_snapshot_partition_files` + after-snapshot + `_apply_write_counters` + profile save are now atomic inside `_ask_lock` for both `ask()` and `roleplay()`; receipt/counters belong exactly to each serialized turn. Deterministic same-user concurrency regression added (barrier-forced interleaving that old snapshot-outside-lock would misattribute).
- BLOCKER B (person fact identity): `FACT:` identity is now `(person_key, predicate)` so identical predicates under Sarah vs Maya do not collapse; alias/relation similarly person-scoped. Real-route + pure-diff controls added.
- BLOCKER C (Finding #9 topology): docs now state zero production BEHAVIORAL readers with one bounded reporting/accounting reader; `verify_finding09` narrow exception pinned to `_trust_rows`, included in this packet.
- BLOCKER D (packet hashes): `_review_packet/` rebuilt from scratch; every copy hashed against its live original at pack time; manifest count/hash-row count/identical statement now agree (18 files, 18 rows).
- BLOCKER E (proof quality): ARM count corrected to 28 (was 27, originally 26), vacuous `True` removed and replaced with real correction-turn evidence, alias-only control added, duplicate ARM 8 / missing ARM 24 fixed, redundant OR hardened with instrumentation.
- BLOCKER F (benign-rewrite contract): `_benign_rewrite()` wired at the semantic seam (TS-only re-holds, N-only bumps yield no receipt); hostile tests added.
- PUBLIC RECEIPT SEMANTICS: `type` documented as legacy compatibility/category, `kind` as authoritative semantic event; pinned.
- DOCUMENTATION TRUTH: "no production behavior changed" replaced with "reporting + persisted profile-accounting behavior changed; cognition/selection/speech unchanged (bounded fallback effect of corrected counters pinned)".

Proof: F10 suite 81/81 green (was 75, originally 64), F9 suite 50/50 green, run_all 87/87, stress 61/61, viewer selftest OK, live state clean. Original audit untouched.

Result:
- AUDIT FINDING #10 MEMORY WRITES JOURNAL — READY FOR FINAL RE-REVIEW.

## 2026-09-22 — Audit Finding #10 Final Re-Review (reporting + counters + observer identity)

Date/time: 2026-09-22
External final re-review accepted core corrections; re-review corrects remaining document truth, counter→depth boundary, journal window, observer identity, and proof hardening.

What changed (reporting/accounting + tests + docs, cognition/selection/speech unchanged):
- Current-document truth: `AURA_CURRENT_CAPABILITIES.md` Finding #9 now zero BEHAVIORAL readers + bounded reporting reader, Finding #10 now 28 ARMs/80 checks with atomic same-user, owner-aware, benign, authoritative kind; `SYSTEM_WHITEPAPER.md` Finding #10 now reports + profile-accounting changed with bounded fallback; `tests/README.md` + root mirror now describe current F9 exception and F10 hardening coverage (atomic, owner-aware, benign, same-user concurrency); `AURA_GF_INTEGRATION_MEMORY_WRITES_REPORT.md` now 28/80 and lists all current changed files, finishing as FINAL RE-REVIEW.
- Counter→depth boundary: explicit tests prove rapport history canonical (hostile counter mutation does not move stage) and legacy fallback moves with counters when no history; rapport thresholds/policy unchanged.
- Journal window: `_compute_depth_stage()` legacy bootstrap (seed_from_contact) happens before the Finding-#10 before-snapshot — deliberately outside the turn's memory_writes transaction; regression proves no false coverage.
- Same-user ask() observer identity: each ask() invocation now gets one stable local turn ID (`turn_count+1-UUID`) for its entire lifecycle (start/input/writeback/final/complete), analogous to roleplay; deterministic same-user concurrent observer regression added.
- Same-user receipt proof hardened: redundant OR replaced with honest instrumentation (each turn exactly one new person_fact, distinct predicates, counters sum, partition holds both once).
- ARM headings renumbered sequentially (duplicate ARM 8 / missing ARM 24 fixed); check count dynamic.

Proof: F10 suite 81/81 green, F9 suite 50/50 green, run_all 87/87, stress 61/61, M16/observer and rapport/G8 preservation, Findings #1/#2/#4/#6/#8 preservation, ask/roleplay parity, isolation, viewer selftest OK, live state clean.

Result:
- AUDIT FINDING #10 MEMORY WRITES JOURNAL — READY FOR FINAL RE-REVIEW.

## 2026-09-22 — Audit Finding #10 Final Proof Repair (tests + current docs only)

Date/time: 2026-09-22
External review accepted all runtime fixes; this repair hardens proof only. Earlier entries stay historical (26/64 close, 28/80 re-review, 81/81 interim counts).

What changed (tests + current authoritative docs; production runtime frozen):
- Removed the vacuous instrumentation check (literal `True`); per-thread snapshot/diff logs now prove each input's own before→after delta holds exactly its predicate, with receipts, counters, and partition cross-checked.
- Observer cross-grouping rewritten on `input_received` text evidence: each concurrent turn ID identified by its own input text and proven to hold exactly one start/input/writeback/final/complete with no foreign input.
- Counter→depth isolated to SAME turn_count (legacy seed_from_contact: STRANGER→FAMILIAR on counters alone) plus forced-failure fallback-formula coverage; precise bootstrap-vs-fallback terminology.
- Journal-window proof replaced with real-route snapshot instrumentation: bootstrap CONTACT bytes proven present before the first journal snapshot, exactly one turn receipt after.
- ARM headings genuinely sequential 1..29; no literal-`True` success check remains.
- Current docs now agree: 29 ARMs, 85 static `check()` sites, 86 executed PASS (one per-ID observer pair executes twice at runtime).

Proof: F10 suite 86/86 executed green, F9 suite 50/50 green, run_all 87/87, stress 61/61, isolation, viewer selftest OK, live state clean. Original audit untouched.

Result:
- AUDIT FINDING #10 MEMORY WRITES JOURNAL — READY FOR FINAL RE-REVIEW.
2

## 2026-09-23 — Finding #11 Personality / Boundary Authority

Date/time: 2026-09-23

What changed:
- Completed Finding #11 audit: authority matrix for personality/boundary surfaces; profile operational for existing users; pack birth-only; executable bounds preserved; unsupported knots (voice_model, voice_temperature, question_back, boundaries_overlay) deferred/orphaned honestly; identity-seed drive weights birth-authoritative; no selector-causal claim added.
- Added verify_finding11_personality_boundary_authority.py to tests/ and registered in tests/run_all.py.
- Updated AGENTS.md, AURA_CURRENT_CAPABILITIES.md, tests/README.md, SYSTEM_WHITEPAPER.md, GF_PRODUCT_SPEC.md; gf_boundaries.md preserved as descriptive of executable authority.
- Rebuilt _review_packet/ with manifest + SHA-256 rows; no live state touched.

Why it changed:
- Prior Finding #11 report inconsistencies (synthetic proofs, tautologies, incorrect accounting); required real-route evidence, structural reader tracing, truthful document state, and hashed packet.

What did NOT change (preserved):
- No production architecture redesign; no new manager module invented; no selection input changed; no amygdala; no reopened Findings #1/#2/#4/#6/#8/#9/#10 or M14/M16; live users/observer untouched.

Remaining open: pack knob wiring (voice_model/temperature/question_back/boundaries_overlay) remains an Architect decision; identity-seed self-modification continues via ukft_identity; no further integration until explicitly tasked.

## 2026-09-24 — Finding #11 Final Closure Hygiene (test contract correction, no architecture change)

Date/time: 2026-09-24

The 2026-09-23 Finding #11 entry stands as history; this entry corrects its test contract and closes the remaining blockers. No production architecture changed in this pass.

What changed (Finding #11 suite + current docs only; runtime frozen):
- Real-route proof replaces synthetic proof: the final suite proves authority through the real `BrainModule.ask()`/`roleplay()` lifecycle in temp sandboxes (onboard -> production post-turn save -> conflicting-pack clash on a fresh module -> prompt-seam observation) instead of synthetic fixtures.
- Selector receipt comparison: same-brain-state/varied-profile perturbation proves the brain selection receipt and basal winner are identical across personalities while the mouth seam receives the profile voice (nerdy vs bold) and only the expression layer differs.
- Fail-closed knob census: voice_model/voice_temperature readers == loader set only; question_back/boundaries_overlay/drives values never dict-read in production; envelope initiative/max_forwardness persisted-only with zero behavioral readers; pet_names_at kept separate (real roleplay-seam + post_check reader).
- Corrected initiative/max_forwardness classification: the earlier ACTIVE claim (initiative active via profile envelope; max_forwardness as a runtime voice cap) was disproven by the new reader census and corrected to PERSISTED-ONLY in `AURA_FINDING11_REPORT.md` (authority matrix + pack-knob section) and `SYSTEM_WHITEPAPER.md`. No wiring added — classification/document truth only.
- Real A->B->A isolation: fresh-module-per-turn A->B->A roleplay through the genuine disk-reload path proves personality/envelope/opt-outs partition-owned with no leakage and A unchanged by the B turn.
- Vacuous check removed: `check("this suite claims no tool-consent proof of its own", True)` deleted with no replacement; tool consent stays EXISTING-REGRESSION-OWNED (verify_safety + verify_i2 + verify_g5_safety, registration asserted).
- Final exact test accounting: 9 test functions (test_existing_profile_real_route, test_birth_real_path, test_personality_brain_mouth, test_route_ownership, test_knob_consumers, test_mirror_classification, test_boundary_ownership, test_isolation_real, test_accounting), 66 static assert/check sites (0 asserts), mechanically recomputed after the removal. The report's stale 11-name inventory was replaced with this exact list.

Gate diagnosis (GREEN OR IT DIDN'T HAPPEN enforced, nothing weakened or whitelisted):
- The prior 86/88 (M13 + Finding #10 live-pin trips) was diagnosed as ambient live-state drift during that gate: not test contamination (no live-write PROBE fired), not a stale fixture, not a real regression. Both suites pass unmodified in the clean rerun.
- A first rerun of this pass showed 81/88 from a bare-interpreter environment gap (this box's Python 3.14 had none of the approved libs: requests/bs4/pypdf missing, no pygame wheel for the viewer suites). Resolved by user-site installs (requests, beautifulsoup4, pypdf, pygame-ce) — environment repair only, zero repo/runtime changes.

Proof (final): focused F11 suite 9/9 GREEN (66 sites); full run_all 88/88; stress 61/61; embedded isolation PASSED; viewer verify PASSED + selftest OK (40 connectome frames + 17 monitor tabs); live state clean (no litter, people.txt pinned).

Result:
- AUDIT FINDING #11 PERSONALITY / BOUNDARY AUTHORITY — CLOSED.
- NEXT: FINDING #12 — AMYGDALA-ONLY PERTURBATION / FIELD ACTIVATION / SELECTED RESPONSE — UNKNOWN.

## 2026-09-24 — Finding #12 Amygdala Causality

Date/time: 2026-09-24

Mission: settle audit unknown #12 (AURA_BRAIN_GF_INTEGRATION_AUDIT.md sec 6.8C / sec 8-unknown-12) — whether amygdala-only perturbation can change a selected response through field activation. No verdict assumed; apparatus valid under either outcome.

What changed (tests + current authoritative docs; production runtime frozen):
- New receipt `tests/verify_finding12_amygdala_causality.py`, registered in `tests/run_all.py`. Runs the REAL production `run_amygdala()` loop in daemon threads (desktop-lobe shape) against temp-root sandboxes: suppressed arm (buffer alone, thread never started), neutral arm (inhibitory line), single-event arm (one excitatory line), burst arm (six distinct excitatory lines in one backlog tick), repeat arm (byte-distinct dose-identical lines, determinism), direct-stimulate instrument positive control (NOT amygdala evidence), forged spike-log sidecar control. Identical FIELD.step x3 per arm; per-arm subdirs; FIELD cleared between arms; no activation ever hand-set except the labelled instrument.
- Structural pins: hearing post-selection (line order); manifest-to-select slice has no STM / emotional-log / stress / mood / ukft_affect reads; mood tone renders only post-selection; API route has no amygdala/hippocampus/STM/background-lobe path; desktop master starts field heartbeat + amygdala + hippocampus; amygdala dose (0.1) and field threshold (0.05) unchanged.

Measurements (green run):
- Suppressed: dark, field 0.0, vault 0.0 (M1 emptied), M4 0.0, STM undrained, cold-receipt text. Neutral: thread drained + CALM_RESPONSE, zero spikes, dark. Single: spikes logged, danger activation 0.013789 after x3 steps (threshold 0.05), dark. Burst: 17 STRESS_SPIKE lines (danger x6, urgent x3, warning x3, critical x3, error x2), danger activation 0.082916, winner field with full 0.5 bid, field-state text naming DANGER. Repeat: identical winner + top node. Instrument: direct stimulation reaches field. Spike-log forgery: dark.
- First determinism run failed honestly (reused exact burst lines; a lingering earlier thread's SeenFilter swallowed them as duplicates — no stim, no log, dark). Matches ukft_amygdala.py:75-89 exactly: identical repeated input stimulates once per amygdala boot (deliberate Phase 0.7 design). Rerun with byte-distinct dose-identical lines is green. Recorded as observed mechanism truth in AURA_FINDING12_AMYGDALA_REPORT.md; no production change.

Verdict: CAUSAL-BOUNDED (desktop route) — amygdala-only backlog moves selection dark to field once activation crosses 0.05; single event does not. Scope narrow by construction (field 0.5 displaces only dark 0.2 among zero bids; no claim over vault/reasoning/proof/voice). Inhibitory path proven inert only on a silent manifold. Emotional log + mood tone proven non-inputs on this seam. NON-CONNECTED (API route) — no amygdala path exists there.

What did NOT change (preserved):
- Zero production files changed; zero saliences, thresholds, gains, or weights changed; zero redesign. Audit file untouched (historical evidence convention, as with all prior closures). No reopened findings; live users/observer untouched.

Docs updated in the same pass: AGENTS.md (frontier: #12 CLOSED, still-open list now pack-knob wiring only), SYSTEM_WHITEPAPER.md (amygdala UNKNOWN claim replaced), AURA_CURRENT_CAPABILITIES.md (stale claim fixed + dated closure line), AURA_WANTED_FEATURES.md (amygdala item settled), tests/README.md (new suite), plus AURA_FINDING12_AMYGDALA_REPORT.md.

Proof (final): focused F12 suite ALL GREEN; full run_all 89/89; stress 61/61; embedded isolation PASSED; viewer verify PASSED + selftest OK (40 connectome frames + 17 monitor tabs); live state clean (no litter, people.txt pinned).

Result:
- AUDIT FINDING #12 AMYGDALA CAUSALITY — CLOSED (CAUSAL-BOUNDED desktop / NON-CONNECTED API).
- NEXT: pack-knob wiring decisions remain the open Architect decision; no further integration until explicitly tasked.

## 2026-09-24 — Finding #12 Fail-Closed Regression + Frontier Sync (correction, zero production change)

Date/time: 2026-09-24

Mission: convert the accepted Finding #12 exploratory receipt into a FAIL-CLOSED shipping regression now that the verdict is established, and synchronize stale frontier wording. No redesign, no production changes, no reopened findings, no pack-knob work.

What changed (test contract + current authoritative docs only):
- tests/verify_finding12_amygdala_causality.py now locks the established CAUSAL-BOUNDED contract: exploratory classification checks replaced with explicit fail-closed checks — baseline dark, single dark, burst field, repeat field, burst field score 0.5, burst moved vs baseline, single did not move vs baseline. Existing controls and measurements kept; printed derived verdict retained as diagnostic output only; GREEN now requires the established result. No new sentence fixtures; zero production files touched.
- AURA_CURRENT_CAPABILITIES.md: stale open-seams wording corrected — the ONLY remaining original-audit decision is unresolved character-pack runtime knobs (#11 CLOSED 23 Sept 2026, #12 CLOSED 24 Sept 2026); stray duplicated "authority" wording removed.
- AURA_WANTED_FEATURES.md: already-closed audit work (shadow assembled-context fields #6, lessons correction #8, trust/importance #9, memory_writes #10, personality/boundary authority #11) removed from the open-work list; Remaining Original-Audit Findings now states the ONLY remaining decision is character-pack runtime knobs. Completion evidence preserved in the closed-finding entries, reports, and receipts.

Proof (final): focused F12 suite ALL GREEN (fail-closed contract: baseline dark, single dark, burst field 0.5, repeat field, burst-moved/single-unmoved); full run_all 89/89; stress 61/61; embedded isolation PASSED; viewer verify PASSED (proper temp-root sandbox; one out-of-sandbox manual run tripped on stale scratch-dir observer data, no live writes — reran correctly, green) + selftest OK (40 connectome frames + 17 monitor tabs); live state clean (no litter, people.txt pinned; zero live writes in 120-min scan).

Result:
- FINDING #12 — CLOSED AND FAIL-CLOSED. DESKTOP: CAUSAL-BOUNDED. BRAIN API: NON-CONNECTED. PRODUCTION CHANGES: NONE.
- REMAINING ORIGINAL-AUDIT FRONTIER: PACK-KNOB PRODUCT DECISIONS ONLY.

## 2026-09-24 — Finding #14 Pack-Knob Product Contract CLOSED (zero production change)

Date/time: 2026-09-24

Mission: close the last original Brain↔GF audit item (#14: whether every pack knob should be runtime-active is a product decision) with an explicit settled per-knob contract, a fail-closed shipping regression, report, and doc sync. Architect policy: the code is already correct — dormant knobs stay dormant. No wiring added, no knob activated, no redesign.

What changed (test contract + current authoritative docs only):
- New `tests/verify_finding14_pack_knob_contract.py` (9 test functions, 49 static check sites), registered in `tests/run_all.py` after Finding #12 and in `tests/README.md`. Locks: (A) pack schema truth — 10 packs directly under `characters/`, each `pack.json` + `seed.md`, exact 5-key schema (name/personality/interests/initiative/pet_names_at), no declared voice/question_back/max_forwardness keys, no `boundaries.md`, loader defaults + `boundaries_overlay None` for all ten; (B) structural fail-closed pins — zero production subscript/`.get` reads of voice_model/voice_temperature/question_back/initiative/max_forwardness outside their defining sites, runtime temperature authority (`ukft_mouth.py` fixed 0 + `ROLEPLAY_TEMPERATURE 0.7`, no temperature kwarg at the speak call site), question_back function/value separation, envelope writer-table presence, `boundaries_overlay` confined to the loader, global-floor owners present, no `p["drives"]` reads; (C) behavioral through real birth — birth consumes pack name/personality/interests, hostile-knob perturbation identity (voice_temperature 0.0, question_back 0.0, initiative HYPER, max_forwardness 99.0, voice_model evil, pet_names_at STRANGER, version 999 with personality unchanged → byte-identical birth greeting modulo run-varying physics jitter + byte-identical second-turn identity answers), envelope drift guard (persisted envelope keeps table values despite hostile pack fields; resolved hostile dict proves non-vacuous).
- Truth-correction vs earlier summaries: pack files DO declare per-pack `initiative`/`pet_names_at`, but those fields are unread mirrors — the personality-keyed envelope table is the authority (drift-guarded by the new suite).
- Jitter forensics (knob-independent, evidence in suite comments): birth-greeting `Field tension` varies run to run (clean-vs-clean control differed identically to hostile-vs-clean); one transient `Manifold phase: Viscous` + tension 0.9998 exonerated by all-clean reruns + decisive interleaved 3-hostile/3-clean run with all six births identical; birth greetings compared modulo tension/phase, second-turn probes exact-matched. Side observation (out of scope, no change): pack birth name does not surface through the "What is your name?" probe (identity-template territory, Finding #11); suite probes "Who are you?" instead.
- New `AURA_FINDING14_PACK_KNOB_CONTRACT_REPORT.md` (contract table, inventory, forensics, gates).
- Docs updated in the same pass: AGENTS.md (frontier: #14 CLOSED — NO open numbered findings remain), SYSTEM_WHITEPAPER.md (knob contract replaces open-decision wording), AURA_CURRENT_CAPABILITIES.md (only-remaining-decision wording retired, Architect-decision item 6 marked SETTLED, dated closure line), AURA_WANTED_FEATURES.md (knob item settled, no-remaining-decisions statement), tests/README.md (new suite). Historical records untouched by convention. GF_PRODUCT_SPEC.md, AURA_GOVERNANCE_PROPOSAL.md, gf_boundaries.md unchanged (no knob behavior claims to correct).

What did NOT change (preserved):
- Zero production files changed; zero behavior change. Any future knob activation is a new Architect-tasked M5 pass, not a bugfix. Audit file untouched (historical evidence convention). No reopened findings; live users/observer untouched.

Proof (final): focused F14 suite ALL GREEN (exit 0, live state untouched); full run_all 90/90 (prior 89/89 plus the new F14 suite); embedded isolation PASSED; stress 61/61 (safe temp-root workflow); viewer verify ALL PASSED from a fresh temp dir + selftest OK (40 connectome frames + 17 monitor tabs); live state clean (no litter, people.txt pinned). Viewer note: one run from the long-lived shared scratch dir showed 3 failures from stale CWD fixture data left by earlier sandbox runs (same hazard as the F12 pass) — reran from a fresh dir, green; scratch-only, zero live writes.

Result:
- AUDIT FINDING #14 PACK-KNOB PRODUCT DECISION — CLOSED.
- ORIGINAL BRAIN↔GF AUDIT — ALL NUMBERED FINDINGS CLOSED. No further integration until explicitly tasked.

## 2026-09-24 — Post-Audit Stage Transition: Conversation Normalization

Date/time: 2026-09-24

What changed (documentation / project-frontier pass; production runtime frozen):
- Created new authoritative `AURA_CONVERSATION_NORMALIZATION_ROADMAP.md` (CN0 -> CN1 -> CN2 -> CN3 -> CN4 -> CN5 -> CN6 -> CN7 plus gated family beta): CN0 is diagnostic-only with zero production behavior change; the first named failure target is the live "I remember: <old sentence>" memory-dump symptom with standing suspect classes A–G; every later phase carries an exit condition; M16 is the primary diagnostic instrument; FIX THE MECHANISM, NOT THE SENTENCE and M5 law preserved; anti-test-overfitting rule (paraphrase sets, multi-topic, positive/negative controls, held-back adversarial evaluation) included.
- Synchronized current authoritative docs to the same truth: original Brain<->GF numbered audit COMPLETE (no open findings; audit file itself stays historical and is not rewritten), target cognitive loop still behaviorally incomplete (audit-complete is NOT brain-perfectly-unified), active stage = Conversation Normalization, current first pass = CN0, family beta remains later and gated.
- `AGENTS.md`: Current Frontier rewritten (audit COMPLETE, CN active, CN0 first, roadmap linked); post-M16 order item 1 converted from "finish integration from still-open findings" to audit-COMPLETE with closure record preserved as evidence; stale "further integration work" hold replaced with CN-fixes/beta hold (CN0 itself needs explicit tasking). Laws, closure evidence, and history preserved.
- `SYSTEM_WHITEPAPER.md`: stale "Finish Brain/Nervous-System Integration / Continue crossing off those still-open audit findings" wording removed (section A now marks the audit stage COMPLETE); Current Roadmap now states audit COMPLETE, loop behaviorally incomplete, CN the immediate objective with M16 as diagnostic; Target Cognitive Loop section preserved unchanged as architectural intent, not current capability.
- `AURA_CURRENT_CAPABILITIES.md`: rev 8 (audit COMPLETE vs behavior-incomplete distinction, CN active, no mechanism change); stale "IN PROGRESS" audit wording retired; CN roadmap referenced; all bounded capability classifications preserved.
- `AURA_WANTED_FEATURES.md`: brain-integration NOW items (1–9) marked completed/history; stale "first unfinished objective is still item 7" retired; active NOW objective = Conversation Normalization with CN0 first; completion history and beta gates preserved.
- `GF_PRODUCT_SPEC.md`: CURRENT DEVELOPMENT STAGE = Conversation Normalization; NOT YET CLAIMED: normal human-level behavior, family-beta readiness; NEXT PRODUCT GATE = conversation normal enough for controlled human evaluation; audit-map-for-remaining-seams wording retired; product strategy otherwise unchanged.
- `AURA_GOVERNANCE_PROPOSAL.md` and `tests/README.md`: inspected, contain no stale CURRENT roadmap/frontier claims — unchanged by design.
- Rebuilt `_review_packet/` with manifest + SHA-256 rows; no live state touched.

What did NOT change (preserved):
- Zero production files changed; zero cognitive-architecture, weight, salience, pack, or live-state changes. No numbered audit finding reopened. CN0 not implemented (diagnostic harness is future tasked work); no conversation behavior fixed. Historical records untouched (audit file, prior changelog entries, reports, archive/reference).

Why it changed:
- Finding #14 closed the final open audit item, leaving current docs split between "still-open findings" language and "no open findings" reality, with no authoritative home for the next stage. This pass gives the audit its closed status everywhere and gives whole-conversation work its roadmap before any production behavior is touched.

Proof:
- Document consistency checks: repo-wide CURRENT-doc search for stale frontier claims ("still-open audit", "remaining audit findings", "Finding #14 open", "amygdala unknown", "brain integration is the next stage", "unfinished brain-integration objective", "IN PROGRESS" audit state) — all current claims corrected, remaining hits historical-only; no CURRENT document claims CN success or open findings; all CURRENT docs identify CN0 as next pass; beta remains later/gated; historical files byte-untouched (see review-packet manifest for the stale-search result and packet hashes).

Result:
- ORIGINAL BRAIN<->GF NUMBERED AUDIT: COMPLETE. CURRENT STAGE: CONVERSATION NORMALIZATION. CURRENT PASS: CN0 (diagnostic, not yet implemented). PRODUCTION CHANGES: NONE.
- NEXT IMPLEMENTATION TASK: CN0 ONLY — reproduce and trace current conversational failures before fixing production behavior.

## 2026-09-24 — CN0 Conversational Baseline COMPLETE (diagnostic, zero production change)

Date/time: 2026-09-24

What changed (diagnostic measurement only; production runtime frozen):
- New harness `tests/verify_cn0_conversation_trace.py`, registered in `tests/run_all.py` and documented in `tests/README.md`: 3 scenarios x 2 paraphrase variants = 6 independent hermetic conversations (30 turns) through the REAL `BrainModule.roleplay()` route with M16 receipts per turn; coarse continuity signals (no exact-response matching); positive controls (genuine recall, agenda read) and negative controls (emotional continuations must not dump); fake echo-mouth through the real post_check gate with brain-template fallback (live-mouth phrasing out of scope by construction). Findings reported, never gating; only trace-lifecycle/partition/representability/temp-root/live-hash integrity gates can fail. Includes `cn0_*` temp-root-scoped rerun hygiene (a cross-run stale-G7 "future quote" artifact was caught by inspection and fixed before the clean baseline).
- New report `AURA_CN0_CONVERSATIONAL_BASELINE_REPORT.md` (authoritative current diagnostic evidence) with per-failure INPUT/CAUSE/SEAM/WRONG-STATE/EVIDENCE/EXPECTED-BEHAVIOR and A–G suspect verdicts.
- `AURA_CURRENT_CAPABILITIES.md`: NOT-CAPABILITIES note records CN0 baseline completion and headline result (dump-on-emotion not reproduced; recall-routing + person/agenda state-carry are the dominant baseline failures).

What did NOT change (preserved):
- Zero production files changed; zero runtime, weight, salience, pack, or live-state changes. No numbered audit finding reopened. No conversation behavior fixed — CN1+ owns the failures.

Why it changed:
- CN0 was the explicitly tasked first normalization pass: objective evidence for current conversational failures before any production fix is designed.

Proof:
- `tests/verify_cn0_conversation_trace.py` green in hermetic sandbox (30 turns, complete monotonic lifecycles, partitioned, all writes in temp root, pinned live-state hashes unchanged); full `tests/run_all.py` green (see result line); baseline counts: context 13 / reasoning 4 / people 4 / dark 3 / teach 2 / belief 1 / agenda 1 / vault 1 / recap 1; M4-influenced 9, M14-influenced 8, M13-detected 0 (empty graph, expected); 2 legitimate recall dumps, 4/4 clean emotion turns; 5 diagnostic findings (F1 person recall loss both phrasings, F2 agenda write/read miss, F3 false-correction scope note, F4 paraphrase-unstable recall routing).

Result:
- CN0 EXIT CONDITION MET: every dominant failure class has INPUT/CAUSE/SEAM/WRONG-STATE/EVIDENCE/EXPECTED-BEHAVIOR with zero guessing and zero production change.
- NEXT: CN1+ mechanism fixes only when explicitly tasked; no CN production work begins untasked.

## 2026-09-24 — CN0 Observability Completion (diagnostic, zero production change)

Date/time: 2026-09-24

What changed (measurement only; production runtime frozen):
- `tests/verify_cn0_conversation_trace.py` extended to the full CN0 trace contract: per-turn capture of grounded pre-stance result (proven identity: manifest_thought() return = last_trace["response"], held as `template` before stance runs), ACTUAL cognitive_stance payload via a record-and-return wrapper around SovereignEgo.cognitive_stance (test-side only, behaviorally inert — identical return), exact mouth prompt captured test-side from roleplay_fn, plus final response. New hard integrity gates: grounded 30/30, stance 30/30 non-executive, prompt 30/30, final 30/30. New four-seam comparison (grounding / stance / prompt-construction / final) and per-seam stale-memory trace on all 4 emotion turns. No scenarios, controls, or gates weakened.
- `AURA_CN0_CONVERSATIONAL_BASELINE_REPORT.md`: F1 base wording corrected (C plus branch/grounding-construction failure; roadmap-D withdrawn — D requires the selected memory to become the reply); new §8 with seam provenance, comparison results, emotion A/B/C/D table, and corrected verdicts.
- Frontier sync: CN0 COMPLETE, CURRENT IMPLEMENTATION PHASE CN1 (not complete, no fix claimed) in `AGENTS.md`, `AURA_WANTED_FEATURES.md`, `AURA_CURRENT_CAPABILITIES.md`, `SYSTEM_WHITEPAPER.md` (§B), `GF_PRODUCT_SPEC.md` (stage + plan wording), and CN0 status note in `AURA_CONVERSATION_NORMALIZATION_ROADMAP.md`.
- `_review_packet/` rebuilt with SHA-256 table (source == copy mechanically asserted).

What did NOT change (preserved):
- Zero production files changed; zero runtime, weight, salience, memory-rule, stance, or mouth changes. F1/F2/F4 NOT fixed. CN1 NOT started.

Why it changed:
- The first baseline recorded stance_used/mouth-fallback metadata only, which could not honestly rule out E or localize the pre-F risk boundary. This pass closes exactly those observability fields.

Proof:
- CN0 suite green: 30 turns, complete lifecycles, partitioned, seam gates 30/30, live hashes pinned. SEAM-A flags 0, SEAM-B flags 0, SEAM-C flags 0. E-VERDICT: RULED OUT (intent template == grounded and intent winner == winner on all 30 non-executive turns; no framing introduced in B). Emotion turns: A framed=False quotes=0; B framed=False (history as context); C framed=False with memory-block/policy language and carried context (~3.3–3.5k chars); D clean. F-VERDICT: UNMEASURED (isolated to live generation). Full run_all + stress + isolation green (see result).

Result:
- CN0: COMPLETE (baseline + observability). PRODUCTION BEHAVIOR CHANGES: NONE.
- NEXT: CN1 — fix proven conversational mechanisms, not the original assumption (untasked).

## 2026-11-16 — Open-source preparation (repository, no runtime change)

Date/time: 2026-11-16

What changed (repository/documentation only; Aura runtime unchanged):
- Added `LICENSE` (Apache License 2.0) to permit open-source use and contribution.
- Rewrote root `README.md` for a public audience (plain-language overview of Aura, honest current state, how to run the working copy in `_recovery/src/`, and ways to help).
- Added `CONTRIBUTING.md` with contributor guidance and safety house rules (never run tests against live Aura/state; do not commit personal data/chat backups/memories; preserve before extending).
- Updated `.gitignore` and removed chat backups, session exports, and request logs from version control (kept locally): `_recovery/archive/session_backup_2026-09-24_redacted.json`, `_recovery/reference/chatgpt_export_2026-09-21_22/`, `request-logs-2026-09-24.csv`. Raw `new-session---2026-09-24t09-55-45-857z.json` and `aura_chat_files.zip` remain excluded.

What did NOT change (preserved):
- Zero production/runtime code behavior changed; no brain, memory, selection, or live-state logic modified. No tests run or altered as part of this pass.

Why it changed:
- To prepare the repository for going open source so others can help build and improve Aura, while keeping chat backups and personal/log data out of version control.

Proof:
- `LICENSE` (Apache-2.0), `README.md`, `CONTRIBUTING.md`, and `.gitignore` present; targeted paths untracked from git; no `sk-`/private-key patterns found in tracked content outside excluded local files.

Result:
- Repository prepared for public/open-source release under Apache-2.0 with chat backups/logs excluded from version control.
- NEXT: maintainer to rotate any real API keys that may have existed in local-only backups; rebuild missing test suites and continue recovery per `_recovery/TODO.md`.
