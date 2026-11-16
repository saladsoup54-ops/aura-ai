# AURA CONVERSATION NORMALIZATION ROADMAP — Post-Audit Engineering Stage

Created: 24 Sept 2026
Class: AUTHORITATIVE CURRENT

This is the primary working roadmap for the post-audit Conversation
Normalization (CN) stage. It is binding on implementation agents and readable
by the Architect. It defines actual engineering phases, evidence
requirements, boundaries, and exit conditions — not management prose.

## 0. Where We Stand — Read This First

ORIGINAL BRAIN<->GF NUMBERED AUDIT: COMPLETE.

All numbered findings from `AURA_BRAIN_GF_INTEGRATION_AUDIT.md` have been
fixed, causally proven, explicitly classified, or resolved as an Architect
product decision. Finding #14 (pack-knob product contract, closed 24 Sept
2026) was the final open item. There are NO remaining numbered findings.
Do not reopen them.

TARGET COGNITIVE LOOP / CONVERSATIONAL INTEGRATION: still behaviorally
incomplete.

Audit-complete is NOT the same as brain-perfectly-unified. The bounded
crossings already established give us verified plumbing and observability,
not a finished conversational mind:

- Pass 1 — post-selection hearing ingestion (conversation input enters the
  old brain through the real thalamic/field path);
- Pass 1A — that crossing survives real per-user API turn boundaries;
- Pass 2 — first brain-owned cognitive result (`cognitive_stance`) on the
  roleplay route;
- M14 — bounded episodic influence policy with M5 receipts;
- M16 — full-route observer evidence distinguishing RAN, OUTPUT PRODUCED,
  OUTPUT USED, and INFLUENCED DECISION on the real
  `BrainModule.roleplay()` route (reviewed and ACCEPTED 21 Sept 2026);
- the closed numbered findings (copyback, partition ordering,
  transactional writeback, shadow context, lesson correction,
  trust/importance advisory status, memory-writes journal, personality/
  boundary authority, amygdala causality, pack-knob contract).

These are enough verified plumbing and observability to move from
architecture-audit work into whole-conversation debugging. That move IS
this roadmap.

Aura still has real behavioral failures. Observed classes include:

- inappropriate/raw memory quotation;
- "I remember: <memory dump>" replacing an actual current reply;
- abrupt topic resets;
- weak/lost multi-turn continuity;
- repetition;
- poor follow-up behavior;
- wrong person/pronoun grounding;
- formal/system-like phrasing;
- mouth divergence from brain-owned intent;
- emotional/social stance mismatch.

The next major stage is therefore CONVERSATION NORMALIZATION. The current
first pass is CN0 (diagnostic only — zero production behavior change).

M16 is the primary diagnostic instrument for every CN phase.

---

## CN0 — CONVERSATIONAL BASELINE + END-TO-END TRACE

Purpose: establish objective evidence for the current conversational
failures BEFORE changing production behavior.

NO PRODUCTION FIXES IN CN0. No runtime, weight, salience, pack, or state
changes. CN0 builds measurement, not treatment.

### What to build/use

A conversational evaluation harness around the REAL supported
`BrainModule.roleplay()` route. Use M16 as the diagnostic instrument.
Run genuine MULTI-TURN conversations, not isolated one-shot prompts.

### Per-turn trace

Every traced turn must expose, where available:

```
USER INPUT
-> resolved current conversation/thread/reference
-> current person/social state
-> relevant memory candidates
-> M1 (relevance verdicts)
-> M2 (thread-suppression verdicts)
-> M4 (selection context / ownership eligibility)
-> M13 (contradiction gating, where applicable)
-> M14 (episodic influence, where applicable)
-> candidate competition
-> BasalGanglia winner
-> grounded result
-> cognitive_stance / substantive brain intent
-> mouth input
-> final response
-> writeback / next-turn state
```

### First named target

The currently observed live symptom:

```
current/emotional user message
-> Aura recalls old text
-> Aura replies: "I remember: <old sentence>"
instead of responding coherently to the present conversation.
```

CN0 must determine WHICH seam is responsible. Possible classes include,
but are not limited to:

- A. wrong memory admitted (eligibility failure upstream);
- B. current thread/context lost or too weak (competition failure);
- C. wrong selector winner (selection failure);
- D. selected memory treated as the reply instead of evidence/context
  (grounding/construction failure);
