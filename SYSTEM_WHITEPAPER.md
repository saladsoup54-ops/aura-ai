# SYSTEM WHITEPAPER — AURA GF Current Architecture

Updated: 24 Sept 2026
Class: AUTHORITATIVE CURRENT

## Executive Summary

Aura GF is a live companion organism built from the AURA UKFT engine. The
brain is not a language model. It is a Python/file-contract system with a
cognitive field, layered memory, proof-oriented reasoning, rapport, boundaries,
permissioned tools, partitioned users, and observer telemetry.

The brain owns Aura's context, memory, identity and persistent state. The mouth
receives only the selected, grounded context required to phrase the current
response. The mouth may phrase; it may not invent memory, identity, history,
reasoning results, or decisions.

The current integration problem is not a lack of modules. Aura has many newer
brain systems, but the old selection machinery still has too much control over
which response wins. Memory activation is not memory selection. Memory
selection is not reasoning. Reasoning is not response selection. Current
conversation/thread/social intent must be able to outrank irrelevant memory
resonance.

## Core Flow

1. Input arrives through terminal/UI file IPC, brain API, or adapter code.
2. The live loop writes sensory/input records and calls `SovereignEgo`.
3. `SovereignEgo` assembles candidate branches from tools, people, beliefs,
   teaching, self, agenda, context, reasoning, vault recall, field fallback,
   and dark fallback. M14 filters assertoric topic/person-trace diary recall
   on provenance, relevance, contradiction, singular ownership, and active-
   thread duplication before the existing reasoning candidate can compete.
4. `ukft_basal_ganglia` selects a winner from scored candidates.
5. The selected branch grounds the response.
6. The mouth/roleplay path may phrase the selected grounded content and must
   fall back when it cannot preserve the brain's facts. On the Brain API
   roleplay route, the mouth phrases a brain-owned cognitive stance
   (current understanding + person + relevant history + relationship
   stance + response intent, formed brain-side — Pass 2), never
   re-derived from sidecar files. When eligible diary recall actually wins,
   the stance carries bounded lived-event provenance labelled as event memory,
   not objective proof; the mouth does not reread episodic storage.
7. Writeback records the turn, episodic event, rapport evidence, gaps,
   observer events, and partition state. Post-selection, the turn's input is
   fed through the real thalamic sensory gate into the field, so GF
   experience enters the old brain under its own rules (Pass 1). On the
   Brain API route (`ask()` / `roleplay()`), the cleared singleton is
   re-owned per turn: the user's `field_state.txt` is restored after the
   partition swap, and after the turn the real field physics is stepped
   (fixed turn-boundary heartbeat) and persisted back before the
   partition sync (Pass 1A) — selection itself is already decided by then.

## Target Cognitive Loop (Intended End-State)

This section describes where the architecture is going, not what runs today.
The Core Flow above is current truth; this is the permanent target.

Aura is not intended to become a collection of GF modules independently
feeding a selector or an LLM prompt. The intended design is one integrated
cognitive loop:

USER → GF INTERPRETATION → ORIGINAL UKFT BRAIN → CURRENT UNDERSTANDING /
STANCE / RESPONSE INTENT → MOUTH → RESPONSE → BRAIN WRITEBACK → NEXT TURN

User input is a stimulus/experience. Relevant GF systems — current
conversation/context, people/current-person, episodic history, beliefs,
relationship/rapport state, personality, boundaries, current internal state,
relevant memories — contribute their relevant grounded information to the
original UKFT brain rather than each dumping its files into the mouth
prompt. The UKFT brain is the central integration point: it combines what
is happening now + what Aura remembers + who is involved + relationship
history + beliefs + personality/boundaries + internal brain state into a
coherent current result (what Aura understands is happening, what memories
are relevant, what she considers important, her grounded social/
relationship stance, what the response intends to accomplish). That
integrated brain result is handed to the mouth, which phrases it.

