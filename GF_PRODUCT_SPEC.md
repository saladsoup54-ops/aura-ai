# AURA GF Product Spec — Current

Updated: 24 Sept 2026
Class: AUTHORITATIVE CURRENT

## Product Vision

Aura GF is a companion who talks to her person, remembers him, and grows with
him while staying honest about what she is. She starts with a chosen
personality beginning and interests, begins as a stranger, builds rapport from
actual interaction, and preserves continuity across sessions and channels.

She is not human and must not claim human life, body, company, lab, or hidden
offline activity without evidence. Warmth is allowed. Fabricated history is
not.

The brain owns Aura's context, memory, identity and persistent state. The mouth
receives only the selected, grounded context required to phrase the current
response.

## Built

- M5 causal-influence harness: `tests/m5_harness.py` +
  `tests/verify_m5_causal.py` ship in `tests/run_all.py` (proven 19 Sept
  2026, hardened same day: fail-closed gate, independent identical
  fixtures). Proven: temporal vault_support modulation and the reasoning
  candidate (path-conditional) move the selected response; observer
  telemetry and mood tone do not move it on the tested path.
- M1 vault relevance gate: ranked anchors compete only when coherent
  with the resolved current query (proven 19 Sept 2026, saliences
  unchanged).
- M2 active-thread suppression: M1-admitted but off-thread memories
  are withdrawn inside an active unswitched thread; explicit pivots
  and query-named requests always release (proven 19 Sept 2026,
  saliences unchanged, M1 meaning preserved).
- M3 reasoning priority: proofs and eligible honest gaps outrank vault
  association (pre-existing mechanism audited and preserved); narrow
  exemption so explicitly requested held answers beat honest ignorance
  (proven 19 Sept 2026, saliences unchanged). Answer-bearing memories
  must cover the full substantive query residue, including the material
  predicates know/learned/read/absorbed even though M1 may treat those
  words as ordinary relevance noise. Phase 10 M4 preserves generic audit
  ownership while releasing answer-bearing specific recall.
- M4 real selection context: strong current-conversation evidence can beat a
  weaker associative fallback; factual-reference and topic-switch modes avoid
  momentum traps; incompatible first-person autobiographical memories are
  ineligible to answer as the current speaker, even without a legacy voice
  trigger, and fall back to honesty rather than filler. The answer,
  compatibility evidence, and spoken explicit-recall source must be the same
  memory anchor; this is not authenticated historical ownership. Proven
  through the real selector seam with three hardened M5 receipts.

- Per-user partitions and brain API.
- Character/personality packs under `characters/`.
- Personality beginnings: nerdy, shy, bossy, flirty, bold, gentle, playful,
  earnest, fierce, dreamy.
- Interest seeding and pack-based birth vault seeding.
- Stranger-first current-person/interlocutor binding.
- G7 conversation memory: both sides of the dialogue, reference resolution,
  continuation, and prompt context.
- M14 episodic influence: relevant lived-event recall may support the existing
  reasoning path, while reply, contradicted, wrong-owner, and active-thread
  duplicate evidence is withheld; selected provenance is labelled event
  memory, not objective proof.
- G8 rapport ledger: relationship depth from warmth/trust/distance/contact,
  dwell, hysteresis, absence cooling, and give-room cooldown.
- G9 current-person grounding: current user facts render as YOU, Aura facts as
  I, and other people as third person.
- Boundaries: global floor plus personality envelopes, explicit deflection,
  opt-outs, and kill-switch concepts.
- Immersive roleplay path with fallback.
- Observer telemetry, viewer monitor tabs, and diagnostics export. M16 proves
  the real roleplay route emits partitioned four-level evidence (RAN, OUTPUT
  PRODUCED, OUTPUT USED, INFLUENCED DECISION), and that viewer/export rejects
  unsupported influence claims. This is observer-only evidence; it does not
  alter Aura's answer. M16 is reviewed, hardened, and ACCEPTED 21 Sept 2026.
- Tkinter UI file IPC: UI writes `ui_input.txt`, core drains it, output returns
  through `aura_output.txt`.
- Discord adapter code.

## Partial

- Mouth/voice: useful when safe, but the brain's grounded answer is canonical
  and template fallback is expected.
- Mood/mirror: affects prompt texture and audit, but not proven as a selection
  gate.
- Web/wiki/PDF accretion: can add material, but it is not direct selection.
- Contradictions: held R3 contradictions guard query-relevant answers
  (grounded conflict instead of confident one-sided speech). No automatic
  truth decision: conflict stays conflict until a memory-correction policy
  exists.
- First-words latency: under about 2 seconds is a product target, not current
  architecture. The mouth must never begin substantive content before the
  brain has made and grounded its decision merely to fake low latency.
