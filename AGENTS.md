# AURA_GF — Current Agent Manual

This is the current working manual for coding agents in `AURA_GF`. It is not
a pre-birth fork note. Aura GF is a live companion organism with persistent
state, user partitions, memories, relationship ledger, observer telemetry,
viewer/export tooling, and archived historical build records.

Historical build notes live later in this file and in `_reference/`. They are
evidence, not current instructions. Current code, current tests, and the
authoritative current documents beat stale history.

## What Aura Is

Aura GF is the companion-product branch of the AURA UKFT engine. The brain is
not an LLM. It is a Python/file-contract organism built around a cognitive
field, layered memory, proof-oriented reasoning, rapport, boundaries,
permissioned tools, partitioned users, and observer telemetry. The local mouth
may phrase the selected grounded response, but it is not allowed to decide.

Current stack: Python 3, stdlib plus existing approved libraries
(`requests`, `bs4`, `pypdf`). Do not add Python dependencies unless the
Architect explicitly approves a dependency change.

## Current Live State

The repository root contains live organism state. Treat root state files,
`users/`, `observer_trace/`, `backups/`, `characters/`, launchers, and live
logs as precious unless a task explicitly permits touching them. The blank
birth state is historical only.

Phase 4 conservative cleanup is complete and `CLEANUP SAFE`. Spent one-shot
scripts and historical/reference documents were moved into `_archive/` and
`_reference/`. Current cleanup report: `AURA_PHASE4_CLEANUP_REPORT.md`.

## Headline Laws

1. **PRESERVE BEFORE EXTENDING**
   "Improve", "modernize", "expand", "visualize", "upgrade", etc. do not
   mean replace existing working behaviour. Understand and preserve working
   mechanisms before extending them.

2. **CALLED != CONNECTED**
   A module existing, running, producing output, or passing its own unit test
   does not prove Aura actually uses it when choosing a response.

3. **CAUSAL-DONE LAW**
   A brain feature that is supposed to influence response selection is not
   DONE until an integration test proves that changing that feature's output
   can change or guard the selected response. Advisory/observer systems must
   be explicitly labelled advisory/observer-only.

4. **GREEN OR IT DIDN'T HAPPEN**
   Do not hard-code old suite totals as permanent law. A change is not done
   until all current shipping regression suites are green, stress is green,
   isolation is green, relevant feature-specific checks are green, and live
   state is clean. Historical totals such as `69/69` and `61/61` may appear
   only as dated evidence.

5. **TESTS NEVER TOUCH LIVE AURA**
   `python tests/run_all.py` is the normal full-suite workflow. Single suites
   may only run from a fresh temporary working directory with the required
   test environment/root. Stress must use its safe temporary-root workflow.
   Never run a state-writing test directly against the repository. Never
   invoke `verify_isolation.py` standalone without its required test-root
   environment. Never bypass the sandbox guard. The Phase-4 isolation incident
   is evidence for why this rule exists.

6. **SNAPSHOT BEFORE RISK**
   Snapshot and verify before risky state or architecture work. Stop Aura
   before restore. Never blindly restore more state than necessary.

7. **FIX THE MECHANISM, NOT THE SENTENCE**
   A bad conversational reply is evidence of a mechanism failure. Do not patch
   individual user phrases unless they reveal a general class of failure. User
   reports go through evidence, root cause, mechanism fix, regression, deploy.

8. **OBSERVABILITY MUST TELL THE TRUTH**
   No fake telemetry. No animation implying cognition unless runtime evidence
   exists. Distinguish: RAN, OUTPUT PRODUCED, OUTPUT USED, INFLUENCED
   DECISION. Unknown means not proven.

9. **BRAIN VS MOUTH**
   The brain owns Aura's context, memory, identity and persistent state. The
   mouth receives only the selected, grounded context required to phrase the
   current response.
   The mouth may phrase. It may not invent memory, identity, history,
   reasoning results, or decisions. Same Aura, better mouth.

10. **CURRENT STRATEGY VS OPEN FUTURE DECISIONS**
    Do not turn unresolved product ideas into architecture law. These remain
    OPEN Architect decisions: future adult/explicit capability, future
    GPU/hosted inference, future cloud mouth/model hosting, and Aura-derived
    non-companion products. Current local/CPU/content rules remain in force
    until changed by the Architect.