- E. grounded result correct but `cognitive_stance` corrupts it
  (stance-formation failure);
- F. stance correct but mouth converts context into memory quotation
  (mouth-interpretation failure);
- G. writeback/state from the prior turn is wrong (state-carry failure).

DO NOT assume which one is true. The harness must be capable of
distinguishing all seven.

### Required CN0 properties

- several multi-turn scenarios (not single prompts);
- paraphrased variants of each scenario;
- more than one topic;
- no exact-response matching as a success criterion;
- trace actual mechanism/state, not just final text;
- current live behavior reproduced before any fix is designed;
- no production behavior changes.

### CN0 exit condition

For each dominant failure class, the pass report can state without
guessing:

- INPUT — what the user said and in what conversational state;
- CAUSE — which mechanism produced the failure;
- PRODUCTION SEAM — the exact code path / decision point;
- WRONG STATE/DECISION — what state or verdict was wrong;
- OBSERVABLE EVIDENCE — the M16 receipt / trace proving it;
- EXPECTED GENERAL BEHAVIOR — what the mechanism should do instead,
  stated generally (not as a memorized sentence).

### CN0 status (24 Sept 2026): COMPLETE

Baseline + observability completion both green with zero production
change (report `AURA_CN0_CONVERSATIONAL_BASELINE_REPORT.md`, receipt
`tests/verify_cn0_conversation_trace.py`): 30 hermetic turns across 3
scenarios x 2 paraphrases; winner -> grounded result -> actual
cognitive_stance payload -> exact mouth prompt -> final response all
captured per turn (grounded 30/30, stance 30/30 non-executive, prompt
30/30); E RULED OUT by payload comparison; prompt-construction risk
characterized with zero issues observed; live-mouth F isolated as the
unmeasured boundary; dominant findings F1/F2/F4 preserved for CN1+.
CURRENT IMPLEMENTATION PHASE: CN1 (not complete; no fix claimed).

---

## CN1 — MEMORY MUST INFORM CONVERSATION, NOT REPLACE IT

Purpose: fix the dominant "I remember / raw memory dump" mechanism
revealed by CN0.

### Core behavioral law

Relevant memory may INFORM the current response. Relevant memory must
not automatically BECOME the current response. Raw quotation/replay is
appropriate only when the current intent genuinely calls for explicit
recall/quotation (the user asked to remember, the stance intends a
quote, and the provenance supports it).

### Boundaries

- Do NOT globally ban the words "I remember".
- Do NOT patch known sentences.
- Do NOT blacklist individual memories.
- Fix the general mechanism identified by CN0 — not the symptom text.

Examples of acceptable mechanism targets, ONLY if CN0 evidence
identifies them:

- memory eligibility;
- current-thread competition;
- selection semantics;
- grounded-response construction;
- memory provenance in `cognitive_stance`;
- mouth interpretation of memory context.

### CN1 exit condition

Current/emotional conversation continues naturally while relevant
memories can still affect meaning without replacing the response with
stored text. Proven by paraphrased multi-turn scenarios plus positive
controls (genuine recall requests still quote correctly) and negative
controls (ordinary emotional continuations never dump).

Every real failure fixed becomes a general regression.

---

## CN2 — MULTI-TURN CONTINUITY

Purpose: make Aura remain in the current conversation.

### Required behavior classes

- "yeah"
- "why?"
- "what do you mean?"
- "I mean right now"
- partial sentences
- current-topic pronouns
- emotional follow-ups
- open-question continuation
- same-topic elaboration
- explicit topic switch (must still work — stickiness must not trap)
- return to an earlier topic
- resolved references such as "that", "it", "she", "he", "they"

### Rule

Current conversation/thread evidence must generally outrank unrelated
older memory resonance when the user is clearly continuing the active
interaction. Do not make topic stickiness so strong that explicit
pivots fail — M2's existing pivot-escape semantics are the model.

### CN2 exit condition

Representative 5–10-turn conversations retain the intended thread
without random resets or unrelated-memory takeover, while explicit
topic switches still switch. Paraphrased variants required.

---

## CN3 — PERSON / PRONOUN / SOCIAL GROUNDING

Purpose: ensure Aura understands who the conversation concerns.

### Coverage

