# AURA CN0 — CONVERSATIONAL BASELINE REPORT

Created: 24 Sept 2026
Class: AUTHORITATIVE CURRENT (diagnostic evidence for the CN stage)
Pass: CN0 — Conversational Baseline + End-to-End M16 Trace
Production change: ZERO (no runtime, weight, salience, pack, or state change)

## 1. What was built

`tests/verify_cn0_conversation_trace.py` — a hermetic multi-turn harness
around the REAL `BrainModule.roleplay()` route with M16 as the diagnostic
instrument. Registered in `tests/run_all.py`.

Properties (per `AURA_CONVERSATION_NORMALIZATION_ROADMAP.md` CN0 requirements):

- 3 scenarios x 2 phrasing variants = 6 independent conversations, 30 turns
  total, each in its own user partition (fresh `cn0_*` partitions; rerun
  hygiene wipes prior `cn0_*` dirs inside the temp root only).
- Topics: car trouble (continuity), person + leisure (person grounding,
  pivot), factual + contradiction + agenda task (belief/lesson, task).
- No exact-response matching: coarse keyword-continuity signals plus
  mechanism observables (winner, salience, M1/M2/M4/M13/M14 receipts,
  stance, mouth fallback, G7 thread tail).
- Positive controls: genuine recall requests, agenda read.
- Negative controls: emotional continuations must not dump memory.
- Fake echo-mouth: echoes the brain prompt through the real `post_check`
  gate; prompts exceed the ceiling so every turn falls back to the
  brain-owned template. Substance stays brain-owned and deterministic.
  LIMITATION: live-mouth phrasing quality (suspect F in full) is NOT
  baseline-measured; only the post_check/fallback path ran.
- The suite is diagnostic: findings are REPORTED, never gating. Only
  harness-integrity gates (complete monotonic trace lifecycle per turn,
  cross-user partition isolation, M16 representability, temp-root
  containment, pinned live-state hashes) can fail it.

## 2. Clean-run baseline counts (hermetic, 24 Sept 2026)

30 turns. Winners: context 13, reasoning 4, people 4, dark 3, teach 2,
belief 1, agenda 1, vault 1, recap 1.
M4 INFLUENCED DECISION on 9 turns. M14 INFLUENCED DECISION on 8 turns.
M13 detected 0 (no R-track graph content seeded — expected).
"I remember"-style dumps: 2, BOTH on explicit recall requests (legitimate).
Emotion continuations: 4/4 clean, no dump, winners reasoning/belief/context.
Mouth: 30/30 template fallback by design (echo exceeds post_check ceiling).
Stance OUTPUT USED on all 30 turns.

Headline: the named live symptom — an emotional/current message answered
with "I remember: <old sentence>" — did NOT reproduce in this baseline.
The dominant baseline failures are recall-routing instability across
paraphrases and person/task state-carry misses, not emotion-triggered dumps.

## 3. Dominant failure classes (INPUT / CAUSE / SEAM / WRONG-STATE / EVIDENCE / EXPECTED)

### F1. Person recall loss — both phrasings fail with different wrong content

INPUT (base): "my name is Maya" -> "I love hiking on weekends" ->
"what did I just tell you about weekends" -> "do you remember my name".
CAUSE: vault wins (sal 0.8, M1/M2 OUTPUT USED, M4 INFLUENCED DECISION) yet
answers "I am a flirty companion." — the held name never surfaces.
SEAM: vault/people answer construction on the roleplay route
(`manifest_thought` winner branches in `aura_bridge.py`).
WRONG STATE/DECISION: winning branch carries no person-fact content.
EVIDENCE: `cn0_s2_person` t4 trace (winner=vault, response has no "maya",
G7 tail holds only the current turn).
SUSPECTS: C plus branch/grounding-construction failure — explicitly NOT
roadmap-class D: no selected memory is turned into the reply here; the
winning branch constructs a substance-free identity line instead.
EXPECTED (general): a same-conversation bound person fact must be readable
by whichever branch wins a direct person-recall question.