11. **NO SILENT CHANGES**
    Every meaningful change to Aura must leave a permanent written record in
    `AURA_CHANGELOG.md`. Existing entries are append-only. If an entry becomes
    wrong, append a correction. If work is reverted, record the revert and why.
    No meaningful runtime, architecture, test-contract, state-contract,
    product-rule, or observability change is complete until its changelog entry
    exists.

12. **DOCUMENTS MUST FOLLOW THE CODE — EVERY PASS**
    Documentation maintenance is part of the work, not a later cleanup job.
    A meaningful pass is not DONE until:
    CHANGE -> TEST -> CHANGELOG -> RELEVANT DOC UPDATE -> CROSS-CHECK ->
    BUILD REVIEW PACKET -> REPORT.

## What You May Touch

Default rule: touch only what the task requires. Live state and runtime code
are not scratch space.

Safe to edit when the task calls for it: current authoritative documents,
tests relevant to a code change, and the specific runtime modules required by
the requested mechanism fix.

Do not touch unless explicitly scoped: live state files, `users/`,
`observer_trace/`, `backups/`, launchers, `characters/`, `pdf_intake/`,
`pdf_processed/`, `_archive/`, `_reference/`, historical documents, and any
runtime module unrelated to the task.

Never copy live state from upstream AURA into GF. Never import personal vault,
identity, people, or episode files from another organism.

## Safe Test Workflow

Use these commands unless the task gives a stricter test plan:

```powershell
python tests/run_all.py
```

Stress must not run from the repo CWD. Use a temp workdir with `PYTHONPATH`
pointing here:

```powershell
$env:PYTHONPATH='C:\Users\DIYTE\OneDrive\Desktop\AURA_GF'; python 'C:\Users\DIYTE\OneDrive\Desktop\AURA_GF\tests\stress_all.py'
```

Viewer checks can run from a temp workdir with `PYTHONPATH` set:

```powershell
$env:PYTHONPATH='C:\Users\DIYTE\OneDrive\Desktop\AURA_GF'; python 'C:\Users\DIYTE\OneDrive\Desktop\AURA_GF\tests\verify_view.py'
python aura_synapse_view.py --selftest
```

Do not directly invoke `tests/verify_isolation.py` unless you provide the
required test root environment exactly and have a reason to do so. Prefer the
embedded production isolation proof inside `tests/run_all.py`.

## Snapshot / Restore Discipline

Create and verify a backup before risky state or architecture work:

```powershell
python ukft_backup.py
python ukft_backup.py verify latest
```

Stop Aura before any restore. Compare content hashes. Restore only proven
damage. If causation is uncertain, stop and report instead of guessing.

## What DONE Means

For a meaningful runtime or architecture change:

1. The mechanism is understood and preserved where already working.
2. The change has the smallest correct implementation.
3. Relevant regression checks pass.
4. Full shipping regression suites pass when appropriate.
5. Stress and isolation are green for state/architecture work.
6. Live state is clean.
7. `AURA_CHANGELOG.md` has an entry.
8. Relevant authoritative documents are updated in the same pass.
9. Stale contradictory claims were searched and resolved.

For observer/advisory systems, DONE must say observer/advisory-only unless
M5-style causal tests prove influence.

## Document Ownership

After completing a meaningful pass, ask: "Did this pass change anything that a
future agent needs to know?" If yes, update the relevant current document in
the same pass.

- `AGENTS.md`: project rules, safe workflow, DONE, current frontier.
- `SYSTEM_WHITEPAPER.md`: how Aura's brain/architecture actually works.
- `GF_PRODUCT_SPEC.md`: what the product does and what users experience.
- `AURA_CURRENT_CAPABILITIES.md`: working, partial, disconnected, shadow,
  legacy-dominant capability status.
- `AURA_WANTED_FEATURES.md`: NOW / NEXT / LATER / FUTURE work.
- `AURA_GOVERNANCE_PROPOSAL.md`: current governance rules until renamed or
  superseded.
- `gf_boundaries.md`: product behaviour/boundary policy only when policy
  changes.
- `tests/README.md`: testing workflow/contracts when testing changes.

Do not update unaffected documents merely to create activity. If no current
authoritative document needs changing, explicitly record: "Documentation
check: no current authoritative document changed by this pass."

Never silently rewrite historical records to match new reality. Current docs
get updated; historical docs stay historical; the changelog explains the
transition.

Fresh-agent test: if a brand-new coding agent opened this repository and only
read the authoritative current documents, would it understand the Aura that
exists right now? If no, the pass is not finished.

## REVIEW PACKET — EVERY MEANINGFUL PASS

After:

CHANGE
-> TEST
-> CHANGELOG
-> RELEVANT DOC UPDATE
-> CROSS-CHECK

the agent must build:

`_review_packet/`

Then the final workflow becomes:

CHANGE
-> TEST
-> CHANGELOG
-> RELEVANT DOC UPDATE
-> CROSS-CHECK
-> BUILD REVIEW PACKET
-> REPORT

The review packet is disposable.

It is NOT authoritative project state.

Nothing in Aura runtime, tests, launchers, or documentation may use
`_review_packet/` as an execution source.

It may be safely deleted after review.

The Architect workflow this serves: let the coding agent finish, drag
`_review_packet/` into the reviewer, get the pass reviewed, delete
`_review_packet/`. No manual file hunting.

### Packet creation

Before creating the packet:

- remove only the previous `_review_packet/`
- never modify/delete the authoritative originals
- recreate `_review_packet/` fresh

Copy files. Never move originals.

### Always include

Every packet must contain:

1. `_REVIEW_MANIFEST.md`
2. The current pass report, for example: `AURA_PHASE7_M1_REPORT.md`
3. Copies of EVERY file changed by the pass.
4. Copies of these standard reviewer-context files:
   - AGENTS.md
   - SYSTEM_WHITEPAPER.md
   - AURA_CURRENT_CAPABILITIES.md
   - AURA_WANTED_FEATURES.md
   - AURA_CHANGELOG.md
   - tests/README.md

### Include when relevant

Also include when changed or materially relevant:

- GF_PRODUCT_SPEC.md
- AURA_GOVERNANCE_PROPOSAL.md
- gf_boundaries.md
- specific runtime files involved in the mechanism
- specific test files involved
- specific audit/evidence documents used by the pass

For brain work this normally means the packet should include the actual
runtime files changed and the tests proving the change.

### Folder structure

Keep root current docs easy to see. For changed runtime/test files,
preserve useful grouping. Example:

```text
_review_packet/
    _REVIEW_MANIFEST.md
    AURA_PHASE7_M1_REPORT.md
    AGENTS.md
    SYSTEM_WHITEPAPER.md
    AURA_CURRENT_CAPABILITIES.md
    AURA_WANTED_FEATURES.md
    AURA_CHANGELOG.md
    runtime/
        aura_bridge.py
        ukft_recall.py
    tests/
        README.md
        verify_m1_relevance.py
        m5_harness.py
```

Do not rename copied files unnecessarily. The manifest must record each
copy's real original path. `runtime/` (and any grouped subfolder) holds
COPIES only.

### _REVIEW_MANIFEST.md

Create a fresh manifest every pass containing:

- pass name
- date/time
- final status
- purpose of the pass
- files changed
- files copied into review packet
- original path of every copied file
- reason each file was included
- production/runtime files changed
- test files changed
- docs changed
- files deliberately NOT included
- confirmation that packet contains copies only
- confirmation that `_review_packet/` is disposable

Also state: "Nothing in this packet is an authoritative replacement for
the original project files."

### Never include by default

Do NOT copy these merely for convenience:

- locked_patterns.txt
- people.txt
- episodic_memory.txt
- working_memory.txt
- rapport.txt
- identity_core.txt
- knowledge_graph.txt
- live state files generally
- users/
- users_probe/
- observer_trace/
- backups/
- live logs
- model/GGUF files
- PDF corpora
- caches
- archive/reference bulk
- screenshots
- large generated artifacts

Only include one of these if a specific review explicitly requires it.
If sensitive/live evidence is required later, include the smallest
necessary derived diagnostic evidence rather than blindly copying live
organism state.

### Safety

The review packet must NEVER:

- be imported by runtime
- be imported by tests
- be scanned as live state
- be treated as another Aura instance
- become a source for backups
- become part of user partitions
- contain executable duplicate state paths that Aura follows

It is simply a folder of review copies.

Verified 19 Sept 2026 (Phase 6B): backups use an explicit named-file
list (`ukft_backup.py: BACKUP_FILES`), test suites run explicit file
lists, and state roots resolve explicit paths — no directory walk can
adopt `_review_packet/` as organism state. If appropriate existing
ignore/exclusion machinery exists, exclude `_review_packet/` from
runtime/test/state scanning. Do not invent unrelated repository
tooling just for this.

Note: no repository ignore/exclusion file exists yet (no git tooling in
this tree), so there is nothing to add `_review_packet/` to. If ignore
tooling is introduced later, exclude `_review_packet/` there; do not
introduce unrelated repository tooling merely for this rule.

