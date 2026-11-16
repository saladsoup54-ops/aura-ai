# AURA CURRENT CAPABILITIES — what she already has (rev 8, 24 Sept 2026)

> Rev 8 records the post-audit frontier reset: the original Brain<->GF
> numbered audit is COMPLETE (all findings closed, Finding #14 last, 24
> Sept 2026). AUDIT STATUS: complete. CURRENT BEHAVIOR: conversation not
> yet normalized; the target cognitive loop remains behaviorally
> incomplete. The active engineering stage is now Conversation
> Normalization (first pass CN0, diagnostic only), per
> `AURA_CONVERSATION_NORMALIZATION_ROADMAP.md`. No capability mechanism
> changed in this pass.
>
> Rev 7 records review acceptance: M16 is COMPLETE, PROVEN, HARDENED, and
> ACCEPTED. This changes no capability mechanism. The original numbered
> audit is now COMPLETE (rev 8); Pass 1/1A, Pass 2, M14, and M16 are bounded
> completed milestones rather than proof of a fully unified cognitive loop.

> Rev 6 adds M16 evidence: the real `BrainModule.roleplay()` route now emits
> one partitioned observer lifecycle plus conservative per-system receipts for
> RAN, OUTPUT PRODUCED, OUTPUT USED, and INFLUENCED DECISION. Viewer/export
> consumes those explicit same-turn receipts, rejects unsupported influence
> claims, and groups turns by `(user_id, turn_id)`. Observer remains
> M5-proven non-causal and behaviorally inert when disabled.

> Rev 5 adds M14 evidence: the existing episodic-recall reasoning path now
> has a provenance-aware eligibility policy and two M5 receipts. Relevant
> lived-event admission can change vault -> reasoning; active-thread duplicate
> suppression can guard reasoning -> context. No episode candidate or salience
> change was added, and selected episode provenance reaches the roleplay mouth
> only through the brain-owned stance.

> Rev 4 adds the M5 evidence layer (19 Sept 2026): the causal-influence
> harness (`tests/m5_harness.py` + `tests/verify_m5_causal.py`, registered
> in `tests/run_all.py`) now proves influence instead of asserting it.
> M5 PROVEN CAUSAL: temporal vault_support modulation (2-C -> 2-D; 0.0 ->
> 0.3 flips voice -> vault) and the reasoning candidate (path-conditional:
> proof present -> reasoning beats vault 0.95 vs 0.8). M5 PROVEN NON-CAUSAL
> TO THE CURRENT RESPONSE-SELECTION SEAM: observer telemetry
> (observer-only) and mood/affect tone (advisory on the tested path; no
> claim about other future uses). M1-M4 now have their own receipts below;
> every unlisted influence keeps its prior status — see
> `AURA_PHASE6_M5_REPORT.md`. No saliences or weights were changed by M5.
> 6A hardening (same day): harness fails closed without its validator;
> ego control uses independent identical sub-sandbox fixtures.

> Rev 2 corrections: `aura_ui.py` re-audited THROUGH the IPC lens and
> reclassified CONNECTED (was ORPHANED — that verdict used Python imports
> only, which the reviewer correctly rejected as insufficient evidence);
> orphan kinds split four ways per reviewer instruction. Rev 3 reconciles
> those orphan classes against caller evidence: master-launched/background
> components are not MODULE ORPHANED merely because their outputs are weak
> or non-causal. Source for every row: AURA_CODEBASE_MAP.md,
> AURA_FILE_INVENTORY.md, and the evidence below. Proposals, not verdicts.

## Re-audit: aura_ui.py — CONNECTED via file IPC (operator-gated)

