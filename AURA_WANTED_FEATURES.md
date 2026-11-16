# AURA WANTED FEATURES — NOW / NEXT / LATER / FUTURE

Updated: 24 Sept 2026
Class: AUTHORITATIVE CURRENT

This file lists current work. Completed NOW items are marked with dated proof.

## NOW — Brain Integration

1. ~~Build the proof system that tells us whether a brain part genuinely affects
   the chosen answer. (M5)~~ DONE 19 Sept 2026 — `tests/m5_harness.py` +
   `tests/verify_m5_causal.py` ship in `tests/run_all.py`; temporal support
   and the reasoning candidate are proven causal, observer/mood proven
   non-causal. M5 stays permanent law for every later change.
   Technical meaning: a feature intended to affect selection needs an
   integration test where changing that feature's output can change or guard
   the selected response.

2. ~~Stop unrelated memories from winning. (M1)~~ DONE 19 Sept 2026 —
   `m1_relevance`/`m1_filter_relevant` in `aura_bridge.py` + shipping
   `tests/verify_m1_relevance.py`: vault anchors compete only on
   query-coverage, title-aboutness, phrase-coherence, or multi-word
   topicality against the resolved query (thread-topic basis for
   contentless follow-ups); M5 receipt proves the gate guards/flips
   the winner. Saliences unchanged.
   Technical meaning: vault/recall candidates must pass relevance and
   coherence gates before they can beat the current question.

3. ~~Make the current conversation/thread strong enough to suppress unrelated
   memories. (M2)~~ DONE 19 Sept 2026 — `m2_thread_state` /
   `m2_filter_thread` in `aura_bridge.py` + shipping
   `tests/verify_m2_thread_suppression.py`: M1-admitted but off-thread
   vault anchors are withdrawn (explicit pivots and query-named anchors
   always escape); M5 receipt proves the suppression guards/flips the
   winner. Saliences unchanged, M1 meaning preserved.
   Technical meaning: active topic, resolved references, and thread state can
   negatively suppress off-topic memory resonance.

4. ~~Let actual reasoning/proof beat irrelevant memory. (M3)~~ DONE 19 Sept
   2026 — pre-existing priority (0.95 reasoning, support zeroed under
   proof, intent-gated gaps) audited, preserved, and locked by shipping
   `tests/verify_m3_reasoning_priority.py`; one real gap closed (narrow
   exemption: VERIFY/COMPARE/WHEN gaps yield to explicitly requested
   held vault answers) with two M5 receipts. Saliences unchanged.
   Technical meaning: proof-backed answers and honest gaps can suppress
   tempting but irrelevant vault recall.

5. ~~Feed real context, current person and conversation state into answer
   selection. (M4)~~ DONE 19 Sept 2026, HARDENED 20 Sept 2026 —
   `m4_selection_state` derives a bounded selection state from existing G7
   dialogue/thread/open-question, resolved-reference, topic-switch,
   query-mode, and current-person evidence. Strong dialogue evidence can raise
   only the context candidate from 0.75 to 0.86. Ownership is eligibility:
   incompatible first-person autobiographical anchors are withdrawn from vault
   competition even when no legacy voice trigger fires; M3's held-memory
   exemption is cancelled and the honest gap stands, with no context filler.
   Released explicit recall speaks only from the eligible same-anchor set.
   This is compatibility evidence, not authenticated historical ownership.
   Three hardened M5 receipts prove conversation, current-person, and
   voice-less eligibility winner influence.

6. Add contradiction handling. (M13) — DONE / PROVEN 20 Sept 2026.
    What shipped: query-relevant R3 contradictions guard answers —
    confident compare/describe proofs become grounded conflict (dedicated
    conflict candidate outbids reasoning), and only vault anchors
    whole-word-carrying the contested proposition are withdrawn. Proven
    scope is structured R-track records (opposite/reversed comparisons,
    is_a cycles, has-vs-lacks); arbitrary vault prose without a
    whole-word participant match is an explicit documented boundary, and
    memory-correction/supersession policy is still open.

 7. ~~Integrate GF experience into the original UKFT brain.
      (GF EXPERIENCE ↔ OLD BRAIN INTEGRATION)~~ DONE as an audit stage
      24 Sept 2026 — bounded, M5-proven passes (set 20 Sept 2026 from
      the read-only Brain↔GF audit; closed with the audit itself).
     Technical meaning: real conversation / episodic experience enters the
     existing UKFT brain lifecycle — GF experience → original UKFT brain →
     existing brain lifecycle → later retrieval — instead of living only in
     separate GF files used around the selector. Start narrow.
     Pass 1 DONE 20 Sept 2026 (`_hearing_ingest` + shipping
     `tests/verify_brain_gf_pass1.py`): post-selection hearing through the
     real thalamic gate, retrievable in-process with G7/episodic wiped.
     Pass 1A DONE 20 Sept 2026 (per-user restore + post-hearing
     heartbeat/persist in `ask()`/`roleplay()`, edge-preserving
     `field_state.txt`, shipping `tests/verify_brain_gf_pass1a.py`):
     the bridge survives real API turn boundaries with cross-user
     isolation. Desktop double-hear documented, not redesigned; API
     background lobes (sleep/decay) still absent.
     Pass 2 DONE 20 Sept 2026 (brain-owned `cognitive_stance` +
     `build_prompt_from_stance` as the roleplay route's only prompt
     entry, shipping `tests/verify_loop_pass2.py`): person,
     relationship, personality, and conversational understanding combine
     into a current understanding/stance/intent result the mouth phrases
     instead of re-deriving. Desktop master assembly out of scope,
     unchanged.
     M14 DONE 21 Sept 2026 adds the first provenance-controlled episodic
     contribution to selection and the stance; it does not complete all
     remaining GF-system integration.