## Current Architecture Snapshot

Original UKFT brain is the working core: field activity/activation, memory
handling, foreground/long-term memory, forgetting/decay, and related brain
lifecycle behavior. GF/companion systems were added afterward.

Working, connected by prior evidence, but M5-proven causal ONLY where
receipts exist (`tests/verify_m5_causal.py`: selector competition,
temporal vault_support, path-conditional reasoning candidate;
`tests/verify_m1_relevance.py`: vault relevance gate verdicts;
`tests/verify_m2_thread_suppression.py`: thread-suppression verdicts;
`tests/verify_m3_reasoning_priority.py`: proof-priority + exemption
verdicts; `tests/verify_m4_selection_context.py`: bounded conversation-mode,
topic/thread, and current-person selection influence;
`tests/verify_m13_contradiction_gating.py`: query-relevant R3
contradiction verdicts (confident proofs become grounded conflict,
contested vault anchors withdrawn proposition-specifically, VERIFY via
the single shared rule since 11A);
`tests/verify_m14_episodic_influence.py`: relevant lived-event admission
and active-thread duplicate-suppression verdicts; observer/mood proven
non-causal to the seam — see
`AURA_CURRENT_CAPABILITIES.md`): turn pipeline, winner branches, G7
dialogue memory, G9 interlocutor binding, rapport-led depth,
people/beliefs/lessons branches, episodic recall, reasoning/proof layer,
confirm-gated tools in the live loop, partition serialization, character
packs, boundaries, and Tkinter UI file IPC.

Partial or non-causal: mouth/voice reliability, background attention, mood and
mirror advisory signals, contradictions beyond M13's proven structured
R-track scope (arbitrary vault prose, memory-correction policy), API-path tool
execution without in-process motor, decay without turn rehearsal, web/wiki/PDF
accretion, spontaneous/trigram idle speech, and gist code without a proven
nightly scheduler.

Working observer-only infrastructure: observer emitter/viewer/export records
and reports evidence states such as RAN, OUTPUT PRODUCED, OUTPUT USED, and
INFLUENCED DECISION. It reports causal evidence from other systems; it is not
itself causal to Aura's response selection and must never be described as
influencing the answer unless future architecture explicitly changes that and
M5 proves it. M16 now proves this reporting across the real
`BrainModule.roleplay()` route with explicit same-turn receipts, per-user
traces, viewer/export validation, and observer-off behavioral identity. M16
was reviewed and ACCEPTED on 21 Sept 2026.

Legacy dominant: old selection saliences and vault resonance still retain
substantial control. M4 now resolves a bounded set of conversation-mode and
current-person collisions; M13 now guards query-relevant R-track
contradictions; M14 now guards topic/person-trace episode evidence for
whole-token relevance, contradiction, singular ownership, and active-thread
duplication without changing saliences.

Old brain vs GF boundary (20 Sept 2026 audit, read-only, no runtime/test/state
changes): G7, people/current-person, beliefs, agenda, teaching, and episodic
recall genuinely connect into cognition and response selection, but connected
to selection is not the same as part of the original UKFT brain. Goal:
GF experience -> original UKFT brain -> existing brain lifecycle -> later
retrieval. In plain English: conversation/episodic/people/relationship
experience should enter and affect the old brain, not only sit in separate GF
files used around the selector.

## Target Cognitive Loop — Permanent Architecture Intent

Aura is not intended to become a collection of GF modules independently
feeding a selector or an LLM prompt.

The intended design is one integrated cognitive loop:

USER → GF INTERPRETATION → ORIGINAL UKFT BRAIN → CURRENT UNDERSTANDING /
STANCE / RESPONSE INTENT → MOUTH → RESPONSE → BRAIN WRITEBACK → NEXT TURN

In plain English: when the user speaks, that input is a stimulus/experience.
Relevant systems — current conversation/context, people/current-person,
episodic history, beliefs, relationship/rapport state, personality,
boundaries, current internal state, relevant memories — should contribute
their relevant grounded information to the original UKFT brain. They should
not all blindly dump their entire files into the mouth prompt.

The UKFT brain is the central integration point. It combines what is
happening now + what Aura remembers + who is involved + relationship
history + beliefs + personality/boundaries + internal brain state, and
forms a coherent current result representing things such as what Aura
understands is happening, what memories are relevant, what she currently
considers important, her grounded social/relationship stance, and what she
intends the response to accomplish. That integrated brain result is what
is handed to the mouth.