Evidence: `Launch_Aura.bat:27-36` starts `aura_ui.py` as its own "AURA UI"
process beside core + synapse. `aura_ui.py:152` appends typed messages to
`ui_input.txt` via the bus; `aura_master.py:531` drains that queue in
order into the live turn; `ukft_voice.py:169` dictation shares the same
queue. Return path: master/motor publish to `aura_output.txt`
(`aura_master.py:365-375`, `aura_motor.py:204`), which `aura_ui.py:210`
watches and displays. Contracts pinned by `aura_constants.py:40-42` and
covered by `verify_i1`, `verify_races`, `verify_g_livevoice`,
`verify_pass05`. Verdict: CONNECTED (process boundary + file IPC), causal
only while the UI process runs — terminal input uses the identical queue,
so the path is live regardless of which writer feeds it. Phase-2 census
row calling it unwired is corrected here.

## M5 PROVEN CAUSAL (receipts in `tests/verify_m5_causal.py`, 19 Sept 2026)

Response competition/winner selection through the real
`BasalGanglia.select` (candidate/context perturbations flip winners) ·
temporal vault_support modulation (2-C -> 2-D) · reasoning candidate,
path-conditional (a present proof beats vault association) · M1 vault
relevance gate (receipts in `tests/verify_m1_relevance.py`: verdict
change guards/flips the winner) · M2 active-thread suppression
(receipts in `tests/verify_m2_thread_suppression.py`: suppression
verdicts guard/flip the winner; switches and named requests escape) ·
M3 reasoning priority (receipts in `tests/verify_m3_reasoning_priority.py`:
pre-existing proof/gap priority preserved + gap-yields-to-memory
exemption; full-residue answer-bearing preserves the material
know/learned/read/absorbed predicates independently of M1 noise;
SovereignVoice generic-audit ownership preserved; answer-bearing specific
recall is released by M4; M3 exemption cancelled when no owned anchor exists) ·
M4 real selection context (receipts in
`tests/verify_m4_selection_context.py`: bounded strong continuation flips
vault->context; changing only valid current-person binding changes/guards
vault->voice and, voice-less, vault->reasoning; incompatible first-person
autobiographical anchors are ineligible regardless of legacy voice triggers;
answer-bearing, person-compatibility, and spoken-recall evidence must come
from the same anchor; owner-unproven bids no context; compatibility is bounded
lexical evidence, not authenticated historical ownership) ·
M13 contradiction gating (receipts in
`tests/verify_m13_contradiction_gating.py`: query-relevant R3
contradictions guard answers — confident compare/describe proofs become
grounded conflict with the winner flipping reasoning->conflict;
contested vault anchors withdrawn proposition-specifically; VERIFY uses
the same single shared rule (11A: property records no longer block is_a
answers, genuine cycle VERIFY still conflicts); unrelated
contradictions, honest gaps, M1/M2/M3/M4 verdicts, cortex DISCORDANT,
episodes, and the mouth all proven non-interfering) ·
M14 episodic influence policy (receipts in
`tests/verify_m14_episodic_influence.py`: whole-token-relevant lived-event
admission changes vault->reasoning; active-G7 duplicate suppression guards
reasoning->context; reply, contradicted, singular wrong-owner, and invisible
episode evidence cannot vote; selected provenance enters the stance as event
memory, never objective proof) ·
mouth/LLM exclusion (re-phrasing cannot move the decision).

M5 PROVEN NON-CAUSAL TO THE CURRENT RESPONSE-SELECTION SEAM: observer
telemetry (OBSERVER ONLY) · mood/affect tone (ADVISORY on the tested
path; no claim about other future uses).

## WORKING / CONNECTED BY PRIOR EVIDENCE — M5 CAUSAL STATUS UNPROVEN

These run, connect downstream by caller/contract evidence, and are
covered by module/integration suites — but none yet has an M5 receipt
proving its output can change or guard the selected response. Do not
describe them as M5-proven causal. They are working features, not
broken ones.