- Growth/gist: code exists, but automatic nightly operation is not proven.
- The original Brain<->GF numbered audit is complete (all findings closed,
  Finding #14 last, 24 Sept 2026). Bounded integration is not equivalent
  to a perfectly unified cognitive loop: Pass 1/1A, Pass 2, M14, and M16
  are bounded completed milestones, not full subsystem unification, and
  the target loop remains behaviorally incomplete.
- Conversational behavior is not yet normalized enough to claim normal
   human-level behavior or family-beta readiness. CURRENT DEVELOPMENT
   STAGE: Conversation Normalization (CN0 baseline + observability
   complete 24 Sept 2026, zero production change; current implementation
   phase CN1, not complete, no fix claimed).
   NEXT PRODUCT GATE: conversation normal enough for controlled human
   evaluation. See `AURA_CONVERSATION_NORMALIZATION_ROADMAP.md`.

## Code-Complete But Not Live-Proven

Discord adapter code exists, but live product deployment is not proven. Before
use with real users, Aura needs token/intent setup, age-gate, kill-switch,
rate limits, one-voice-per-box proof, stranger-safety verification, and current
boundary checks.

## Not Yet Built / Not Yet Proven

- M11 scheduler ownership proof for nightly gist.
- Restore-to-temp ownership proof (M15) as a required operating ritual.
- Sarcastic preset kindness guard.
- Multi-user production scale quotas/rate/concurrency rules.
- Controlled family-beta deployment and operating proof.
- Thin-client/local-encrypted-vault/private-server-brain production
  architecture.

## Conversation Normalization — Current Development Stage

The current behavioral objective is simple: Aura should talk normally. M16 should diagnose mechanisms,
not justify sentence patches. Important failure classes are inappropriate
memory quotations, topic resets, lost multi-turn context, formal/system-style
phrasing, repetition, wrong person/pronoun grounding, awkward memory insertion,
poor follow-up questions, mouth divergence from brain-owned intent, and an
emotional/social stance that does not fit the interaction. Each genuine class
should become a regression under FIX THE MECHANISM, NOT THE SENTENCE. The
staged engineering plan (CN0 -> CN7, CN0 complete, CN1 current) lives
in `AURA_CONVERSATION_NORMALIZATION_ROADMAP.md`. NOT YET CLAIMED: normal
human-level conversational behavior; family-beta readiness.

## Controlled Family Beta

Family beta is a small trusted testing stage, not public launch and not a claim
of product completeness. It can begin when conversation is normal enough for
humans to evaluate Aura, per-user isolation is reliable, backup/recovery/restore
is proven, simultaneous users are proven not to leak state, a controlled client
or deployment path exists, and the chosen channel's kill switch, rate,
boundary, stranger, and age protections are proven.

Its purpose is to let different humans expose failure classes missing from the
Architect/test distribution: contradictions, false corrections, multiple or
similar names, pronoun ambiguity, slang, typos, affection, anger, absence and
return, false "remember when" claims, repeated questions, topic jumps,
restart/reconnect, and concurrent-user behavior.

M10 personality-kindness hardening, M11 automatic gist, perfect first-word
latency, and long-horizon growth do not automatically block the earliest
tightly controlled family beta unless a concrete safety requirement makes one
necessary.

## Future Production Architecture — Not Current Capability

The conceptual product target is:

```text
downloadable thin Aura client / UI
                <->
local encrypted personal Aura vault / gatekeeper
                <->
private server-side Aura brain
```

Proprietary UKFT/cognitive architecture should remain server-side. Users should
not receive a readable folder exposing the system through separate people,
rapport, episodic, belief, field, or similar filenames. A future production
storage adapter may place those logical stores inside an opaque encrypted
database/container. Per-user autobiographical state remains isolated locally,
and only minimum bounded turn context crosses the network.

This architecture is not implemented today. The intended distinction is:

- individual Aura autobiography = private per-user state;
- shared/server brain = proprietary cognition/compute;
- future population learning = generalized/aggregated signals, not centralized
  raw user memories.

## Onboarding And Personality

The user chooses:

- Personality beginning, not permanent destiny.
- Interests, used as seeded knowledge and conversation hooks.
- Name, with a personality default available.
- Boundaries and current-person profile state.

Personality modulates stranger behaviour but never skips relationship earning.
Shy can be reserved, bossy can be direct, nerdy can infodump when invited, and
flirty/bold still obey stranger-first boundaries.

## Stranger-First Behaviour

Every non-Architect partition starts bound to its own `interlocutor` record.
Display name or later "call me" instructions attach to that record. Matching a
name from another partition never makes a stranger into the Architect.

Distance first, warmth earned. She can be kind at first contact, but not
intimate as if shared history already exists.

## Relationship Depth

Relationship depth is rapport-driven, not volume-driven. The current mechanism
is `ukft_rapport.py`: warmth, trust, distance, and contact produce stage and
heat. Contact volume alone does not create closeness.

Stages: STRANGER -> ACQUAINTANCE -> FAMILIAR -> CLOSE -> BONDED.

Once FAMILIAR was truly reached, absence decay alone never drops below
ACQUAINTANCE. Direct distance can cool the relationship. Devotion must follow
evidence, not user demand.

## Persistence And Memory

Historical events and provenance are preserved. Semantic memory, beliefs,
inferred claims, and graph edges may be corrected, superseded, decayed, or
deleted only under explicit logged policy. Never silently rewrite historical
events to make Aura's past cleaner.

Config versions and day-one seed identity remain visible as history. Growth can
append and supersede, not erase provenance.

## Boundaries

Preserve:

- Honest AI identity.
- No fabricated shared history.
- Consent wording exact.
- No sycophancy as a substitute for care.
- Stranger safety.
- Personality beginnings without boundary bypass.
- Deflect-not-lecture handling for explicit content under the current floor.

Future adult/explicit capability remains an OPEN Architect decision. Current
never-explicit floor remains in force until changed.

## Open Architect Decisions

- Permanent prohibition vs future allowance of adult/explicit companion
  capability.
- Future GPU/hosted inference.
- Future cloud mouth/model hosting.
- Whether Aura-derived non-companion products are in scope.
- Exact first-words implementation under the never-precede-brain constraint.
- Exact long-term population-learning/privacy design.

## Product Readiness Gates

Product readiness requires dynamic green gates, not fixed historic suite
counts. Controlled family beta uses the narrower gates above; public-scale
readiness additionally requires:

- all current shipping regression suites green;
- stress green;
- isolation green;
- relevant feature-specific checks green;
- live state clean;
- M5 causal proof for claimed brain-influencing features;
- Discord deploy blockers satisfied before public/live deployment;
- scheduler/ownership proof before claiming nightly gist.
- production packaging, updates, monitoring, deletion/export, disaster
  recovery, and scale proof.