Brain vs mouth (existing law 9, preserved): the brain decides what Aura
means; the mouth decides how to say it. The mouth may choose natural
wording, rhythm, conversational style and phrasing. The mouth must not
independently invent memories, identity, relationship history, beliefs,
facts, emotional/relationship state, or substantive response intent. The
mouth receives enough grounded brain context to express Aura naturally
without becoming the real decision-maker.

Feedback loop: the completed interaction feeds back into Aura's brain so
it can affect later cognition. Therefore the target is not user → LLM,
and not user → twenty sidecar databases → giant prompt → LLM decides.
It is: user experience → relevant GF interpretation → UKFT brain
integration → Aura's current understanding / stance / intention → mouth
phrasing → response → experience/writeback into brain → next cognitive
cycle.

Important clarification: Pass 1 only proves the first narrow crossing —
conversation input can enter the old brain through the real thalamic/field
path. That is not the final integration architecture. Future passes must
progressively bring the relevant GF systems into this shared brain-centered
loop rather than leaving them as disconnected sidecars. This documentation
is not permission to merge every subsystem immediately: integration remains
incremental and must be proven structurally and causally (M5 law).

ONE ORGANISM, NOT ONE SELECTOR SURROUNDED BY TWENTY DATABASES.

## Current Product State

Built: character/personality packs, per-user partitions, brain API, immersive
roleplay path, G7 conversation memory, G8 rapport depth, G9 current-person
grounding, boundaries, observer/viewer/export, Tkinter UI IPC, and Discord
adapter code.

Not live-proven: Discord deployment. It needs token/intent, age-gate,
kill-switch, rate limits, and one-voice-per-box proof before product use.

Gist scheduling is not proven. `ukft_gist.py` exists; a scheduler and
ownership proof (M11) are still required before claiming automatic operation.

Product target, not architecture law: first words under about 2 seconds. The
mouth must never begin substantive content before the brain has made and
grounded its decision merely to fake low latency.

## Current Frontier

Phase 4 cleanup completed safely. The original Brain<->GF numbered audit is
COMPLETE (Finding #14 closed 24 Sept 2026 — no open numbered findings
remain). Current work is Conversation Normalization, not cleanup and not
further audit passes. Authoritative roadmap:
`AURA_CONVERSATION_NORMALIZATION_ROADMAP.md`.

Completed sequence (M5 proven + hardened 19 Sept 2026; M1 proven 19 Sept 2026
— vault relevance gate ships in `aura_bridge.py` with M5 receipt; M2
proven 19 Sept 2026 — active-thread suppression with M5 receipt; M3
proven 19 Sept 2026 — reasoning priority audited/preserved plus narrow
gap-yields-to-memory exemption, full-residue and material-predicate
answer-bearing hardening, two M5 receipts; M4 proven 19 Sept 2026 — bounded
real-context scoring and current-person guard with two M5 receipts, hardened
so answer-bearing, bounded lexical person compatibility, and spoken explicit
recall share one anchor (not authenticated historical ownership), then 10B
structural eligibility so incompatible first-person recall is withdrawn even
without legacy voice (vault->reasoning receipt); M13 proven 20 Sept 2026 —
query-relevant contradiction gating with proof + vault M5 receipts
(`tests/verify_m13_contradiction_gating.py`), hardened same day (11A:
VERIFY proposition provenance — single shared rule in
`ukft_inference.py`, legacy entity-level R5 matcher deleted); GF-old-brain
Passes 1/1A/2 proven 20 Sept 2026; M14 proven 21 Sept 2026 — relevant
episode evidence can preserve the existing reasoning bid while off-query,
reply, contradicted, wrong-owner, and active-thread duplicate evidence is
suppressed, with selected lived-event provenance entering the brain-owned
stance; M16 proven 21 Sept 2026 — real roleplay-route observer evidence now
distinguishes ran/produced/used/influenced without entering cognition and was
reviewed/accepted; M5 stays permanent law for every later change):