Turn pipeline boot→writeback incl. winner branches, grounding · G7 dialogue
memory beyond M4's proven selection subset · G9 interlocutor rendering,
normalization, and activity gate beyond M4's narrow ownership guard · rapport
ledger → depth →
prompt/mirror · people/beliefs/lessons branches + VERIFY fallback ·
episodic diary recording and recall outside M14's proven topic/person-trace
selection subset (reply-kind excluded) · R-track chain + hourly
rebuild · confirm-gated tools + execute-only motor (live loop) ·
partitions serialize without crosstalk · packs seed birth vaults ·
envelopes + explicit deflects · Tkinter UI input/output IPC pair ·
post-selection thalamic hearing bridge (GF input → field nodes/edges under
existing field rules; Pass 1 receipt `tests/verify_brain_gf_pass1.py`) with
per-user cross-turn persistence on the API route (restore after partition
swap + post-hearing heartbeat/persist before sync-back; edge-preserving
`field_state.txt`; Pass 1A receipt `tests/verify_brain_gf_pass1a.py`) ·
brain-owned roleplay stance (understanding/person/history/relationship
stance/intent formed in `cognitive_stance`, phrased via
`build_prompt_from_stance` as the route's only prompt entry; Pass 2
receipt `tests/verify_loop_pass2.py`; M14 adds bounded selected event
provenance with no mouth-side episodic read; desktop master assembly
unchanged).
Observer emitter + viewer + export are working OBSERVER-ONLY
infrastructure (M5-proven: cannot move the winner). M16 now covers the real
`BrainModule.roleplay()` route from input through winner, brain-owned stance,
mouth, writeback, final response, and completion. Its explicit same-turn
receipts distinguish RAN, OUTPUT PRODUCED, OUTPUT USED, and INFLUENCED
DECISION for M1/M2/M3/M4/M13/M14, old-brain field restore, Pass-1 hearing,
people/belief/agenda/teach branches, the basal winner, stance, and mouth.
Influence is reported only where an existing causal receipt applies; selected
legacy branches without dedicated M5 proof stop at OUTPUT USED.
M16 was reviewed and ACCEPTED 21 Sept 2026.

## PARTIAL (wired, gaps)

Mouth/voice (narrow wins; daemons fail → template) · attention (background
real; the turn never runs the thalamus lobe, but Pass 1 reuses its gate
function post-selection for hearing) · mood/mirror advisory (audit in trace
only) · contradictions counted AND query-relevantly gating (M13 proven
for structured R-track records; arbitrary vault prose and
memory-correction policy remain open) · API-path tools
speak without in-process motor · decay without turn rehearsal ·
API-route field cleared per ask, then re-owned per user (persisted
`field_state.txt` restored after the swap; post-hearing state settled +
saved before sync-back — Pass 1A) · desktop/in-process carry as before · background
web/wiki intake (`ukft_synapse.run_synapse_cycle`) is launched by
`aura_master.py:492` and appends `sensory_buffer.txt`, but is not a direct
turn-selection source · `ukft_spontaneous.SpontaneousSpeech` is called by
inner monologue (`ukft_inner_monologue.py:477`, `573-577`) and can publish
to `aura_output.txt`, but is idle/trigram/product-unvalidated rather than
the conversational turn path · `ukft_grammar.GrammarSkeleton` is invoked by
answer composition and spontaneous speech, but remains a lightweight shaper.
Ordinary conversation is not yet normalized; see
`AURA_CONVERSATION_NORMALIZATION_ROADMAP.md` for the staged failure-class
objective (CN0 first).