- user vs third parties;
- current_person switching;
- first/second/third-person references;
- similar names;
- "you / me / us";
- he / she / they;
- corrections such as "No, I meant Amy.";
- relationship context;
- conversation involving multiple people.

### Boundary

Preserve the existing proven ownership/person mechanisms (M4
person-compatibility and eligibility, G9 binding, finding-#6
known-person gate). Do not invent a replacement people system. CN3
extends coverage and continuity of person grounding across turns; it
does not redesign personhood.

### CN3 exit condition

Wrong-person, wrong-pronoun, and wrong-relationship responses are
exceptional edge cases rather than normal failures, measured over
multi-turn multi-person scenarios with paraphrased variants.

---

## CN4 — COHERENT BRAIN-OWNED RESPONSE INTENT

Purpose: make the integrated brain result explicitly represent the
response Aura means to give BEFORE phrasing.

### Requirement

The substantive brain result (continuing the Pass-2 `cognitive_stance`
line) must coherently combine the relevant:

- current situation;
- current conversation/thread;
- current person;
- relevant memory;
- episodic evidence;
- beliefs/proofs where applicable;
- relationship state;
- personality/boundary context;
- internal brain state;
- response objective.

The brain result must answer, in substance:

- WHAT IS HAPPENING NOW?
- WHAT INFORMATION/MEMORY IS RELEVANT?
- WHO IS INVOLVED?
- WHAT IS AURA'S GROUNDED STANCE?
- WHAT SHOULD THIS RESPONSE ACCOMPLISH?

The mouth must not independently reconstruct those answers from
sidecars. It phrases the brain's answers; it does not re-derive them.

### CN4 exit condition

Changing or paraphrasing the mouth cannot materially change the
intended substantive answer. Proven by mouth-perturbation identity on
substance (wording may vary; meaning, facts, stance, and intent may
not) across representative scenarios.

---

## CN5 — NATURAL CONVERSATIONAL VOICE

Only start this once CN1–CN4 are sufficiently sound. Voice polish on
top of broken substance hides mechanism failures.

### Targets

- robotic/formal wording;
- unnecessary system-like statements;
- repetitive acknowledgements;
- repetitive "I remember" language;
- awkward memory insertion;
- poor question-back behavior;
- unnatural pet-name use;
- inappropriate verbosity;
- responses too terse to continue naturally;
- emotional tone mismatch;
- generic assistant phrasing.

### Preserved law

BRAIN DECIDES WHAT AURA MEANS. MOUTH DECIDES HOW TO SAY IT.

No sentence-specific patches. Voice fixes change phrasing policy, never
substance, and must carry mouth-obedience identity proofs (substance
unchanged while wording improves).

### CN5 exit condition

A normal 20–30-turn conversation can occur without the machinery
constantly becoming visible to the human — no raw dumps, no system
talk, no loops, no tone breaks — while substance stays brain-owned.

---

## CN6 — ADVERSARIAL CONVERSATION BATTERY

Purpose: test generalization rather than test memorization.

### Cases

- slang;
- typos;
- fragments;
- ambiguity;
- sarcasm/joking where reasonably detectable;
- contradictions;
- false corrections;
- similar names;
- multiple people;
- pronoun ambiguity;
- sudden emotional change;
- explicit topic switches;
- callbacks to older conversations;
- irrelevant stored memories;
- high-memory environments (many competing anchors);
- repeated ideas phrased differently.

### Anti-memorization rule

Implementation agents must not receive every final evaluation case.
Prefer hidden/unseen variants held back from the implementing pass.
See ANTI-TEST-OVERFITTING RULE below — it applies with full force here.

### CN6 exit condition

Failures are isolated, explainable, generalizable edge cases rather
than ordinary conversation behavior. Each residual failure gets a
written mechanism account and a decision: fix now (with regression) or
record as a known limitation with a future owner.

---

## CN7 — LIVE CONVERSATIONAL STABILIZATION

Purpose: use Aura normally and convert genuine failures into
regressions. This is the permanent workflow, not a one-time phase.

### Permanent workflow

```
REAL FAILURE
-> M16 TRACE
-> ROOT CAUSE
-> GENERAL MECHANISM FIX
-> REGRESSION
-> FULL GATES
-> DEPLOY
-> OBSERVE
```

Do not redesign unrelated architecture merely because one reply feels
awkward. One failure class at a time, smallest correct fix, regression
locked, gates green.