M5 COMPLETE -> M1 COMPLETE -> M2 COMPLETE -> M3 COMPLETE -> M4 COMPLETE ->
M13 COMPLETE -> GF/OLD-BRAIN PASS 1/1A/2 COMPLETE -> M14 COMPLETE -> M16
COMPLETE -> ORIGINAL NUMBERED AUDIT COMPLETE (all findings closed, Finding
#14 last, 24 Sept 2026). The bounded crossings are stable enough to begin
whole-conversation normalization; the target cognitive loop remains
behaviorally incomplete — the audit is complete, the brain is NOT claimed
fully unified.

Plain English:

prove influence -> stop bad memory wins -> protect conversation context -> let
reasoning beat irrelevant recall -> feed real context into selection -> handle
contradictions -> GF experience enters the old brain and is retrievable through
it -> handle episodic influence -> prove all of it in the viewer.

M16 (21 Sept 2026): the real `BrainModule.roleplay()` route emits one complete
partitioned observer lifecycle and explicit same-turn evidence receipts.
Viewer/export distinguishes RAN, OUTPUT PRODUCED, OUTPUT USED, and INFLUENCED
DECISION, validates influence against system-specific causal bases, and keeps
same-numbered turns separate by `(user_id, turn_id)`. M1/M2 and selected legacy
branches stop below influence without a dedicated turn receipt; basal winner,
Pass-2 stance, and mouth are separate stages. Observer remains non-causal and
disabling it leaves the selected response unchanged — COMPLETE, READY FOR
REVIEW, subsequently ACCEPTED 21 Sept 2026.

The original numbered audit is complete and the verified seams are stable
enough to begin whole-conversation normalization. This is not a claim that
every sidecar is already unified or that the brain is fully unified:
bounded crossings proven, target loop still behaviorally incomplete. The
next engineering work is Conversation Normalization starting with CN0
(diagnostic, zero production change), per
`AURA_CONVERSATION_NORMALIZATION_ROADMAP.md`. Do not reopen closed findings.

Pass 1 (20 Sept 2026): post-selection hearing bridge (`_hearing_ingest` in
`aura_bridge.py` feeds each turn's input through the real thalamic gate into
the field; receipt `tests/verify_brain_gf_pass1.py`) — COMPLETE, READY FOR
REVIEW. Desktop hears twice (async pre-turn + sync post-turn, accepted);
API-route cross-turn field carry still absent by existing clear/no-restore
policy, not redesigned here.

Pass 1A (20 Sept 2026): real turn persistence (`ukft_brain_api.py` restores
each user's `field_state.txt` into the cleared singleton after the
partition swap, and heartbeat-settles + persists post-hearing state before
the partition sync-back, in both `ask()` and `roleplay()`; edge-preserving
serializer extension in `aura_bridge.py`; receipt
`tests/verify_brain_gf_pass1a.py`: same-user retrieval across fresh module
instances with G7/episodic neutralized, cross-user isolation with
return-to-A, persistence-deleted dark control, roleplay-route sharing,
Pass-1 invariants kept) — HARDENED, READY FOR REVIEW. Desktop double-hear
left documented (async stimulation not guaranteed, so no safe suppression);
API background lobes (sleep/decay) still absent — warmth persists until
later-turn leak steps cool it.

Pass 2 (20 Sept 2026): first brain-owned cognitive result
(`SovereignEgo.cognitive_stance` in `aura_bridge.py` forms current
understanding + person + relevant history + relationship stance + response
intent from the decision trace, live people model, G7, fresh rapport
ledger, and personality config; `build_prompt_from_stance` in
`ukft_roleplay.py` is the roleplay route's only prompt entry; receipt
`tests/verify_loop_pass2.py`: person/relationship/personality causal
proofs, sidecar-corruption mouth-obedience identity, rich-rapport negative
control on a grounded fact) — COMPLETE, READY FOR REVIEW. Legacy
`build_prompt` signature kept for the desktop route and tests; desktop
master assembly left untouched (different route, out of scope).

M14 (21 Sept 2026): episodic influence policy (`m14_filter_recall` in
`aura_bridge.py`) governs the existing diary-recall reasoning path after M4
and before selection. It requires visible, whole-token-relevant lived-event
evidence; suppresses reply, contradicted, singular wrong-owner, and active-G7
duplicate evidence; changes no saliences and adds no episode candidate.
`cognitive_stance` carries bounded provenance only when eligible recall wins,
and `build_prompt_from_stance` labels it event memory rather than objective
proof. Receipt `tests/verify_m14_episodic_influence.py` proves episode
admission and duplicate suppression can change or guard the selected winner,
including polite-modal ownership hardening — COMPLETE, READY FOR REVIEW.

Finding #11 PERSONALITY / BOUNDARY AUTHORITY — CLOSED 23 Sept 2026 (authority matrix + test receipt; no new architecture; pack knobs honestly classified; safety preserved; no selector causality claimed).

Finding #12 AMYGDALA CAUSALITY — CLOSED 24 Sept 2026 (verdict CAUSAL-BOUNDED on the desktop route: genuine `run_amygdala()` backlog through real field physics moves selection dark→field once the danger node crosses the 0.05 candidate threshold — single event 0.0138 stays dark, six-line backlog 0.0829 wins field 0.5; NON-CONNECTED on the API route, which has no amygdala/hippocampus/STM path; zero production change, zero weight changes; receipt `tests/verify_finding12_amygdala_causality.py`).

Finding #14 PACK-KNOB PRODUCT DECISION — CLOSED 24 Sept 2026 (settled per-knob contract: name/personality/interests/seed-anchors birth-active; pet_names_at envelope-active via the personality-keyed table; max_forwardness/initiative persisted-only; voice_model/voice_temperature/question_back-value dormant with zero production readers; boundaries_overlay absent with the global floor owning; identity-seed drive presets dead code; hostile-knob perturbation identity through real birth; zero production change, zero behavior change; receipt `tests/verify_finding14_pack_knob_contract.py`). The original Brain↔GF audit has NO open numbered findings remaining.

Post-M16 development order:

1. **Original Brain<->GF numbered audit — COMPLETE.** All numbered
   findings in `AURA_BRAIN_GF_INTEGRATION_AUDIT.md` are closed (fixed,
   causally proven, classified, or settled as an Architect product
   decision; Finding #14 last, 24 Sept 2026). The audit file itself is
   historical evidence — do not rewrite it and do not reopen findings.
   The per-finding closure record below is preserved as evidence.
    Audit finding #1 (empty-file API copyback) is CLOSED 21 Sept 2026:
    allowlisted pending-slot clears now sync back as empty state, missing
    root files never delete partition state, Pass-1A field ownership kept.
    Audit finding #2 (ego/vault partition ordering) is CLOSED 21 Sept 2026:
    the requested partition is swapped into root before any ego is created
    or used on an API turn, with restore-on-early-failure in both ask()
    and roleplay().
    Audit finding #4 (transactional writeback) is CLOSED 21 Sept 2026:
    detectors propose against non-persisting staged models and only the
    basal winner's decision-owned effects commit post-selection; losing
    candidate-owned effects leave their stores byte-identical, selected
    effects commit exactly once, and turn-owned experience writeback
    (mentions, gaps, sleep-wake, G7/episodes/rapport/hearing/field) is
    intact — receipt `tests/verify_finding04_transactional_writeback.py`.
    Audit finding #6 (shadow context fields) is CLOSED 21 Sept 2026
    (re-review corrections 22 Sept 2026): the bundle is classified
    (`current_user` CAUSAL, the rest DUPLICATE, dead keys retired) and
    person-attribute questions route through the known-person gate into
    truthful held-fact answers or honest declines — receipt
    `tests/verify_finding06_shadow_context.py` (true M5, ask/roleplay
    parity, sibling-frame truthfulness).
    Audit finding #8 (lesson correction) is CLOSED 22 Sept 2026: the
    ledger is an audit/history + review source (never a second truth
    source); parseable corrections answer later VERIFY provisionally
    via held beliefs (graphless too), person corrections surface via
    best-match recency without erasure, contested claims still route
    to confirm/cancel, banked-only text says exactly that — receipt
    `tests/verify_finding08_lessons_correction.py` (two true M5s,
    stale-lesson no-hijack, Finding-#4 preserved).
    Audit finding #9 (belief trust / people importance) is CLOSED
    22 Sept 2026 (re-review correction 22 Sept 2026): both metrics
    audited end-to-end and retained ADVISORY-HISTORY — computed,
    persisted, test-readable, zero production BEHAVIORAL readers
    (proven by repo-wide structural pins + hostile-perturbation
    identity on every live seam); Finding #10 adds one bounded
    reporting/accounting reader that classifies durable trust
    mutations without influencing cognition or selection — receipt
    `tests/verify_finding09_trust_importance.py` (now included
    in Finding #10 packet with narrow exception).
    Audit finding #10 (memory_writes journal) is CLOSED 22 Sept
    2026: size-growth heuristic replaced with before/after partition-
    bytes diff reporting durable mutations (clears, shrinkage,
    equal-size replacements, content identity); truthful counters
    (facts_learned, threads_shared, threads_closed, lessons_banked)
    via shared `_apply_write_counters()` in ask/roleplay; observer
    gated on non-empty writes — receipt
    `tests/verify_finding10_memory_writes_journal.py` (29 ARMs, 86 checks).
     Audit finding #12 (amygdala causality) is CLOSED 24 Sept 2026:
     CAUSAL-BOUNDED on the desktop route (amygdala-only backlog moves
     selection dark to field through real field activation; single
     event sub-threshold; emotional log and mood proven non-inputs on
     the seam), NON-CONNECTED on the API route (no amygdala path) —
     receipt `tests/verify_finding12_amygdala_causality.py`, zero
     production change.
     Audit finding #14 (pack-knob product decision) is CLOSED 24 Sept
     2026: settled per-knob contract (birth-active, envelope-active,
     persisted-only, dormant, floor-owned, dead-code classifications
     with hostile-perturbation identity through real birth) — receipt
     `tests/verify_finding14_pack_knob_contract.py`, zero production
     change, zero behavior change.
     No numbered findings remain open. Do not reopen the closed field persistence, roleplay
     observer lifecycle, roleplay person/relationship timing, bounded M14
     episodic, finding-#1 copyback, finding-#2 partition-ordering,
     finding-#4 transactional-writeback, finding-#6 shadow-context,
     finding-#8 lesson-correction, finding-#9 trust-importance,
     finding-#10 memory-writes-journal, finding-#12 amygdala-causality,
     or finding-#14 pack-knob-contract findings merely for cleanup.
2. **Conversation normalization — CURRENT MAJOR ENGINEERING STAGE.**
   Ordinary conversation is now the major behavioral objective. CN0 —
   Conversational Baseline + End-to-End M16 Trace — is COMPLETE
   (diagnostic baseline + observability completion, zero production
   behavior change; report
   `AURA_CN0_CONVERSATIONAL_BASELINE_REPORT.md`). CURRENT
   IMPLEMENTATION PHASE: CN1 — fix proven conversational mechanisms, not
   the original assumption. CN1 is NOT complete and no CN1 fix is claimed.
   Diagnose real failures with M16, fix mechanisms rather than sentences,
   and turn genuine failure classes into regressions, per
   `AURA_CONVERSATION_NORMALIZATION_ROADMAP.md` (CN0 -> CN1 -> CN2 ->
   CN3 -> CN4 -> CN5 -> CN6 -> CN7).
3. **Controlled family beta.** This is a trusted multi-human failure-discovery
   stage, not public launch. It requires normal-enough conversation, reliable
   per-user isolation, proven backup/restore, concurrent-user no-leakage proof,
   a controlled client/deployment path, and the channel's kill-switch, rate,
   boundary, stranger, and age protections.
4. **Product readiness and later scale.** M15 recovery, M9 deployment, M12
   concurrency/scale, correction policy, M10 kindness, M11 gist ownership, and
   safe latency remain planned. M10, M11, perfect latency, and long-horizon
   growth do not automatically block the earliest tightly controlled family
   beta unless a concrete safety requirement makes them necessary.

The secure thin-client/local-encrypted-vault/private-server-brain design is a
future product architecture target, not current capability. Exact hosting,
model, population-learning, and privacy design remain open Architect decisions.

Do not begin CN1 production fixes or family beta work until explicitly tasked.
CN0 is complete; CN1 implementation itself requires explicit tasking.

## Behaviour Contract

Proof beats association. Honest ignorance wins for verify/compare/when when
evidence is absent. Open questions may use resonant knowledge only when it is
relevant and not contradicted by the current thread. Tools stay
confirm-gated. Consent wording stays exact. Persona/attunement changes belong
in product/boundary rules, not in the honesty machinery.

Historical events and provenance are preserved. Semantic knowledge, beliefs,
inferred claims, and graph edges may be corrected, superseded, decayed, or
deleted only under explicit logged policy. Never silently rewrite historical
events to make Aura's past cleaner.

## Historical Build Record

The blank-fork, G0-G9, viewer recovery, Phase-3 audit, Phase-4 recovery, and
cleanup history remain useful evidence, but they are not current law. See:

- `AURA_MASTER_INVENTORY.md`
- `AURA_FILE_INVENTORY.md`
- `AURA_CODEBASE_MAP.md`
- `AURA_RULE_AUDIT.md`
- `AURA_PHASE4_CLEANUP_REPORT.md`
- `_reference/`
- `AURA_CHANGELOG.md` for changes from Phase 5 onward

Historical suite counts are dated evidence only. Use dynamic green-gate rules
for current work.