8. ~~Decide how episodic memories boost or suppress answers. (M14)~~ DONE /
    PROVEN 21 Sept 2026 — `m14_filter_recall` governs the existing diary-
    recall reasoning path after M4 and before selection. Topic/person-trace
    evidence must be visible and whole-token relevant; reply, contradicted,
    singular wrong-owner, and active-thread duplicate evidence is suppressed.
    Relevant admission and duplicate suppression have M5 winner receipts in
    `tests/verify_m14_episodic_influence.py`. No candidate or salience was
    added. Only selected eligible provenance enters `cognitive_stance`, and
    the mouth receives it as event memory rather than objective proof.

9. ~~Make the viewer prove which systems actually influenced the answer.
    (M16)~~ DONE / PROVEN / HARDENED / ACCEPTED 21 Sept 2026 — the real `BrainModule.roleplay()`
    route emits one partitioned lifecycle and explicit same-turn receipts;
    viewer/export distinguishes RAN, OUTPUT PRODUCED, OUTPUT USED, and
    INFLUENCED DECISION without inferring causality from wording. Existing M5
    bases govern influence, legacy branches without dedicated proof stop at
    OUTPUT USED, and observer-off behavior is identical.

The original numbered brain-integration audit is fully closed (Finding #14
last, 24 Sept 2026). Pass 1/1A, Pass 2, M14, and M16 are bounded completed
milestones, not proof that the whole target cognitive loop is integrated.
No numbered brain-integration objective remains unfinished; the active NOW
objective is Conversation Normalization below.

### Original-Audit Findings (ALL CLOSED 24 Sept 2026)

The original `AURA_BRAIN_GF_INTEGRATION_AUDIT.md` remains the map; do not create
a replacement census. Finding #1 is CLOSED 21 Sept 2026 (pending-slot
empty-state copyback, see `AURA_GF_INTEGRATION_EMPTY_STATE_COPYBACK_REPORT.md`).
Finding #2 is CLOSED 21 Sept 2026 (partition-before-ego vault ownership,
see `AURA_GF_INTEGRATION_PARTITION_OWNERSHIP_REPORT.md`).
Finding #4 is CLOSED 21 Sept 2026 (transactional writeback: non-persisting
staged proposals, winner-gated post-selection commit, losing effects leave
stores byte-identical, selected effects commit exactly once, turn-owned
experience writeback intact,
see `AURA_GF_INTEGRATION_TRANSACTIONAL_WRITEBACK_REPORT.md`).
Finding #6 is CLOSED 21 Sept 2026 (shadow assembled-context fields
classified: `current_user` CAUSAL, the rest DUPLICATE, dead keys retired,
see `tests/verify_finding06_shadow_context.py`).
Finding #8 is CLOSED 22 Sept 2026 (lesson ledger as audit/history +
review source, never a second truth source,
see `tests/verify_finding08_lessons_correction.py`).
Finding #9 is CLOSED 22 Sept 2026 (belief trust and people importance
retained ADVISORY-HISTORY with zero production behavioral readers,
see `tests/verify_finding09_trust_importance.py`).
Finding #10 is CLOSED 22 Sept 2026 (truthful `memory_writes` journal via
partition-bytes diff, see `tests/verify_finding10_memory_writes_journal.py`).
Finding #11 is CLOSED 23 Sept 2026 (personality / boundary authority,
see `AURA_FINDING11_REPORT.md`).
Finding #12 is CLOSED 24 Sept 2026 (amygdala causality: CAUSAL-BOUNDED
on desktop, NON-CONNECTED on API,
see `AURA_FINDING12_AMYGDALA_REPORT.md`).
Finding #14 is CLOSED 24 Sept 2026 (pack-knob product decision:
settled per-knob contract — birth-active, envelope-active,
persisted-only, dormant, floor-owned, dead-code — with
hostile-perturbation identity through real birth; zero production
change; see `AURA_FINDING14_PACK_KNOB_CONTRACT_REPORT.md` and
`tests/verify_finding14_pack_knob_contract.py`).