The original `AURA_BRAIN_GF_INTEGRATION_AUDIT.md` numbered audit is now
CLOSED in full (rev 8) — it remains the historical findings map, not open
work. Bounded integration is not equivalent to a perfectly unified
cognitive loop: the target loop remains behaviorally incomplete and
ordinary conversation is not yet normalized (see
`AURA_CONVERSATION_NORMALIZATION_ROADMAP.md`). ALL of
its numbered findings are now CLOSED, including the last one —
character-pack knob product decisions (Finding #14 CLOSED 24 Sept
2026: settled per-knob contract — birth-active, envelope-active,
persisted-only, dormant, floor-owned, dead-code — with
hostile-perturbation identity; zero production change). Already-closed field persistence, roleplay
observer lifecycle, roleplay person/relationship timing, bounded M14
episodic influence, and finding-#1 empty-state copyback (pending-slot
clears sync back as empty; missing root never deletes partition state)
remain closed. Finding #2 is likewise closed: the requested partition is
swapped into root before any ego is created or used on an API turn.
Finding #4 is likewise closed (21 Sept 2026): detectors propose against
non-persisting staged models and only the basal winner's decision-owned
effects commit post-selection (receipt
`tests/verify_finding04_transactional_writeback.py`). Finding #6 is
likewise closed (21 Sept 2026, re-review corrections 22 Sept 2026): the
assembled context bundle is classified (`current_user` CAUSAL, the rest
DUPLICATE, dead keys retired), person-attribute questions route through
the known-person gate into truthful held-fact answers or honest declines
(true M5 receipt plus ask/roleplay parity proofs in
`tests/verify_finding06_shadow_context.py`).
Finding #8 is likewise closed (22 Sept 2026): the lesson ledger is an
audit/history + review source, never a second truth source; parseable
corrections answer later VERIFY provisionally via held beliefs
(graphless too), person corrections surface via best-match recency
without erasure, contested claims still route to confirm/cancel, and
banked-only text says exactly that (receipt
`tests/verify_finding08_lessons_correction.py`).
Finding #9 is likewise closed (22 Sept 2026, re-review 22 Sept
2026): belief trust and people importance are retained
ADVISORY-HISTORY — computed, persisted, test-readable, with zero
production BEHAVIORAL readers (repo-wide structural pins + hostile-
perturbation identity on every live seam); Finding #10 adds one
bounded reporting/accounting reader that classifies durable trust
mutations without influencing cognition or selection (receipt
`tests/verify_finding09_trust_importance.py` now included in
Finding #10 packet with narrow exception).
Finding #10 is likewise closed (22 Sept 2026, re-review 22 Sept
2026): the `memory_writes` journal is now truthful: before/after
partition-bytes diff reports durable mutations (clears, shrinkage,
equal-size replacements, content identity) with owner-aware fact
identity (`(person_key, predicate)`) and benign-rewrite suppression
(TS-only, N-only); atomic same-user receipt/counters inside
`_ask_lock`; truthful counters (facts_learned, threads_shared,
threads_closed, lessons_banked) via shared `_apply_write_counters()`
in ask/roleplay; observer gated on non-empty writes; legacy `type`
vs authoritative `kind` — receipt
`tests/verify_finding10_memory_writes_journal.py` (29 ARMs,
86 checks).

## MODULE ORPHANED (present, no caller on any live path)

`ukft_directed_synapse` has no live caller in the current grep evidence.
`aura_diagnostic.py` is operator-run, not turn-called; classify it as a
tool, not a lobe.

## OUTPUT ORPHANED (module runs, its output is never read downstream)

`run_discovery` → `discoveries.txt` · DMN/dream narrative → logs (except
the 15-min thought-topic check) · `aura_vocal_manifest.py` is launched by
master (`aura_master.py:472`) and tails vault/cortex, but emits console
manifest lines only; no decision path reads those lines ·
`cognitive_observatory.html`/pngs (artifacts, no `.py` importer) · one-shot
dev scripts (spent by design).

## BACKGROUND RUNNING BUT NON-CAUSAL (thread runs, output lands nowhere causal)

Cerebellum · entropy · hippocampus (episodes bypass it) · parietal (no
importer) · sleep/dream/ambient loops beyond their gated outputs · trigram
generator rebuild (used by idle spontaneous speech, not the selected
conversational answer path).

## WRITEBACK ONLY (persisted, never re-read for decisions)

Identity reinforcement returns · `DriveState.adapt` effects · web/wiki/PDF
accretion between rebuilds · growth readouts beyond mirror briefs.

## LEGACY DOMINANT (old system still owns the path)

Thalamus→cortex→vault chain (turn still ranks vault directly after M1-M4
gates) · engine template voice · boot TTS/presence/motor lobes off the API
path · remaining fixed selection hierarchy + saliences.