Brain vs mouth is unchanged: the brain decides what Aura means, the mouth
decides how to say it — wording, rhythm, style — and must not invent
memories, identity, relationship history, beliefs, facts,
emotional/relationship state, or substantive response intent. The completed
interaction then feeds back into the brain (experience/writeback) so it can
affect later cognition: user experience → GF interpretation → UKFT brain
integration → understanding/stance/intention → mouth phrasing → response →
brain writeback → next cycle.

Pass 1 proves only the first narrow crossing (conversation input entering
the old brain through the real thalamic/field path), and Pass 1A proves
that crossing survives a real per-user API turn boundary (restore →
turn → hear → settle → persist). Pass 2 proves the first narrow return
crossing on the roleplay route: person, relationship, personality, and
conversational understanding combine into a brain-owned stance the mouth
phrases instead of re-deriving. M14 proves a further bounded crossing:
eligible episode evidence can affect the existing reasoning competition and
selected event provenance can enter that stance, without a new episode
candidate or mouth-side diary read. This is still not the final architecture. Bringing
the remaining GF systems into the shared brain-centered loop is incremental
future work, each step proven structurally and causally under M5 law — not
a license to merge every subsystem at once. ONE ORGANISM, NOT ONE SELECTOR
SURROUNDED BY TWENTY DATABASES.

## M5 Proven Response-Selection Causal

Only these have M5 receipts proving their output can change or guard the
selected response (`tests/verify_m5_causal.py`, 19 Sept 2026, hardened
same day):

- Response competition/winner selection through the real
  `BasalGanglia.select`: perturbing candidates or context flips winners.
- Temporal vault_support modulation (2-C feeds 2-D).
- Reasoning candidate, path-conditional: a present proof (or honest gap
  where eligible) beats vault association 0.95 vs 0.8.
- M1 vault relevance gate (proven 19 Sept 2026): `m1_filter_relevant`
  admits only anchors coherent with the resolved current query
  (query-coverage, title-aboutness, phrase-coherence, multi-word
  topicality; thread-topic basis for contentless follow-ups). Changing
  the verdict guards/flips the winner per M5 receipt.
- M2 active-thread suppression (proven 19 Sept 2026):
  `m2_filter_thread` withdraws M1-admitted anchors incoherent with the
  G7 active thread (explicit pivots and query-named anchors escape).
  Consuming the suppression guards/flips the winner per M5 receipt.
- M3 reasoning priority (proven 19 Sept 2026): pre-existing 0.95
  reasoning candidate, support zeroed under proof, intent-gated honest
  gaps, hysteresis displacement — all audited, preserved, and locked
  by `tests/verify_m3_reasoning_priority.py`; plus a narrow exemption
  (VERIFY/COMPARE/WHEN gaps yield to explicitly requested held vault
  answers). Answer-bearing uses M1 content words plus an M3-specific
  preserved predicate set (`know`, `learned`, `read`, `absorbed`), so
  subject-only memory cannot answer those predicates. The narrow direct
  recall set remains remember/recall/memory/memories/vault. Existing
  Phase 10 M4 now preserves generic audit ownership while releasing
  answer-bearing specific recall. Two M5 receipts. Base saliences unchanged.