There are NO remaining original-audit decisions. The original
Brain↔GF audit is fully closed. No further consolidation passes
until explicitly tasked.

Do not reopen already-closed per-user field restore/persistence, roleplay
observer lifecycle, roleplay current-person/relationship temporal consistency,
bounded M14 episodic influence, finding-#1 empty-state copyback,
 finding-#2 partition ordering, or finding-#4 transactional writeback,
finding-#6 shadow-context, finding-#8 lesson-correction,
finding-#9 trust-importance, finding-#10 memory-writes-journal,
finding-#12 amygdala-causality, or finding-#14 pack-knob-contract
merely for cleanup.

## NOW — Conversation Normalization (ACTIVE STAGE from 24 Sept 2026)

Aura should simply talk normally. The completed brain-integration audit
(items 1–9 above plus ALL original-audit findings, now closed) is history,
not the active task. The working roadmap is
`AURA_CONVERSATION_NORMALIZATION_ROADMAP.md` (CN0 -> CN1 -> CN2 -> CN3 ->
CN4 -> CN5 -> CN6 -> CN7). CN0 — Conversational Baseline + End-to-End
M16 Trace — is COMPLETE (diagnostic baseline + observability completion,
24 Sept 2026, zero production behavior change; report
`AURA_CN0_CONVERSATIONAL_BASELINE_REPORT.md`). CURRENT IMPLEMENTATION
PHASE: CN1 (not complete; no fix claimed). Use M16 to diagnose real
conversations and preserve FIX THE MECHANISM, NOT THE SENTENCE. Each
genuine failure class should become a regression:

- random/inappropriate memory quotations and awkward memory insertion;
- abrupt topic resets, lost multi-turn context, repetition, and poor follow-up
  questions;
- formal/system-style phrasing;
- incorrect person/pronoun grounding;
- mouth divergence from brain-owned intent;
- emotional/social stance inconsistent with the actual interaction.

## NEXT STAGE — Controlled Family Beta Readiness

Family beta is a trusted multi-human failure-discovery stage, not public
launch. Minimum gates:

- conversation is normal enough that humans can evaluate Aura rather than
  constantly fight dialogue failures;
- per-user isolation is reliable;
- backup, recovery, and restore procedure is proven;
- several simultaneous users operate without state leakage;
- a controlled client/deployment route exists;
- the chosen channel's kill switch, rate, boundary, stranger, and age
  protections are proven.

The test mission includes contradictions, false corrections, multiple people,
similar names, pronoun ambiguity, slang, typos, affection, anger,
disappearing/reappearing, false "remember when" claims, repeated questions,
topic jumps, restart/reconnect, and concurrent-user behavior.

## PRODUCT READINESS — Family Beta To Public Scale

- M15 restore-to-temp/recovery proof and named ownership.
- M9 live deployment proof: kill switch, rate limits, stranger safety,
  boundaries, age handling as appropriate, and one-voice-per-box.
- M12 multi-user quotas, concurrency, leakage, and production-scale rules.
- Memory correction/supersession policy with authorization and logging.
- M10 sarcastic/personality kindness guard.
- M11 nightly gist scheduler ownership; no automatic-nightly claim before it.
- First-word latency optimization without allowing mouth output before a
  grounded brain decision.

M10, M11, perfect latency, and long-horizon growth do not automatically block
the earliest tightly controlled family beta unless another safety requirement
makes them necessary.

## LATER — Growth, Continuity, And Public Beta

- Gist-driven volunteered memory after M11.
- Long-horizon personality/relationship growth and stronger social
  consequences/behavioral continuity.
- Contradiction-aware self-repair dialogue.
- Optional field-edge-weighted recall only if M5 proves it useful.
- Model-swap/ablation testing showing persistent character belongs to Aura's
  architecture rather than merely the mouth model.
- Public-beta packaging, updates, monitoring, deletion/export, disaster
  recovery, and scale.

## FUTURE PRODUCT ARCHITECTURE — NOT BUILT

Conceptual direction: downloadable thin client/UI <-> local encrypted personal
Aura vault/gatekeeper <-> private server-side Aura brain. Keep proprietary UKFT
cognition server-side; expose no readable architecture-by-filename folder to
users; send only minimum bounded turn context. Individual autobiography stays
private per user, the shared brain is proprietary cognition/compute, and any
future population learning uses generalized/aggregated signals rather than a
central dump of raw memories.

## FUTURE — OPEN ARCHITECT DECISIONS

- Permanent prohibition vs future allowance of adult/explicit capability.
- GPU/hosted inference strategy.
- Cloud mouth/model choice.
- Aura-derived non-companion product scope.
- Exact long-term population-learning/privacy design.
- Upstream AURA ports only by explicit hand-port with changelog entry.