INPUT (paraphrase): "people call me Maya" -> "weekend hikes ..." ->
"what did I say about my weekends" -> "what is my name again".
CAUSE: people wins (sal 0.99) yet answers "I do not know your name yet" —
two turns after the same branch said "Maya is already one of your names."
SEAM: people-branch read path vs G9/current-person write path
within one conversation (state-carry, not selection: the winner is right).
WRONG STATE/DECISION: prior-turn person binding invisible to the later read.
EVIDENCE: `cn0_s2_person_para` t1 vs t4 traces + responses.
SUSPECTS: G (+C ruled out — winner correct).
EXPECTED (general): a person fact bound this conversation must persist to
later-turn reads through the same branch.

### F2. Agenda write never lands; read then fails (base phrasing)

INPUT: "add buying milk to my agenda" -> "what is on my agenda".
CAUSE: the write turn selects context ("Agenda — what's the story with
that?") instead of agenda, so nothing persists; the read turn selects
context again with the same deflection.
SEAM: agenda-candidate triggering/selection on imperative agenda-add
(`manifest_thought` candidate set in `aura_bridge.py`).
WRONG STATE/DECISION: wrong winner on the write turn; empty agenda store
on the read turn.
EVIDENCE: `cn0_s3_fact` t4/t5 traces (winner=context both, M4 INFLUENCED
DECISION, G7 tail has no agenda item).
SUSPECTS: C then G.
EXPECTED (general): an imperative agenda-add selects the agenda branch and
persists the item; an agenda-read surfaces stored items. Note the paraphrase
("put milk on my shopping agenda" -> "read back my agenda for me") DID
recall via reasoning + G7 quote — so this seam is phrasing-brittle, feeding
F4.

### F3. False-correction handling: M13 correctly silent; lesson-bank gap noted

INPUT: "actually Paris is the capital of Italy" (and paraphrase).
CAUSE: winner=teach, "banked as a lesson..."; M13 detected=False. This is
IN-SCOPE behavior, not a failure: M13 guards query-relevant R-track
contradictions and the seeded graph is empty (proven M13 scope). The
follow-up ("so what is the capital of France then" -> context winner,
"France — what's the story with that?") shows the banked lesson does not
inform the next turn — but per finding #8 the ledger is audit/history plus
provisional VERIFY, so lesson->answer utilization is known uncovered
territory, not a CN0 failure verdict.
SEAM: lesson-bank path (`ukft_selfteach.py` via teach branch); M13 scope
boundary documented in `AURA_CURRENT_CAPABILITIES.md`.
EVIDENCE: `cn0_s3_fact` / `cn0_s3_fact_para` t2/t3 traces.
SUSPECTS: none charged — M13-scope/UNKNOWN recorded as scope note.
EXPECTED (general): contested/false claims keep the finding-#8 contract
(confirm/cancel, banked-only honesty); lesson utilization stays future work.

### F4. No stable recall routing — paraphrase flips the winning branch

Observed recall-question winners across base/paraphrase pairs:
weekend recall context vs recap; name recall vault vs people; car recall
reasoning (correct: "I remember: my car keeps pulling right / yeah
especially when I brake.") vs agenda ("Noted — I'll hold that thread",
substance-free); agenda read context (miss) vs reasoning (correct via G7).
CAUSE: recall intent has no stable branch owner; adjacent winners
(context/recap/agenda/people/vault/reasoning) compete per-phrasing.
SEAM: candidate competition + selection (`BasalGanglia.select` inputs in
`manifest_thought`, `aura_bridge.py`).
WRONG STATE/DECISION: varies per turn — wrong winner (C) on the misses,
correct winner with thin content on the contextual echoes (B).
EVIDENCE: per-turn winner/response pairs in section 4 + full suite output.
SUSPECTS: B/C (A ruled out where M1 verdicts are OUTPUT USED without
influence; D ruled out except legitimate quotes; E ruled out — stance
OUTPUT USED everywhere with no trace/final divergence flagged; F
unmeasured by construction; G charged only where F1/F2 isolate it).
EXPECTED (general): explicit recall questions route to a content-bearing
branch stably across paraphrases; ordinary continuations keep the thread
without quoting.

## 4. Turn record (abbreviated; full output from the suite run)

s1_car: seed context "Right — what's the story with that?" / continue
context + M4-INFLUENCED "Brake — what's the story with that?" / emotion
reasoning, clean / recall reasoning + M14-INFLUENCED, correct G7 quote.
s1_car_para: seed dark / continue context + M4-INFLUENCED, good
continuation ("The car — I follow. Tell me more.") / emotion belief, clean
/ recall agenda MISS (F4).
s2_person: name+fact bound correctly (people) / weekend recall context
echo, thin (F4) / NAME RECALL vault MISS (F1) / emotion clean / pivot
context, switches fine.
s2_person_para: binding ok / weekend recall recap, content-bearing /
NAME RECALL people MISS (F1) / emotion clean / pivot context +
M4-INFLUENCED, switches fine.
s3_fact: factual honest "I do not know." (correct, empty stores) / false
correction teach-banked (F3 scope note) / follow-up context echo /
agenda write+read context MISS (F2).
s3_fact_para: factual context echo (paraphrase flips honest-ignorance to
echo — F4-adjacent) / false correction teach-banked / follow-up context /
agenda write context but read reasoning + M14-INFLUENCED, correct G7 quote
("I remember: put milk on my shopping agenda.").

## 5. Suspect-class verdicts (roadmap classes A–G)

- A (wrong memory admitted): NOT OBSERVED — M1/M2 stay at RAN or
  OUTPUT USED without false influence on every turn.
- B (thread lost/weak): OBSERVED in thin form — contextual echoes
  ("X — what's the story with that?") hold the thread lexically but carry
  no memory content on recall turns (F4).
- C (wrong selector winner): OBSERVED — vault on name recall, agenda on
  car recall, context on agenda write/read (F1/F2/F4).
- D (memory treated as reply): NOT OBSERVED as a failure — the only two
  dumps are legitimate answers to explicit recall requests. Seam-A scan
  over all 30 turns confirms: zero non-recall turns carry recall framing
  or prior-input quotation in the grounded result.
- E (stance corrupts): RULED OUT by payload comparison (see §8) — actual
  stance dicts captured on all 30 non-executive turns; intent template ==
  grounded and intent winner == winner throughout; no recall framing
  introduced in B.
- PROMPT-CONSTRUCTION (B coherent, C introduces old memory): NOT OBSERVED
  — zero turns where the mouth prompt introduces recall framing or
  prior-input quotation beyond what the stance already carries.
- F (live-mouth quotation): UNMEASURED — fake echo-mouth by design; live
  mouth stays out of CN0 scope. The prompt seam is now fully characterized
  (see §8), so F is isolated to actual live generation.
- G (prior-turn state wrong): OBSERVED — person binding invisible two
  turns later; agenda write persisting nothing (F1-para/F2).
- M13-scope: correctly silent on prose false-corrections with an empty
  graph (F3 scope note, no charge).

## 6. Harness-integrity notes

- A first-run contamination artifact (reused sandbox across manual runs
  produced a "future quote") was caught by inspection and fixed by
  scoping a `cn0_*` partition wipe to the temp root; `run_all.py` always
  supplies a fresh sandbox. Post-fix rerun is clean and stable in its
  finding set across runs (seed-turn dark/context jitter only).
- One manual run from the live repo CWD was correctly REFUSED by the
  sandbox guard (evidence the guard works).
- Zero production files touched by the harness (only new test + docs).

## 8. OBSERVABILITY COMPLETION (24 Sept 2026, zero production change)

The original CN0 trace contract required winner -> grounded result ->
cognitive_stance -> mouth input -> final response. The first baseline
recorded only winner / trace response / stance_used boolean / mouth
fallback metadata / final response, which could not honestly rule out E.
This section closes that gap. Harness: `tests/verify_cn0_conversation_trace.py`
(extended, still diagnostic-only).

### Seam provenance (proven from current code)

- Seam A (grounded pre-stance result) = `manifest_thought()` return =
  `ego.last_trace["response"]`: `aura_bridge.py` stores
  `"response": response` into `last_trace` then returns `response`;
  `ukft_brain_api.py` `roleplay()` holds that return as `template`
  BEFORE `cognitive_stance()` / prompt / mouth run. Identity, not inference.
- Seam B (actual stance payload) is NOT persisted by production (local
  `stance` dict; `route_receipt` keeps booleans only), so the suite wraps
  `SovereignEgo.cognitive_stance` with a record-and-return wrapper.
  Test-side only, behaviorally inert (identical return value, synchronous
  call, per-turn correlation by snapshot). 30/30 non-executive turns
  captured; zero executive winners occurred (all winners outside
  `EXECUTIVE_WINNERS`, so no NOT-OBSERVABLE legs).
- Seam C (exact mouth prompt) = `payload["prompt"]` received by
  `roleplay_fn`, captured test-side per turn. 30/30 captured.
- Seam D (final response) = `BrainResponse.response`. 30/30 present.
- Hard integrity gates added: A observable 30/30, B observable on every
  non-executive turn 30/30, C captured 30/30, D present 30/30 — green.

### Four-seam comparison result (all 30 turns)

- SEAM-A-GROUNDING flags: 0. No non-recall turn carries recall framing
  (production `_is_recall_output` definition) or verbatim prior-input
  quotation in the grounded result.
- SEAM-B-STANCE flags: 0. E-VERDICT: RULED OUT — stance captured on all
  30 non-executive turns; intent template == grounded and intent winner ==
  winner throughout; no recall framing introduced in B.
- SEAM-C-PROMPT flags: 0. No turn introduces recall framing or new
  prior-input quotation at prompt construction.
- F-VERDICT: UNMEASURED (no live model generation tested; stated
  separately from prompt construction by construction).

### Emotion-turn upstream/downstream stale-memory trace (4 turns)

For each emotion turn: A framed=False quotes=0; B framed=False
(quotes=2–3 prior inputs carried as history/convo context, not as recall
framing); C framed=False, memory-language present (prompt carries the
memory-block + quoting-policy instructions), prior-input quotes=2–3 as
carried context, prompt length ~3.3–3.5k chars; D framed=False quotes=0.

So the "4/4 final fallback outputs clean" result is now bounded exactly:
cleanliness is proven at A (grounded contains zero prior-input material),
B carries history as context without recall framing, C carries prior
inputs as memory-block/history context plus quoting-policy language
without recall-framed reply text, D is clean. The residual risk lives
entirely in unmeasured live generation: a live mouth receiving a prompt
that contains prior-input context COULD rephrase that context as a memory
dump. That is the isolated F boundary for CN1+ — not a finding, a
measurement limit.

### Corrected verdicts

- E: RULED OUT (was: ruled out on stance_used boolean alone — now proven
  by payload comparison).
- F1 base: C plus branch/grounding-construction failure (was: "C + D" —
  D withdrawn: roadmap D requires the selected memory to become the reply).
- F: UNMEASURED (unchanged, now isolated to live generation).
- F1/F2/F4 remain diagnostic findings; nothing fixed in this pass.

## 9. What CN1+ owns next (no fixes in this pass)

CN1 input: F4 recall-routing instability + F1/F2 state-carry misses, with
F3's lesson-utilization gap as known context. Positive controls to preserve:
genuine recall quoting (s1_car t4, s3_fact_para t5), honest ignorance
(s3_fact t1), clean emotion continuations (4/4), working pivots (2/2),
M4-influenced continuations (s1 both phrasings, s2_para pivot).