- M4 real selection context (proven 19 Sept 2026, hardened 20 Sept 2026):
  `m4_selection_state` consumes existing G7 dialogue/open-question/reference/
  topic evidence and current-person compatibility before `BasalGanglia.select`.
  Strong dialogue evidence bids context at 0.86 instead of 0.75; topic overlap
  or ellipsis alone remains weak. Ownership is memory eligibility, not ranking
  luck: a first-person autobiographical request is answerable only from an
  anchor that is itself answer-bearing and compatible (first-person wording or
  the current user's name/key/alias). Incompatible anchors are withdrawn from
  vault bidding/reinforcement/speech, the M3 held-memory exemption is cancelled
  for that turn, and the prior honest gap stands; owner-unproven bids no
  context. This is compatibility evidence, not authenticated historical
  ownership. Independent, manifest-equal receipts prove vault->context
  conversation influence, a current-person guard that changes vault->voice, and
  a voice-less current-person eligibility receipt that changes vault->reasoning.
- Mouth/LLM exclusion (proven non-influence): re-phrasing cannot move the
  decision; `manifest_thought` never invokes the mouth.

M5 proven non-causal to the current response-selection seam: observer
telemetry (OBSERVER ONLY) and mood/affect tone (ADVISORY on the tested
path; no claim about other future uses).

## Working / Connected / Functional But M5 Influence Unproven

These run, connect downstream by caller/contract evidence, and are
covered by module/integration suites — but none yet has an M5 receipt,
so none may be called M5-proven causal. Working does not mean proven
influential (CALLED != CONNECTED).

- Turn pipeline from input to winner branch to writeback.
- G7 conversation memory beyond the M4-proven subset: full prompt dialogue and
  wording remain working but not selection-causal by this receipt.
- G9 interlocutor binding beyond M4's narrow current-person recall ownership:
  YOU/AURA/other rendering and hidden activity guard retain prior status.
- Rapport ledger: current relationship-depth mechanism, replacing old
  volume-based depth rules.
- People, beliefs, lessons, self/agenda branches where selected.
- Episodic recall with reply-kind exclusions.
- R-track relation extraction, graph, inference, proof answers, honest gaps.
- Confirm-gated tools in the live loop.
- Partition serialization and test-proven isolation.
- Character/personality packs and seed loading.
- Product boundaries and explicit deflection.
- Tkinter UI file IPC: `Launch_Aura.bat` starts `aura_ui.py`; UI writes
  `ui_input.txt`; core drains it; output returns through `aura_output.txt`.

## Observer Only / Observability

Observer emitter/viewer/export is working observability infrastructure, not a
response-selection mechanism. It records and reports evidence states such as
RAN, OUTPUT PRODUCED, OUTPUT USED, and INFLUENCED DECISION. It may report
causal evidence from other systems, but it does not create causal influence and
must never itself be described as influencing Aura's answer unless future
architecture explicitly changes that and M5 proves it.

M16 (proven, hardened, reviewed, and ACCEPTED 21 Sept 2026) extends that
infrastructure across the real `BrainModule.roleplay()` route. The selector
leaves an inert same-turn receipt;
the API observer classifies it only after the response path has completed, and
the viewer/export validates explicit system receipts instead of inferring
causality from wording or animation. M1/M2 and selected legacy branches stop at
OUTPUT USED where no turn-specific causal receipt exists. M3/M4/M13/M14 and
old-brain field influence are promoted only on their already-proven conditions.
The basal winner is distinct from the downstream Pass-2 stance, and the mouth
is always downstream phrasing. Traces are partitioned by user and viewer/export
groups them by `(user_id, turn_id)`. Disabling telemetry bypasses all M16
classification/emission and leaves winner, grounded response, and writeback
unchanged.

## Partial Systems

- Mouth/voice reliability: template fallback is safe; local runner paths are
  not the source of truth.
- Attention: background thalamus/reticular/PFC paths run, but live turn
  selection does not fully consume them.
- Mood and mirror signals: useful prompt/advisory information, not proven
  selection gates.
- Contradictions: detected AND query-relevantly selection-gating since M13
  (20 Sept 2026) for structured R-track records; arbitrary vault prose and
  memory-correction policy remain partial.
- API tool path: can speak results without the same in-process motor consumer
  used by the live loop.
- Decay/forgetting: exists, but lacks turn-rehearsal integration.
- Web/wiki/PDF accretion: writes knowledge material, but is slow-loop and not
  direct turn selection.
- Idle spontaneous/trigram speech: can publish outside the normal answer path,
  but is not the selected conversational answer.

## Shadow / Non-Causal / Orphan Categories

These categories must be preserved when documenting architecture:

- WORKING / CAUSAL: output is consumed and can affect the selected response.
- PARTIAL: wired but incomplete, unreliable, or only partly consumed.
- SHADOW: computed or emitted but not consumed for decision-making.
- WRITEBACK ONLY: persisted for later or audit use, but not read back into the
  current decision path.
- BACKGROUND NON-CAUSAL: thread runs, but its output does not currently affect
  answer selection.
- OUTPUT ORPHANED: module runs and produces output that no decision path reads.
- MODULE ORPHANED: module exists with no live caller.
- LEGACY DOMINANT: old path still controls more of the response than newer
  intended brain systems.

Current examples: viewer/export telemetry is observer-only; identity
reinforcement returns are mostly writeback-only; several background lobes run
without causal selection impact; old vault resonance and hardcoded saliences
remain legacy-dominant.

## Product/Deployment Architecture Truth

Character packs exist. Discord adapter code exists, but live Discord deployment
is not proven. Do not claim Discord product readiness until token/intent,
age-gate, kill-switch, rate limits, one-voice-per-box, and stranger-safety
proof are complete.

Nightly gist code exists in `ukft_gist.py`, but scheduler ownership is not
proven. Do not claim automatic nightly operation until M11 is proven.

First words under about 2 seconds is a product target, not current architecture
law. The implementation is unresolved. The mouth may never begin substantive
content before the brain has made and grounded its decision merely to fake low
latency.

Current local/CPU/content floors remain in force. Future adult/explicit
capability, GPU/hosted inference, cloud mouth/model hosting, and Aura-derived
non-companion products are OPEN Architect decisions, not decided by this
whitepaper.

### Future Production Architecture Target - Not Built

The intended product direction must protect both Aura's proprietary cognitive
architecture and each user's private autobiographical state. The conceptual
target is:

```text
downloadable thin Aura client / UI
                <->
local encrypted personal Aura vault / gatekeeper
                <->
private server-side Aura brain
```

The UKFT/cognitive architecture should remain server-side rather than being
distributed to users. A production storage adapter may represent the current
logical people, rapport, episodic, belief, field, and related stores inside an
opaque encrypted database or container; users should not receive a readable
folder that exposes the architecture through those filenames.

This architecture does not exist today. Current Aura uses Python modules and
file contracts, with per-user state represented in filesystem partitions. A
future implementation must preserve per-user autobiographical isolation and
send only the minimum bounded turn context across the network.

The long-term privacy boundary is:

- individual Aura autobiography = private per-user state;
- shared/server brain = proprietary cognition and compute;
- future population learning = generalized or aggregated learning signals,
  never a central dump of raw user memories.

Exact encryption, hosting, GPU/model placement, retention, aggregation,
deletion/export, and population-learning privacy remain design work and/or open
Architect decisions.

## Memory / History Rule

Historical events and provenance are preserved. Semantic knowledge, beliefs,
inferred claims, and graph edges may be corrected, superseded, decayed, or
deleted only under explicit logged policy. Never silently rewrite historical
events to make Aura's past cleaner.

## Selection Frontier

Current answer selection still gives old memory association too much power.
The next architecture work is integration, not new surface features.

NOW requirements:

- M5 causal test harness (PROVEN 19 Sept 2026): `tests/m5_harness.py` +
  `tests/verify_m5_causal.py` prove whether a brain part genuinely changes
  or guards the selected answer. Exact seam: `SovereignEgo.manifest_thought`
  builds context-modulated candidates + `{vault_support, inhibited, m4}`, then
  `BasalGanglia.select` picks the winner; the mouth runs after selection
  and cannot move the decision. Proven causal: temporal vault_support
  modulation and the reasoning candidate (path-conditional). Proven
  non-causal: observer telemetry, mood/affect tone. Each later row states its
  own receipt status.
- M1 memory relevance/coherence gate (PROVEN 19 Sept 2026): ranked
  anchors must be about the resolved query before competing; the vault
  candidate is withdrawn when none are. Saliences unchanged.
- M2 negative suppression: active conversation/thread context suppresses
  irrelevant memory (PROVEN 19 Sept 2026 — off-thread M1-admitted
  anchors withdrawn; switches and named requests escape).
- M3 reasoning/proof priority: proof can suppress irrelevant vault
  recall (PROVEN 19 Sept 2026 — pre-existing priority preserved; one
  narrow gap-yields-to-memory exemption added).
- M4 real selection context (PROVEN 19 Sept 2026): bounded current-thread,
  current-person, and conversation-mode evidence participates in selection.
- M13 contradiction gating (PROVEN 20 Sept 2026): query-relevant R3
  contradictions guard answers instead of only being counted — a confident
  compare/describe proof intersecting the contested proposition becomes
  grounded conflict (reasoning bid withdrawn, dedicated conflict candidate
  wins), and only vault anchors whole-word-carrying the contested
  proposition are withdrawn. Proven scope is structured R-track records
  (opposite/reversed comparisons, is_a cycles, has-vs-lacks); arbitrary
  vault prose without a whole-word participant match is out of scope, and
  no memory-correction/supersession policy was decided. 11A hardening
  (same day): VERIFY conflicts use the same single shared rule — a
  has-vs-lacks record no longer blocks an is_a answer, while genuine
  is_a-cycle VERIFY conflicts still surface.
- GF EXPERIENCE ↔ OLD BRAIN INTEGRATION (audit stage COMPLETE 24 Sept
  2026 — bounded M5-proven passes; the target loop remains behaviorally
  incomplete, now owned by Conversation Normalization): real conversation / episodic experience enters
  the existing UKFT brain lifecycle — GF experience → original UKFT brain →
  existing brain lifecycle → later retrieval — instead of living only in
  separate GF files used around the selector. Start narrow. Pass 1 (20 Sept
  2026): post-selection hearing ingestion in `manifest_thought` through the
  real thalamic gate into the field — proven by
  `tests/verify_brain_gf_pass1.py`. Pass 1A (20 Sept 2026): the bridge
  survives real API turn boundaries — per-user field restore after the
  partition swap plus post-hearing heartbeat/persist before the sync-back
  in `ask()`/`roleplay()`, with an edge-preserving `field_state.txt` —
  proven by `tests/verify_brain_gf_pass1a.py` (same-user retrieval across
  fresh module instances, cross-user isolation, persistence-deleted dark
  control). Pass 2 (20 Sept 2026): the first brain-owned cognitive result
  on the roleplay route — `cognitive_stance` forms understanding, person,
  history, relationship stance, and response intent brain-side, and
  `build_prompt_from_stance` is the route's only prompt entry — proven by
  `tests/verify_loop_pass2.py` (person/relationship/personality causal
  proofs, mouth-obedience identity, grounded-fact negative control).
- M14 episodic influence policy (PROVEN 21 Sept 2026): the existing
  diary-recall reasoning answer is admitted only with visible, whole-token-
  relevant lived-event evidence; reply records, query-relevant R3 conflicts,
  singular wrong-owner evidence, and active-G7 duplicates are suppressed.
  Relevant admission and duplicate suppression have M5 winner receipts in
  `tests/verify_m14_episodic_influence.py`. No episode candidate or salience
  change was added. Only selected eligible provenance enters
  `cognitive_stance`; the mouth receives an event-memory caveat and performs
  no episodic read.
- M16 observer selection coverage (PROVEN/HARDENED/ACCEPTED 21 Sept 2026): the real roleplay
  route emits a complete per-user lifecycle and explicit four-level receipts;
  viewer/export shows which systems ran, produced output, had output consumed,
  or met an existing causal basis for influencing the selected answer. The
  observer remains non-causal and observer-off behavior is identical.

Whole-conversation work now proceeds under the Conversation Normalization
roadmap. M5 remains the required instrument; M1/M2/M3/M4/M13/M14/M16 are proven above.

## Current Roadmap

COMPLETED MILESTONES: M5 -> M1 -> M2 -> M3 -> M4 -> M13 -> GF/OLD-BRAIN
Pass 1 -> Pass 1A -> Target Loop Pass 2 -> M14 -> M16 ACCEPTED.

CURRENT STATE: the original Brain<->GF numbered audit is COMPLETE (all
numbered findings closed, Finding #14 last, 24 Sept 2026). The completed
bounded passes do not prove every GF sidecar is unified with the original
brain, and bounded integration is not equivalent to a perfectly unified
cognitive loop — the target loop remains behaviorally incomplete.
Conversation Normalization is now the immediate engineering objective, per
`AURA_CONVERSATION_NORMALIZATION_ROADMAP.md`; M16 is the primary diagnostic
instrument. Do not reopen closed findings.

The original Brain<->GF audit is closed and remains historical evidence. Its closed findings
stay closed: per-user field restore/persistence, roleplay observer lifecycle,
roleplay current-person/relationship temporal consistency, bounded M14
episodic influence, and (21 Sept 2026) finding #1 empty-state copyback —
allowlisted pending-slot clears sync back as empty state while missing root
files never delete partition state. Finding #2 is likewise CLOSED
(21 Sept 2026): the requested partition is swapped into root before any ego
is created or used on an API turn, with restore-on-early-failure in both
ask() and roleplay(). Finding #4 is likewise CLOSED (21 Sept 2026):
candidate-owned detectors propose against non-persisting staged models and
only the basal winner's decision-owned effects commit post-selection.
All of the following are now CLOSED (preserved as evidence, not open work):

- the `memory_writes` journal is now truthful: before/after partition-bytes
  diff reports durable mutations (clears, shrinkage, equal-size
  replacements, content identity) with owner-aware identity,
  benign-rewrite suppression, and atomic same-user snapshots/counters
  inside `_ask_lock`; truthful counters (facts_learned,
  threads_shared, threads_closed, lessons_banked) via shared
  `_apply_write_counters()` in ask/roleplay; observer gated on
  non-empty writes; reporting + persisted profile-accounting changed,
  cognition/selection unchanged except for the already-existing legacy
  relationship-depth bootstrap/fallback dependency (proven bounded) —
  closing audit Finding #10;
- the assembled context bundle is now classified: `current_user` is the
  only CAUSAL bundle field reaching selection (M4 person_bound/ownership,
  M3-10B/M14 eligibility — pinned at the seam in
  `tests/verify_finding06_shadow_context.py`); the remaining bundle keys
  are DUPLICATE (detectors/recall/stance read authoritative stores
  directly) and the dead `day`/`session`/`open_threads` keys were retired
  from `assemble()` — closing audit Finding #6;
- the lesson ledger is an audit/history + review source, never a second
  truth source: parseable corrections answer later VERIFY provisionally
  via held beliefs (graphless too), person corrections surface via
  best-match recency without erasure, contested claims route to
  confirm/cancel, banked-only text says exactly that — closing audit
  Finding #8;
- belief trust and people importance are retained ADVISORY-HISTORY:
  computed, persisted, and test-readable, with zero production
  BEHAVIORAL readers (proven repo-wide; Finding #10 adds one
  bounded reporting/accounting reader that classifies durable trust
  mutations inside `_trust_rows` without influencing cognition or
  selection) — closing audit Finding #9 with no behavioral change
  except that bounded journal classification;
- personality and boundary authority: Finding #11 closed 23 Sept 2026 — explicit layered authority established (profile operational for existing users; pack birth-only; executable floor/explicit/post-check/opt-out owners preserved; identity-seed birth-authoritative/self-modifying; unsupported pack knobs honestly classified in Finding #11 and settled by product contract in Finding #14 (closed 24 Sept 2026); no manager invented; no selector-causal claim);
- amygdala-only selector influence: Finding #12 closed 24 Sept 2026 —
  CAUSAL-BOUNDED on the desktop route (genuine amygdala backlog through
  real field physics moves selection dark to field once activation
  crosses the 0.05 candidate threshold; single event stays sub-threshold;
  emotional log and mood tone proven non-inputs on the seam),
  NON-CONNECTED on the API route (no amygdala/hippocampus/STM path);
  scope narrow by construction (field 0.5 displaces only dark 0.2),
  zero production change;
- character-pack knobs — Finding #14 closed 24 Sept 2026, settled product contract: name/personality/interests/seed-anchors birth-active; pet_names_at envelope-active via the personality-keyed table (real roleplay-seam + post_check reader); max_forwardness/initiative persisted-only with zero production behavioral readers; pack-file initiative/pet_names_at fields declared-but-unread mirrors (envelope table is the authority, drift-guarded); voice_model/voice_temperature/question_back-value dormant with zero production readers (runtime temperature authority: fixed mouth temp + ROLEPLAY_TEMPERATURE); boundaries_overlay absent with the global floor owning; identity-seed drive presets dead code; hostile-knob perturbation identity proven through real birth; zero production change, zero behavior change.

### A. Brain/Nervous-System Integration — COMPLETE (audit stage)

The original numbered audit is complete (all findings closed, Finding #14
last, 24 Sept 2026). No still-open audit findings remain; there is nothing
left to cross off. The closure record above is preserved as evidence.
Future brain-side changes are governed by the Conversation Normalization
roadmap and M5 law, not by the closed audit.

### B. Conversation Normalization — CURRENT ENGINEERING STAGE

Normal human conversation is now the major immediate behavioral objective.
CN0 — Conversational Baseline + End-to-End M16 Trace — is COMPLETE
(diagnostic baseline + observability completion, 24 Sept 2026, zero
production behavior change; report
`AURA_CN0_CONVERSATIONAL_BASELINE_REPORT.md`). CURRENT IMPLEMENTATION
PHASE: CN1 (not complete; no fix claimed), per
`AURA_CONVERSATION_NORMALIZATION_ROADMAP.md`. M16 is the primary
diagnostic instrument. Do not patch individual sentences. Diagnose the
mechanism and turn genuine classes into regressions: inappropriate memory
quotes, abrupt topic resets, lost multi-turn context, formal/system phrasing,
repetition, wrong person/pronoun grounding, awkward memory insertion, poor
follow-up questions, mouth divergence from brain-owned intent, and mismatched
emotional/social stance.

### C. Controlled Family Beta

Family beta is a trusted multi-human testing stage, not public launch. It may
begin when conversation is normal enough to evaluate Aura, per-user isolation
is reliable, backup/recovery/restore is proven, simultaneous users are proven
not to leak state, a controlled client/deployment path exists, and the chosen
channel's kill switch, rate, boundary, stranger, and age protections are proven.
Its purpose is to expose mechanisms under messy conversation: contradictions,
false corrections, multiple/similar names, pronoun ambiguity, slang, typos,
affection, anger, absence/return, false "remember when" claims, repetition,
topic jumps, restart/reconnect, and concurrency.

### D. Product Readiness And Later Scale

M15 restore/recovery proof, M9 deployment safeguards, M12 concurrency/scale
rules, memory correction/supersession policy, M10 personality kindness, M11
gist scheduling ownership, and first-word latency without pre-grounded speech
remain planned. M10, M11, perfect latency, and long-horizon growth are not
automatic blockers for the earliest tightly controlled family beta unless a
specific safety requirement makes them necessary.

Later objectives include gist-driven volunteered memory, long-horizon
personality/relationship growth, contradiction-aware self-repair, stronger
social consequences and continuity, optional field-edge-weighted recall only
with M5 proof, model-swap/ablation proof that persistent character belongs to
the architecture rather than the mouth, and public-beta packaging, updates,
monitoring, deletion/export, disaster recovery, and scale.

## Testing And Evidence

Dynamic rule: all current shipping regression suites, stress, isolation, and
relevant feature checks must be green before declaring work done. Historical
suite totals are dated evidence only.

Normal full-suite workflow:

```powershell
python tests/run_all.py
```

Stress and single-suite state-writing checks must run from safe temporary roots
with the required environment. Never run standalone `verify_isolation.py`
without its test-root environment; the Phase-4 incident proves why.