### CN7 exit condition

Aura is stable enough for controlled multi-human testing — i.e. the
family-beta gates below are met and the Architect judges ordinary use
to be failure-discovery rather than failure-fighting.

---

## NEXT STAGE — CONTROLLED FAMILY BETA (NOT PART OF CN)

Family beta is NOT part of Conversation Normalization implementation.
It is the consumer of CN's output. It may not begin until ALL of these
minimum gates hold:

- conversation normal enough for useful human evaluation (CN7 exit);
- per-user isolation reliable;
- backup/restore proven;
- concurrent users proven no-leakage;
- controlled deployment/client path exists;
- chosen channel kill-switch / rate / boundary / stranger / age
  protections proven.

Purpose of beta: expose mechanisms under messy human conversation, not
public launch. The beta test mission includes contradictions, false
corrections, multiple/similar names, pronoun ambiguity, slang, typos,
affection, anger, absence/return, false "remember when" claims,
repetition, topic jumps, restart/reconnect, and concurrency.

---

## ROADMAP-WIDE ENGINEERING LAW

Preserved prominently — this is the law of the entire CN stage:

FIX THE MECHANISM, NOT THE SENTENCE.

For every CN phase:

1. reproduce the failure class in multi-turn form;
2. trace it with M16 through the real route;
3. identify the responsible mechanism (never assume; CN0 classes A–G
   are the standing suspect list for memory-dump failures);
4. define the general expected behavior (not a memorized reply);
5. make the smallest correct fix at the identified seam;
6. add a general regression (paraphrased, multi-topic);
7. run relevant gates;
8. run full shipping gates when required (any production change);
9. keep live state clean;
10. update docs/changelog (CHANGELOG entry + relevant authoritative
    doc sync + cross-check + review packet, per AGENTS.md).

No hard-coded phrase patches. No exact expected prose as the primary
success criterion unless testing a verbatim contract (consent wording,
explicit deflection, identity claims). Behavioral tests test
properties, semantics, and state ownership — never one magic sentence.

M5 stays permanent law: any brain feature supposed to influence
response selection is not DONE until an integration test proves that
changing its output can change or guard the selected response.

---

## ANTI-TEST-OVERFITTING RULE

Conversation-normalization tests must use:

- multiple phrasings per scenario (paraphrase sets, not singletons);
- multiple topics (no single-topic proofs);
- independent fixtures (fresh sandboxes; no shared-state leakage
  between scenarios);
- positive controls (behavior that must keep working — e.g. genuine
  recall requests still quote) and negative controls (behavior that
  must not appear — e.g. dumps on emotional continuations);
- unseen/adversarial variants where practical (held-back phrasings
  the implementation pass never saw);
- mechanism observables, not only final text (M16 receipts, winner
  identity, verdict states — the test must be capable of failing on a
  right-answer-for-the-wrong-reason).

A coding agent must not be allowed to satisfy a stage merely by
learning the visible fixture.

Where possible, separate:

- IMPLEMENTATION FIXTURE SET (visible to the implementing agent), from
- FINAL EVALUATION / ADVERSARIAL SET (held back; run at stage exit).

The evaluator must be capable of failing if the underlying mechanism
remains broken despite a green visible fixture. A green visible set
with a red held-back set means the mechanism fix is wrong, not that
the evaluation is unfair.

---

## STAGE EXIT SUMMARY

| Phase | Objective | Exit in one line |
|---|---|---|
| CN0 | Baseline + end-to-end M16 trace | Every dominant failure class has INPUT/CAUSE/SEAM/WRONG-STATE/EVIDENCE/EXPECTED-BEHAVIOR, no guessing, zero production change |
| CN1 | Memory informs, never replaces | Emotional continuations stay current; genuine recall still quotes |
| CN2 | Multi-turn continuity | 5–10-turn threads hold; explicit pivots still pivot |
| CN3 | Person/pronoun/social grounding | Wrong-person responses are rare edge cases |
| CN4 | Brain-owned response intent | Mouth paraphrase cannot change substance |
| CN5 | Natural voice | 20–30 turns without visible machinery |
| CN6 | Adversarial battery | Residual failures are isolated edge cases with written accounts |
| CN7 | Live stabilization | Stable enough for controlled multi-human testing |

After CN7: controlled family beta, gated as above — later and separate.