## ARCHITECT DECISIONS STILL REQUIRED

1. Field graph: make edges causal to recall (indexed, M5-tested) or
   permanently label the field display-only.
2. Trigram speak path: wire with causal test or delete the generator claim.
3. Gist: schedule with ownership (M11) or strike "nightly" from the spec.
4. Discord: deploy-proof (M9) or keep hermetic-only label.
5. UI: keep Tkinter IPC face, or bless Discord as the sole channel.
6. Character-pack knobs: SETTLED 24 Sept 2026 (Finding #14 — per-knob
   product contract with fail-closed regression; dormant knobs stay
   dormant until an Architect-tasked M5 pass says otherwise).
7. Production architecture: exact thin-client, encrypted local vault,
   server-brain, hosting/model, and population-learning privacy design.

## NOT CURRENT CAPABILITIES

Conversation normalization is the active engineering stage (not a proven
capability): CN0 — Conversational Baseline + End-to-End M16 Trace is
COMPLETE as a diagnostic baseline (24 Sept 2026, zero production change;
report `AURA_CN0_CONVERSATIONAL_BASELINE_REPORT.md`), per
`AURA_CONVERSATION_NORMALIZATION_ROADMAP.md`. Headline result: the
emotion-triggered "I remember" dump did not reproduce (4/4 clean emotion
turns, only legitimate recall quotes); dominant baseline failures are
paraphrase-unstable recall routing and person/agenda state-carry misses.
Observability completion (24 Sept 2026): full winner -> grounded ->
stance-payload -> mouth-prompt -> final seam capture on all 30 turns;
stance seam E RULED OUT by payload comparison; prompt-construction clean
with zero issues; live-mouth F remains the isolated unmeasured boundary.
CURRENT IMPLEMENTATION PHASE: CN1 (not complete; no fix claimed).
Controlled family beta has not begun and is not public launch. The proposed
thin client, local encrypted personal vault/gatekeeper, private server-side
brain, opaque production storage adapter, and generalized population-learning
pipeline are future architecture targets, not implemented systems.


2026-09-23 — Finding #11 (personality / boundary authority) audited and closed. Explicit runtime authority established for each duplicated surface; profile operational for existing users; pack birth-only; executable floors preserved; unsupported pack knobs deferred rather than invented; no selector-causal claim added.

2026-09-24 — Finding #12 (amygdala causality) settled and closed: CAUSAL-BOUNDED on the desktop route — genuine amygdala backlog through real field physics moves selection dark to field (danger node 0.0829 crosses the 0.05 candidate threshold; single event 0.0138 stays dark); emotional log and mood tone proven non-inputs on the seam; NON-CONNECTED on the API route (no amygdala/hippocampus/STM path). Scope narrow by construction (field 0.5 displaces only dark 0.2); zero production change. Receipt `tests/verify_finding12_amygdala_causality.py`. Side observation recorded: per-boot SeenFilter dedup means identical repeated hippocampus lines stimulate once per amygdala boot (deliberate Phase 0.7 design, no change).

2026-09-24 — Finding #14 (pack-knob product decision) settled and closed: per-knob contract — name/personality/interests/seed-anchors birth-active; pet_names_at envelope-active (roleplay seam + post_check gate); max_forwardness/initiative persisted-only; voice_model/voice_temperature/question_back-value dormant (zero production readers); boundaries_overlay absent (global floor owns); identity-seed drive presets dead code. Hostile-knob perturbation identity proven through real birth; pack-file initiative/pet_names_at mirrors drift-guarded. Zero production change, zero behavior change. Receipt `tests/verify_finding14_pack_knob_contract.py`. The original Brain↔GF audit has NO open numbered findings remaining. Side observations recorded: birth-greeting field tension/manifold phase vary run to run (engine physics jitter, proven knob-independent by clean-vs-clean control + interleaved 3v3 identity); pack birth name does not surface through the "What is your name?" probe (identity-template territory, out of scope).
