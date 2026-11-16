# AURA Brain <-> GF Integration Audit

Date: 20 Sept 2026

Status: READ-ONLY ARCHITECTURE AUDIT COMPLETE

Scope: episodic memory, G7 context, people/current-person, rapport, beliefs,
lessons, agenda, mood, boundaries, personality, and writeback. This pass made
no runtime, test, state, M14, or M16 changes.

## 1. Audit Question

Which GF-era systems participate in the UKFT brain lifecycle, and which sit
beside, before, or after the selector?

The audit standard is the current project law:

- A module being called is not enough.
- Producing output is not enough.
- A reader must be identified before persisted state is called connected.
- A selector claim requires a real path into candidate eligibility, candidate
  salience, selector context, or a winner branch.
- M5-proven causal is narrower than structurally connected or covered by an
  older integration test.
- Post-selection phrasing influence is not response-selection influence.
- Unknown is preferable to inferred causality.

## 2. Classification Key

- `IN-BRAIN`: participates in the turn, memory, reasoning, field, or selector
  lifecycle rather than only wrapping it.
- `READS-BRAIN`: reads brain-owned state but does not write that state through
  the audited path.
- `WRITES-BRAIN`: writes brain-owned state but is not a general reader of it.
- `BIDIRECTIONAL`: persisted output is read on later turns and the subsystem
  also writes or updates it.
- `SELECTION-ONLY`: acts at candidate eligibility/scoring/winner control but
  has no broader memory lifecycle of its own.
- `SIDECAR`: surrounds the brain lifecycle without participating in the basal
  decision seam.
- `WRITEBACK-ONLY`: writes are not read into the audited future decision path,
  or a named sub-field has no decision reader.
- `DUPLICATED`: the same fact, event, policy, or setting exists in multiple
  stores or implementations.
- `ORPHANED`: a module, field, argument, or output has no live consumer.
- `OBSERVER-ONLY`: records or displays activity without affecting cognition.
- `UNKNOWN`: a plausible route exists but isolated influence or ownership is
  not established.

Classifications can be combined. They describe topology, not quality.

## 3. Executive Verdict

GF is not one sidecar around a pre-existing UKFT selector. It is split across
four architectural zones:

1. **Inside the turn and selector lifecycle:** G7 working context,
   people/current-person, agenda intents, beliefs, teaching intents, explicit
   self/constitutional boundaries, and episodic recall through reasoning.
2. **Inside persistence but outside the basal winner competition:** rapport
   update, rapport mood, most lesson-led future learning, and generic turn
   writeback.
3. **After selection:** roleplay personality, relationship depth, affect tone,
   romance pacing, explicit-content deflection, pet-name checks, and final
   response amendment.
4. **Outside cognition:** character-pack source files after onboarding,
   observer telemetry, API write summaries, viewer/export, and several
   persisted metadata fields with no behavioral reader.

### 3.1 System matrix

| System | Primary classification | Storage authority | Selector relationship | M5 status |
|---|---|---|---|---|
| Episodic | `IN-BRAIN`, `BIDIRECTIONAL`, `DUPLICATED` | `episodic_memory.txt` in active root/partition | Recall may create the `reasoning` candidate; no independent episode bid | Connected by prior evidence; M14 influence policy not proven |
| G7 context | `IN-BRAIN`, `BIDIRECTIONAL`, `DUPLICATED` | `working_memory.txt` | Query resolution, M1/M2 basis, M4 context bid and later prompt context | M4 subset M5-proven |
| People/current-person | `IN-BRAIN`, `BIDIRECTIONAL`, `DUPLICATED` | `people.txt`; API binding also in `profile.json` | Direct `people` candidate plus M4 recall eligibility guard | Narrow M4 current-person subset M5-proven |
| Rapport | `IN-BRAIN`, `BIDIRECTIONAL`; selector-relative `WRITEBACK-ONLY` | `rapport.txt` | No basal candidate or modifier; changes same-turn/later final voice | Proven non-participant in tested selector paths; mouth influence working |
| Beliefs | `IN-BRAIN`, `BIDIRECTIONAL`; trust sub-ledger `WRITEBACK-ONLY` | `beliefs.txt`, `pending_belief.txt` | Direct `belief` candidate and graph-silent VERIFY fallback via `reasoning` | Connected by prior evidence; no dedicated M5 receipt |
| Lessons | `IN-BRAIN`, `BIDIRECTIONAL` on teach/review turns; persistent text mostly `WRITEBACK-ONLY` | `lessons.txt` | Direct `teach` candidate only when correction/review is detected | Connected by prior evidence; no general future-answer influence proof |
| Agenda | `IN-BRAIN`, `BIDIRECTIONAL` | `threads.txt` | Direct `agenda` candidate; open threads also shape greetings and roleplay question-back | Connected by prior evidence; no dedicated M5 receipt |
| Mood | `DUPLICATED`, mixed `READS-BRAIN` / `BIDIRECTIONAL` / `UNKNOWN` | No single authority | Affect and rapport mood shape phrasing; amygdala has an unproven field route | Affect tone M5-proven non-causal at selector seam; amygdala route unknown |
| Boundaries | `DUPLICATED`; constitutional/tool surfaces `SELECTION-ONLY`; romance surface `SIDECAR` / output gate | Code, `gf_boundaries.md`, and API profile settings | Some boundaries own candidates; GF romance rules constrain only the mouth/output | Mixed; no single boundary subsystem |
| Personality | `DUPLICATED`; packs `SIDECAR` + `WRITES-BRAIN`; profile `READS-BRAIN` | Pack at birth, then `profile.json` plus seeded vault/identity | Direct current effect is mouth phrasing; seeded brain records can enter normal vault paths | No direct personality-to-selector receipt |
| Writeback | `IN-BRAIN`, `BIDIRECTIONAL`, distributed | Owning files; API partition is authority between turns | Mostly after selection, but several intent detectors write before selection | Turn pipeline connected; no transaction boundary |
| Observer | `OBSERVER-ONLY`, `SIDECAR` | `observer_trace/**/*.jsonl` | None | M5-proven non-causal |

### 3.2 Bottom-line answer

- **Actually inside the UKFT brain lifecycle:** G7, people/current-person,
  agenda, beliefs, the teach detector/branch, episodic recording and recall,
  working-memory writeback, rapport persistence, and constitutional/tool
  decision rules.
- **Inside only after the decision seam:** rapport-to-depth, rapport mood,
  stateless affect, personality voice, romance mirroring, explicit-content
  deflection, pet-name checks, and immersive reply writeback.
- **Sidecars that seed or inspect the brain:** character packs, profile
  onboarding, observer telemetry, viewer/export, API write summaries.
- **Duplicated:** conversation history, current-person identity, relationship
  depth, personality, boundaries, and mood.
- **Partly orphaned/writeback-only:** people importance, belief trust, most
  banked lesson text, several pack knobs, and API write-summary counters.

## 4. The Two Production Lifecycles

The architecture has two materially different production routes. A subsystem
can be connected in one and absent in the other.

### 4.1 Live desktop organism

`aura_master.py` launches background field, amygdala, hippocampus, dream,
identity, sleep, thalamus, cortex, temporal, decay, and other lobes
(`aura_master.py:467-513`). `process_message()` writes the incoming message to
the sensory path, waits, calls `SovereignEgo.manifest_thought()`, optionally
roleplays the selected template, writes `aura_output.txt`, emits observer
events, and releases the thinking lock (`aura_master.py:165-393`).

Root files are the operational and persistent source of truth on this route.
Background decay, sleep, sensory ingestion, and field evolution are present.

### 4.2 GF Brain API / Discord route

Discord calls `BrainModule.roleplay()` (`ukft_discord.py:365-425`). The API:

1. Loads or creates `users/<id>/profile.json` and the user partition.
2. Acquires one instance-local `_ask_lock`.
3. Gets a cached `SovereignEgo`.
4. Clears the process-global cognitive field.
5. Stashes root files.
6. Copies the partition's `USER_STATE_FILES` into hard-coded root paths.
7. Reloads only the ego's working memory explicitly.
8. Runs `manifest_thought()`.
9. Runs post-selection roleplay unless the winner is executive.
10. Copies non-empty root state files back to the user partition.
11. Restores the original root files.
12. Updates `profile.json` counters and depth.

Evidence: `ukft_brain_api.py:88-199`, `542-583`, `618-827`.

For this route, `users/<id>/` is the persistent source of truth between turns,
but temporary root copies are the operational source during a turn. The route
does not start the desktop background lobes. It clears the field before each
turn and does not call `restore_field_state()`. Therefore live field history,
sleep, Ebbinghaus decay, amygdala processing, and reasoning maintenance are not
uniformly present for API partitions.

This distinction is central to the Brain<->GF boundary. "In the live organism"
does not automatically mean "in every GF partition lifecycle."

## 5. Selector Seam

`SovereignEgo.manifest_thought()` computes action branches, assembles context,
resolves the current input through G7, ranks vault anchors, runs reasoning,
applies M1/M2/M4/M13, and builds the candidate arena
(`aura_bridge.py:3032-3378`).

The candidates are:

```text
execute 1.00   focus 1.00   sleep 1.00   tools 1.00   idle 1.00
self 0.99      people 0.99  agenda 0.99  belief 0.99  teach 0.99
reasoning 0.95 conflict 0.95 recap 0.92   voice 0.90
context 0.75/0.86            vault 0.80   field 0.50   dark 0.20
```

Exact construction: `aura_bridge.py:3319-3363`.

The only generic `BasalGanglia.modulate()` inputs are `vault_support` and
`inhibited`; `m4` and `m13` are carried in context for evidence but are applied
before selection through candidate construction/eligibility
(`ukft_basal_ganglia.py:77-102`; `aura_bridge.py:3364-3378`). Rapport, mood,
personality, episodes, agenda persistence, and observer telemetry are not
hidden generic selector knobs.

## 6. System Traces

### 6.1 Episodic memory

**Classification:** `IN-BRAIN`, `BIDIRECTIONAL`, `DUPLICATED`. Operator gist is
`READS-BRAIN` + `WRITES-BRAIN` + `SIDECAR`. M14 policy remains `UNKNOWN`/not
implemented.

**Storage and source of truth**

- Active event store: `episodic_memory.txt`, capped at 500 records
  (`ukft_episodic.py:21-35`, `123-133`).
- Records contain timestamp, kind, concepts, and content
  (`ukft_episodic.py:38-80`).
- `forgotten_memories.txt` is an archive, not an active retrieval source
  (`ukft_episodic.py:147-170`).
- In an API route, the user partition copy is authoritative between turns.

**Writers**

- Every completed engine turn writes a `conversation` episode containing the
  first 80 input characters and the winner, not the answer
  (`aura_bridge.py:3510-3519`).
- An accepted immersive line writes a separate `reply` episode
  (`aura_master.py:319-335`; `ukft_brain_api.py:764-781`).
- Tools, sleep, spontaneous speech, and discovery also write event kinds.
- Sleep writes a `sleep` episode after field-edge consolidation
  (`ukft_sleep.py:142-175`).

**Readers and retrieval**

- `_recall_answer()` routes time, known-person, and topic recall
  (`aura_bridge.py:2393-2469`).
- Recall is attempted inside `_reasoning_answer()` when graph proof is absent
  (`aura_bridge.py:2530-2596`).
- A successful diary recall becomes the `reasoning` answer and therefore can
  create the 0.95 reasoning candidate (`aura_bridge.py:3337-3341`).
- Reply-kind records are excluded from factual recall by `ukft_recall.py`.
- People descriptions, agenda story, status, presence, delight, growth, and
  the roleplay fallback also read episodes.

**Field / working / vault involvement**

- Episodes do not directly become field nodes on ordinary recording or recall.
- Episode concepts are derived from working-memory turn concepts; this is not
  the same as storing the full conversation.
- `ukft_gist.py` can distill episodes into a `Nightly Gist` vault anchor, but
  repository caller evidence shows CLI/tests only; scheduling is not proven.
- `_assemble_context()` copies recent episodes and open episode questions into
  a bundle, but the live selector consumes only `current_user` from that bundle
  (`ukft_context.py:19-105`; `aura_bridge.py:3223-3250`). Those episode bundle
  fields are currently shadow data.

**Decay / sleep / consolidation**

- Hard FIFO cap: 500.
- Ebbinghaus half-life: three days with deletion below 0.10
  (`ukft_ebbinghaus.py:26-30`, `104-129`).
- `expose()` can rehearse a trace, but production caller search found no turn
  caller; only tests call it. Retrieval therefore does not rehearse memory.
- Ebbinghaus is launched by the desktop master, not by standalone Brain API.
- Sleep consolidates field nodes and then records that event. It does not
  consolidate conversation episodes into semantic memory.

**Selection influence**

- Connected: a diary result can supply the reasoning candidate.
- Not M14-proven: there is no provenance-aware episode boost/suppress policy,
  no independent episode candidate, and no isolated episode perturbation
  receipt proving a winner flip/guard.
- M13 explicitly proves episodes do not vote in contradiction gating.

**Duplication / gaps**

- One exchange may exist as a full G7 turn, a truncated `conversation`
  episode, and a separate immersive `reply` episode.
- A non-immersive engine response is not stored as a reply episode.
- Trace strength does not rank recall; an episode remains equally searchable
  until deletion.

### 6.2 G7 conversation context

**Classification:** `IN-BRAIN`, `BIDIRECTIONAL`, `DUPLICATED`. The M4 subset is
M5-proven selection-causal.

**Storage and source of truth**

- `working_memory.txt` stores up to eight turns
  (`ukft_working_memory.py:31-37`, `124-128`).
- Each turn stores timestamp, query, response, winner, and concepts
  (`ukft_working_memory.py:142-166`, `195-252`).
- It is the source of truth for the current conversation, not long-term event
  history.

**Writers**

- Every selected engine response is recorded after winner construction
  (`aura_bridge.py:3494-3498`).
- If immersive roleplay succeeds, the last stored response is amended to what
  Aura actually said (`ukft_working_memory.py:159-166`).

**Readers and retrieval**

- G7 resolves pronouns and vague references before vault/reasoning retrieval
  (`ukft_working_memory.py:309-481`; `aura_bridge.py:3088-3122`).
- It provides active topic, open question, continuation, recap, ordered
  dialogue, and prompt context (`ukft_working_memory.py:168-190`, `255-307`,
  `483-551`).
- Resolved input adds vault hits and enters reasoning; contentless follow-ups
  retry retrieval against the current topic (`aura_bridge.py:3110-3178`).

**Field / working / vault involvement**

- Working memory is the owning layer.
- It supplies M1's resolved-query basis and M2's active-thread basis.
- It has no direct field-node bid. It can indirectly determine which vault
  anchor wins and is then recruited into the field.

**Decay / sleep / consolidation**

- No temporal decay or sleep consolidation.
- Strict eight-turn eviction only; persistence survives reboot.

**Selection influence**

- M4 converts strong dialogue evidence into a 0.86 context bid; weak evidence
  remains 0.75 (`aura_bridge.py:849-970`, `3354-3360`).
- `tests/verify_m4_selection_context.py` contains the M5 receipt where changing
  real M4 context changes `vault` to `context`.
- M2 also consumes active thread state to suppress off-thread vault anchors.

**Duplication / gaps**

- The same exchange is also represented in episodic memory.
- `last_winner()` has no production caller found; its stored field is useful
  for persistence/diagnostics but behaviorally orphaned at that accessor.

### 6.3 People and current-person

**Classification:** `IN-BRAIN`, `BIDIRECTIONAL`, `DUPLICATED`. Narrow M4
current-person eligibility is M5-proven. `importance` is `WRITEBACK-ONLY` /
output-orphaned.

**Storage and source of truth**

- `people.txt` owns display names, aliases, first/last seen, mention count,
  importance, relationship history, facts, timestamps, and provenance
  (`ukft_people.py:295-390`).
- `pending_people.txt` owns one uncertain introduction.
- In API partitions, `profile.json.current_person_key` owns the stable speaker
  binding while `people.txt` owns the person record
  (`ukft_brain_api.py:45-64`, `312-330`). This is duplicated responsibility.

**Writers**

- `_people_action()` learns introductions, current-user name/alias/facts,
  known-person facts, and mentions (`aura_bridge.py:1573-1653`).
- `PeopleModel.commit`, `note_mention`, `learn_fact`, and pending lifecycle
  persist the state (`ukft_people.py:415-496`, `638-676`).
- Onboarding/migration creates and synchronizes the current-person binding
  (`ukft_brain_api.py:221-250`, `289-330`).
- Presence can create the architect record while gathering boot state.

**Readers and retrieval**

- Direct who-is/current-user rendering reads people state
  (`aura_bridge.py:1655-1843`).
- Names and aliases become valid G7 referents (`aura_bridge.py:3092-3101`).
- Episodic person recall, roleplay prompt rendering, proof-register address,
  growth, and volunteered memory also read it.

**Field / working / vault involvement**

- Names/aliases feed working-memory reference resolution.
- Current-person evidence guards autobiographical vault eligibility through
  M4 (`aura_bridge.py:3219-3250`).
- No direct people-to-field write was found.

**Decay / sleep / consolidation**

- Importance lazily decays with a 30-day half-life and floor 0.2 when a
  `PeopleModel` is loaded (`ukft_people.py:356-369`).
- Facts cap at 20; people are not deleted by this mechanism.
- No sleep consolidation.
- Importance has no production reader outside its own persistence/mutation
  code, so its decay currently has no demonstrated behavioral effect.

**Selection influence**

- A recognized action creates `people=0.99` and owns its winner branch
  (`aura_bridge.py:3328-3329`, `3424-3428`).
- M4 can guard generic voice, withdraw an incompatible autobiographical vault
  anchor, and change vault eligibility. M5 receipts prove the narrow
  current-person `vault -> voice` and voice-less `vault -> reasoning` effects.
- Other people behavior is connected by prior evidence, not separately
  M5-proven.

**Duplication / gaps**

- Profile binding and people record can drift.
- Lazy importance decay can be re-applied from an old `last_seen` after an
  unrelated save; no reader currently makes this user-visible.
- API empty-file copyback can resurrect a cleared pending introduction; see
  writeback findings.

### 6.4 Rapport

**Classification:** `IN-BRAIN`, `BIDIRECTIONAL` across turns and into final
voice; selector-relative `WRITEBACK-ONLY`. The separate `rapport_audit`
verdict is `OBSERVER-ONLY`.

**Storage and source of truth**

- `rapport.txt` stores score, stored stage, dwell, warmth, trust, distance,
  contact, streak, cooldown, familiar floor, mood coordinates/name, and last
  timestamp (`ukft_rapport.py:305-394`).
- It is the intended relationship source of truth when it has history.
- `profile.json.depth_stage` is a derived cache/fallback, not an equal
  authority (`ukft_brain_api.py:362-404`).

**Writers**

- Every normal engine turn calls `Rapport.observe()` after the winner and
  engine response already exist (`aura_bridge.py:3521-3556`).
- `observe()` decays prior evidence, scores the user input, moves stage/mood,
  and saves (`ukft_rapport.py:422-503`).
- New partitions seed a stranger ledger; legacy depth can bootstrap it.

**Readers and retrieval**

- Roleplay reads a rapport line, depth, and heat lane
  (`ukft_roleplay.py:480-565`, `677-701`, `854-888`).
- Post-check depth gates pet names (`ukft_roleplay.py:796-826`).
- Rapport is not retrieved as a candidate or vault record.

**Field / working / vault involvement**

- It receives a derived affect family and user heat label during observation.
- It imports G7's lexical `substance_words()` helper but does not read stored
  dialogue.
- No direct vault or field-node connection.

**Decay / sleep / consolidation**

- Warmth, trust, distance, and contact have a weekly half-life applied on the
  next observation (`ukft_rapport.py:430-445`).
- No background rapport decay and no sleep consolidation.

**Selection influence**

- Rapport is explicitly excluded from M4 (`aura_bridge.py:849-856`).
- No rapport candidate or selector modifier exists.
- It cannot change the already selected engine winner through this path.
- It can change the same turn's user-visible response after selection by
  changing the roleplay prompt, heat lane, intimacy envelope, or post-check
  acceptance. Calling it wholly observer-only would therefore be wrong.

**Duplication / gaps**

- Stored stage, recomputed `current_stage()`, profile depth cache, and legacy
  episode-count fallback duplicate relationship depth.
- API roleplay computes `profile.depth_stage` before `manifest_thought()`
  updates rapport, while rapport line/lane are read afterward. One prompt can
  therefore contain stale depth plus fresh rapport state.
- `rapport_audit()` only reports into `last_trace`; it does not revise an
  offending engine response (`ukft_rapport.py:261-282`).

### 6.5 Beliefs

**Classification:** `IN-BRAIN`, `BIDIRECTIONAL`. Trust is
`WRITEBACK-ONLY`/output-orphaned.

**Storage and source of truth**

- `beliefs.txt` owns provisional user-asserted claims and trust records.
- `pending_belief.txt` owns one unresolved contested claim
  (`ukft_belief.py:201-280`, `364-404`).
- The knowledge graph remains the proof source; beliefs do not replace it.

**Writers**

- `_belief_action()` detects assertions and checks graph conflict
  (`aura_bridge.py:2026-2083`).
- Uncontested claims are held immediately; contested claims are staged only in
  the selected answer branch (`aura_bridge.py:2097-2134`).
- Confirm/cancel changes trust and pending state
  (`ukft_belief.py:331-362`).
- Parsed correction counterclaims can also write beliefs.

**Readers and retrieval**

- Direct assertion/pending lifecycle creates the belief response branch.
- `_belief_verify()` reads a held claim only when a VERIFY plan has no proof or
  graph result (`aura_bridge.py:2146-2186`).
- Match and word-match retrieval are in `ukft_belief.py:294-329`.

**Field / working / vault involvement**

- Graph/inference state is read before holding or contesting a claim.
- Generic post-turn writeback places the exchange in G7/episodes.
- No field integration.
- No vault reader revises a belief despite response text saying vault evidence
  would change the mind back (`aura_bridge.py:2123-2131`).

**Decay / sleep / consolidation**

- No cap, time decay, sleep consolidation, or automatic supersession.

**Selection influence**

- A belief action creates `belief=0.99`.
- A graph-silent VERIFY belief answer becomes `reasoning=0.95` with
  `reasoning_kind=belief-provisional` (`aura_bridge.py:2570-2579`).
- These are real paths into competition, but no dedicated M5 perturbation
  receipt proves belief output alone changes the winner.

**Duplication / gaps**

- Trust is written and test-readable through `trust_of()`, but production
  caller search found no consumer. It does not alter conflict policy,
  confidence, or candidate score.
- Ordinary `hold()` happens before basal selection, so a losing belief intent
  can still mutate state.
- API empty-file copyback can resurrect a cleared pending contest.

### 6.6 Lessons

**Classification:** `IN-BRAIN`, `BIDIRECTIONAL` for correction/review turns;
persistent lesson text is otherwise mostly `WRITEBACK-ONLY`. Correction facts
are `DUPLICATED` into beliefs/people where parseable.

**Storage and source of truth**

- `lessons.txt` stores timestamp, teacher, topic, and lesson text, capped at
  200 and exact-deduplicated (`ukft_teach.py:77-146`).
- It is authoritative for what was banked as a lesson, not for corrected world
  truth.

**Writers**

- `_teach_action()` handles bare corrections, counterclaims, unparsed
  correction text, and review requests (`aura_bridge.py:2275-2350`).
- Parseable counterclaims may also write `beliefs.txt`; known-person text may
  also write `people.txt`.
- Tool outcomes are banked only when an explicit lesson review runs
  (`ukft_teach.py:158-176`; `aura_bridge.py:2380-2388`).

**Readers and retrieval**

- The lesson ledger is rendered on an explicit "what have you learned?" style
  request (`ukft_teach.py:179-191`).
- Growth counts lessons and may later affect a roleplay mirror brief.
- Generic factual answer selection does not consult banked lesson text.

**Field / working / vault involvement**

- Bare correction reads the previous G7 query and the last output file for
  provenance (`aura_bridge.py:2299-2313`).
- No direct field or vault path.
- Factual corrections can be duplicated into beliefs/people, which are the
  only general future-answer paths found.

**Decay / sleep / consolidation**

- No time decay or sleep consolidation; oldest-drop at 200 only.

**Selection influence**

- A detected correction/review creates `teach=0.99` and owns a branch.
- Previously banked lesson content does not generally change future candidate
  eligibility or scoring.
- No dedicated M5 receipt.

**Duplication / gaps**

- "I will keep that in mind" overstates future use when a correction cannot be
  parsed into belief/person state.
- Recording can happen during intent computation before selection.
- API size-growth metrics can miss capped/same-size lesson rewrites and make
  `profile.lessons_banked` inaccurate.

### 6.7 Agenda

**Classification:** `IN-BRAIN`, `BIDIRECTIONAL`. Its direct action path is a
selection owner; its greeting/roleplay reads are phrasing paths.

**Storage and source of truth**

- `threads.txt` stores up to 50 thread records with id, topic, opened/updated
  time, status, kind, and source (`ukft_agenda.py:78-131`).

**Writers**

- `_agenda_action()` calls `AgendaModel.open()` or `.close()` before selection
  (`aura_bridge.py:1952-1980`, `3064-3066`).
- Restating refreshes an existing open thread; capacity eviction removes the
  oldest closed record first, otherwise the oldest updated record
  (`ukft_agenda.py:137-183`).

**Readers and retrieval**

- Direct agenda responses read open thread state and episodes for "our story"
  (`aura_bridge.py:1982-2021`).
- `_assemble_context()` includes open threads, although that bundle field is
  not consumed by selection.
- Greetings and roleplay `question_back()` independently read open threads
  (`aura_bridge.py:225-262`; `ukft_policy.py:57-90`;
  `ukft_roleplay.py:556-565`).

**Field / working / vault involvement**

- Agenda state is not a vault anchor and does not write field nodes.
- The selected agenda response enters G7/episodic generic writeback.
- Open agenda threads are separate from G7's current conversation thread.

**Decay / sleep / consolidation**

- Capacity eviction only; no temporal decay or sleep consolidation.

**Selection influence**

- A recognized action creates `agenda=0.99` and can displace a reasoning
  incumbent (`aura_bridge.py:3328-3331`; `tests/verify_c6.py:116-143`).
- No dedicated M5 isolated perturbation receipt.
- Persisted open threads can affect a later greeting's content, but not its
  basal winner; they also add a post-selection roleplay question-back.

**Duplication / gaps**

- "Thread" means two stores: short G7 conversation thread and persistent
  agenda obligation. `_assemble_context()` carries both.
- Agenda open/close mutates before the winner is known, so a losing agenda
  detector can leave state behind.

### 6.8 Mood

**Classification:** `DUPLICATED`. There is no single mood system or source of
truth.

#### A. Stateless affect

- `ukft_affect.read_state()` reads `self_state.txt`, `field_stats.txt`, and
  knowledge gaps and owns no store (`ukft_affect.py:28-79`).
- `tone_for()` maps this to warm/bright/cool/quiet
  (`ukft_affect.py:84-102`).
- It affects proof-register styling, API emotion metadata, and roleplay prompt
  mood (`aura_bridge.py:2221-2238`; `ukft_brain_api.py:406-432`;
  `ukft_roleplay.py:285-297`, `536-546`).
- M5 proves changing this tone output does not change the current response
  selector result. Classification: `READS-BRAIN`, phrasing-only at the tested
  seam.

#### B. Rapport mood

- Persistent valence, energy, and mood name live in `rapport.txt` and update
  after the engine response (`ukft_rapport.py:529-553`).
- They affect rapport prompt text and heat lane, not basal selection.
- Classification: `IN-BRAIN`, `BIDIRECTIONAL`, post-selection phrasing.

#### C. Amygdala / emotional history

- Hippocampal vault processing writes `short_term_memory.txt`; amygdala drains
  it, appends `emotional_core.txt`, and stimulates/damps the field
  (`ukft_amygdala.py:67-118`; `ukft_hippocampus.py:187-198`).
- Field activation can create the low-priority `field` candidate, so an
  indirect route exists.
- No isolated test proves changing amygdala output changes the winner.
- This route runs in the desktop master, not ordinary standalone Brain API.
- Classification: `IN-BRAIN`, `BIDIRECTIONAL`, selector influence `UNKNOWN`.

#### D. Orphaned mood input

- `assemble_thought()` receives an `emotional_state` argument, but current
  inner-monologue body inspection found no material use. That argument is
  output-orphaned.

**Decay / sleep / consolidation**

- Stateless affect has no state to decay.
- Rapport mood changes/decays through later observations.
- Emotional history is append-style state; field has its own decay and sleep
  paths. There is no unified mood consolidation.

### 6.9 Boundaries

**Classification:** `DUPLICATED`. Constitutional and tool boundaries are
`SELECTION-ONLY`; GF romance/content boundaries are a post-selection
`SIDECAR`/output gate; profile opt-outs are `READS-BRAIN` by the mouth.

**Storage and source of truth**

- Constitutional floor: executable `FLOOR` rules in `ukft_self.py:46-95`.
- Tool consent: pending action state and exact protocol in bridge/tools.
- GF romance/content floor: `gf_boundaries.md`, `ukft_boundaries.py`, roleplay
  prompt construction, and roleplay post-check.
- Per-user opt-outs and personality envelope live in `profile.json`.
- There is no one boundary authority spanning all surfaces.

**Writers and readers**

- Constitutional floor reads input and returns a `self` action.
- Tool consent reads/writes pending tool state.
- GF output rules read user heat, depth, rapport lane, personality, opt-outs,
  and generated text (`ukft_boundaries.py:36-57`, `77-178`;
  `ukft_roleplay.py:568-674`, `796-826`, `978-1005`).
- Boundary policy does not write vault, working memory, or field state; final
  accepted/deflected speech is later written through ordinary response
  writeback.

**Decay / sleep / consolidation / retrieval**

- No decay or sleep consolidation.
- Rules and profile settings are directly loaded, not semantically retrieved.

**Selection influence**

- Constitutional violations create `self=0.99` and can own the selected
  response.
- Tool confirm/cancel/request creates `tools=1.0` and controls execution.
- Romance mirroring, explicit detection/deflection, and pet-name policy run
  after the engine winner. They can alter or reject the spoken line but cannot
  move the basal winner.

**Duplication / gaps**

- Policy prose, executable checks, profile envelopes, prompt rules, and
  post-checks duplicate boundary truth.
- Character packs expose an optional `boundaries_overlay`, but no
  `characters/*/boundaries.md` files exist and no runtime consumer of the
  loaded overlay was found.
- Discord deployment age-gate remains policy-required but not live-proven.

### 6.10 Personality

**Classification:** character packs are `SIDECAR` + `WRITES-BRAIN`; persisted
profile/persona is `READS-BRAIN`; the overall system is `DUPLICATED`, with
some `ORPHANED` controls.

**Storage and source of truth**

- Birth source: `characters/<id>/pack.json` plus `seed.md`
  (`ukft_pack.py:31-94`).
- Existing-user operational source: `users/<id>/profile.json`; pack changes do
  not update existing profiles (`ukft_brain_api.py:262-310`).
- Brain seeds: `identity_core.txt` and `locked_patterns.txt`
  (`ukft_user_state.py:224-347`).
- Runtime voice also has persona/depth tables in `ukft_roleplay.py`, API
  envelope tables in `ukft_brain_api.py`, and a fixed desktop
  `LIVE_PERSONALITY="flirty"` (`ukft_roleplay.py:831-839`).

**Writers and readers**

- Onboarding consumes pack name/personality/interests and seed bullets, then
  writes profile, identity core, and founding vault anchors
  (`ukft_brain_api.py:279-305`; `ukft_pack.py:78-94`).
- Roleplay reads profile personality/name/interests/depth and boundary
  envelope on every GF turn (`ukft_brain_api.py:696-747`).
- The basal candidate arena does not read `profile.personality`.

**Field / working / vault involvement**

- Founding seed bullets become `SOURCE: GIVEN` vault anchors and can later
  enter ordinary vault retrieval.
- Personality core words become identity-core entries and can enter identity
  field injection through existing identity machinery.
- Current conversation context is not selected by personality.

**Decay / sleep / consolidation**

- Pack/profile personality does not decay or consolidate.
- Seeded identity/vault records follow their own brain-store policies.

**Selection influence**

- Direct current effect is post-selection mouth phrasing and pet-name envelope.
- Indirect seeded vault/identity content may later participate through normal
  brain paths, but no test isolates personality as the changed selector input.
- Classification of direct selector influence: `UNKNOWN`/not proven.

**Duplication / gaps**

- Personality is duplicated across pack JSON, profile JSON, API envelope
  tables, roleplay persona tables, desktop globals, identity seeds, vault
  seeds, and boundary prose.
- Pack `voice_model`, `voice_temperature`, `question_back`, `initiative`, and
  `boundaries_overlay` have no consistent live consumer found. The active
  roleplay model/temperature are module constants, and question-back is driven
  by open brain state instead of the pack knob.
- `_build_identity_seed()` declares per-personality drive weights but only
  writes core words; the `drives` mapping is not consumed in that function
  (`ukft_user_state.py:271-330`).

### 6.11 Writeback

**Classification:** aggregate `IN-BRAIN`, `BIDIRECTIONAL`, distributed and
non-transactional. API write reporting is `OBSERVER-ONLY` diagnostic data.

**Source of truth**

- Each subsystem's owning file is authoritative on the desktop route.
- The user partition is authoritative between API turns; root files are an
  execution staging area.
- `profile.json` is written directly in the user partition and is not one of
  the swapped `USER_STATE_FILES`.

**Writes before selection**

- Agenda open/close.
- Uncontested belief hold.
- Most lesson recording and parseable correction writes.
- Many people facts/names/mentions.
- Knowledge-gap recording during reasoning.

These writes happen while candidates are being computed. There is no rollback
if another candidate wins.

**Writes after selection inside the ego**

- `working_memory.txt`: full current turn with engine response.
- `episodic_memory.txt`: truncated input plus winner.
- `rapport.txt`: observation of the user input.
- `self_state.txt`: selected companion-contact adaptation or earlier
  reasoning/strain adaptation.
- `basal_ganglia_log.txt`: winner/candidate diagnostic.
- Conditional `field_state.txt`, `identity_core.txt`, pending/tool stores,
  register state, and branch-specific files.

Evidence: `aura_bridge.py:3377-3596`.

**Writes after final voice**

- Accepted immersive output amends the last G7 response.
- It writes a second `reply` episode.
- Desktop route writes `aura_output.txt`; API returns a `BrainResponse` and
  Discord sends the message without using the desktop output file.

**Readback**

- G7, episodes, rapport, people, beliefs, and agenda have later-turn readers.
- Most lesson text does not.
- Decision log is used by roleplay to recover the winner during the same API
  swap, but `_EXTRA_ROOT_TOUCHED` is restored rather than copied into the user
  partition. A GF partition does not retain its own basal log after settlement.

**Partition defects and limits**

- `_sync_user_files_to_root(..., "from_root")` copies a root file back only
  when its size is greater than zero (`ukft_brain_api.py:190-194`). Clearing
  `pending_people.txt` or `pending_belief.txt` to empty can therefore leave the
  old non-empty partition copy in place and resurrect pending state next turn.
- `_extract_memory_writes()` reports only size growth
  (`ukft_brain_api.py:434-450`). It misses clears, shrinkage, and equal-size
  replacements. `memory_writes` and profile counters are not an authoritative
  transaction journal.
- The lock serializes swaps only within one `BrainModule` instance. It does not
  coordinate another process, a desktop master, or another API instance.
- The turn is best-effort, not atomic across its files.

### 6.12 Observer telemetry

**Classification:** `OBSERVER-ONLY`, `SIDECAR`.

- Storage is partitioned JSONL under `observer_trace/`, explicitly outside
  vault, episodes, people, and working memory
  (`observer_telemetry.py:1-10`, `65-77`).
- Emission is fail-open and has no cognition write
  (`observer_telemetry.py:101-146`).
- M5 proves telemetry cannot move the winner.
- Desktop `process_message()` and `BrainModule.ask()` emit turn-level events.
- `BrainModule.roleplay()`, the route used by Discord, contains no equivalent
  observer emission block. A normal Discord/GF turn can therefore complete
  without a turn trace.
- Detailed memory/candidate event methods exist, but current production paths
  do not emit a complete candidate-by-candidate causal journal
  (`observer_telemetry.py:162-208`).
- Desktop reports `reasoning_output_produced` after the whole ego call and
  winner confidence as `0.0`; these events must not be interpreted as precise
  causal receipts (`aura_master.py:223-253`).

## 7. Critical Conversation Trace

This is a static trace of one normal meaningful GF conversation through the
Discord/Brain API roleplay route. No live state was executed.

### 7.1 Scenario

Assume an existing user and an active conversation in which Aura asked what
happened at work. The user writes:

> Work was rough today, but I finally solved the gearbox problem.

Assume no tool, constitution, people, agenda, belief, teaching, proof,
contradiction, or relevant vault branch outranks conversation context. The
exact winner is state-dependent; under these stated conditions, the ordinary
continuation path can win `context`.

### 7.2 Input to engine

1. Discord normalizes the author id/name and calls
   `BrainModule.roleplay()` (`ukft_discord.py:365-401`).
2. `profile.json` supplies name, personality, interests, boundary envelope,
   current-person key, cached depth, and counters.
3. The API stashes root state, clears the global field, copies the user's
   partition files to root, and reloads G7 (`ukft_brain_api.py:662-680`).
4. `manifest_thought()` computes action detectors. Some detectors may mutate
   state before selection, although the scenario assumes none match.
5. `_assemble_context()` reads people, episodes, gaps, drives, agenda, and G7;
   only current-person data from this bundle reaches M4.
6. G7 resolves references, carries the open Aura question, and supplies the
   active topic (`aura_bridge.py:3088-3104`).
7. Vault rank, reasoning, M1, M2, M4, and M13 run. M4 can classify the input as
   an answer/continuation and bid `context=0.86`.
8. Basal ganglia selects one winner. This occurs before GF personality,
   rapport lane, romance mirroring, or LLM roleplay.
9. `_answer_context()` produces a grounded engine template.

### 7.3 Engine writeback

Before the final GF voice is generated:

- G7 appends the user input, engine response, winner, and concepts to
  `working_memory.txt`.
- Episodic memory appends a `conversation` record like
  `Work was rough today... -> context`; it does not include the response.
- Rapport observes the user input, updates relationship evidence/mood, and
  writes `rapport.txt`.
- The decision is appended to the temporary root basal log.
- `last_trace` exists in the cached ego object but is not independently
  persisted as brain state.

### 7.4 GF final voice

1. Roleplay reads the already selected winner.
2. It assembles prior ordered G7 dialogue, people/current-person facts,
   interests, stateless affect, fresh rapport line/lane, open agenda/gap
   question-back, profile personality, depth, opt-outs, and the selected
   engine template (`ukft_brain_api.py:677-747`; `ukft_roleplay.py:480-701`).
3. The local mouth may rephrase the template. It cannot move the engine winner.
4. Explicit-content and grounding/post-check gates may replace/reject the
   generated wording (`ukft_roleplay.py:796-826`, `978-1005`).
5. If accepted, G7's response is amended to the actual spoken line and a
   separate immersive `reply` episode is recorded.
6. Root user-state files are copied back, root live state is restored,
   `profile.json` counters are updated, and Discord sends the response.

### 7.5 Where the experience exists afterward

| Location | What remains | Authority / use |
|---|---|---|
| `users/<id>/working_memory.txt` | Full bounded user/Aura turn, final voiced response if roleplay succeeded, winner and concepts | Current-conversation source; used by G7 and later prompts |
| `users/<id>/episodic_memory.txt` | Truncated `conversation` routing record; optionally separate final `reply` record | Event source; recall can later feed reasoning |
| `users/<id>/rapport.txt` | Updated contact/warmth/trust/distance/stage/mood | Later depth, prompt, and heat lane; not basal selection |
| `users/<id>/profile.json` | Incremented turn count, cached depth and other size-derived metrics | GF onboarding/product source; partly derived/duplicated |
| `users/<id>/people.txt` | Existing current-user identity; changed only if this input matched a people-learning rule | Person source; G7/M4/prompt readers |
| `users/<id>/threads.txt` | Unchanged in this scenario | Agenda source |
| `users/<id>/beliefs.txt` / `lessons.txt` | Unchanged in this scenario unless a detector interprets the sentence as an assertion/correction | Conditional companion state |
| `users/<id>/field_state.txt` | Conditional winner snapshot only | Persisted but not automatically restored by Brain API |
| `users/<id>/locked_patterns.txt` | Normally unchanged | Conversation is not automatically semantic vault memory |
| Root `basal_ganglia_log.txt` | Temporary decision line is used during roleplay, then prior root file is restored | Not retained per GF user |
| `observer_trace/` | Usually nothing for `BrainModule.roleplay()` | Roleplay route lacks the ask/master emission sequence |
| Discord channel | Final user-visible text | Product transcript, outside brain state |

The experience therefore exists afterward in at least two brain memories plus
rapport and profile state, but not as one canonical "experience object." G7 is
the best full short-term record; episodic memory is a lossy event index;
rapport is a relationship interpretation; Discord is the external transcript.

## 8. Integration Risks and Called-vs-Connected Findings

### High significance

1. **API empty-file writeback is incomplete.** A cleared pending people or
   belief file is not copied back because `from_root` requires size `> 0`.
   The clear runs, but its result can be disconnected from partition truth.
2. **Brain API creates/gets the ego before swapping the user partition.**
   `SovereignEgo` constructs `PatternEngine`, which eagerly loads the current
   root vault (`ukft_brain_api.py:542-555`; `aura_bridge.py:387-405`). After
   swap, reload occurs only if the partition vault mtime is newer. A cached
   root/user vault can therefore remain stale or cross-partition under an mtime
   ordering. This is a static conditional risk, not a reproduced failure.
3. **The API field lifecycle is not the desktop field lifecycle.** The API
   clears the singleton before every turn and never restores `field_state.txt`.
   Persisted field state is copied, but does not become the next turn's active
   field through this route.
4. **Writeback is not transactional.** People, agenda, beliefs, lessons, and
   gaps can write before winner selection; a losing detector can leave state.
5. **Discord's normal `roleplay()` route lacks observer turn emission.** M16
   cannot prove complete GF selection coverage from current traces.

### Medium significance

6. **The assembled context bundle is mostly shadow.** Time, people mentions,
   recent episodes, facts, open episode questions, gaps, drives, and agenda are
   assembled each turn, but M4 consumes only `current_user`; working-context
   signals are read directly from G7.
7. **Relationship state is temporally inconsistent inside API roleplay.**
   Cached depth can be from before the current rapport observation while the
   rapport line/lane is from after it. The roleplay context also reads
   `people.txt` from the user partition before root state is copied back, so a
   same-turn people write can be absent from that auxiliary prompt context even
   though the selected engine template contains its grounded result.
8. **Persistent lessons are not a general correction mechanism.** Their text
   usually affects only review/growth phrasing unless duplicated into a belief
   or person fact.
9. **Belief trust and people importance are computed and persisted without
   production behavioral readers.**
10. **API `memory_writes` is not a reliable journal.** It reports size growth,
    not actual content mutation, and derived profile counters inherit that
    limitation.
11. **Personality and boundary truth are distributed.** There is no single
    runtime authority across packs, profiles, seeds, prompt tables, executable
    gates, and prose policy.

### Explicit unknowns

12. Whether amygdala-only perturbation can change a selected response through
    field activation is `UNKNOWN`.
13. Whether episode-only perturbation can change/guard a selected response at
    the full real seam is `UNKNOWN`; successful recall is not the M14 receipt.
14. Whether every pack's intended knobs should be runtime-active is a product
    decision; current caller evidence does not establish it.
15. Exact winner and exact post-turn conditional writes for a live message
    remain state-dependent and were not executed in this read-only audit.

## 9. Source-of-Truth Summary

| Concern | Current source of truth | Duplicates / caches |
|---|---|---|
| Current conversation | `working_memory.txt` | Episodic summaries, external channel transcript |
| Lived events | `episodic_memory.txt` | G7 turn, optional reply event, external transcript |
| Current speaker/person facts | `people.txt` | `profile.json.current_person_key/current_user_name` |
| Relationship state | `rapport.txt` | `profile.depth_stage`, episode-count fallback |
| Provisional user claims | `beliefs.txt` | Graph remains independent proof authority |
| Banked lessons | `lessons.txt` | Parseable correction duplicated to belief/person state |
| Persistent obligations | `threads.txt` | G7 "thread" is a different short-term concept |
| Stateless affect | Derived each read | Rapport mood and emotional core are separate systems |
| Personality for existing GF user | `profile.json` | Pack JSON, persona tables, identity/vault seeds, desktop constant |
| Constitutional boundary | `ukft_self.py` executable floor | Governance/product prose |
| Romance/output boundary | `ukft_boundaries.py` + roleplay prompt/post-check | `gf_boundaries.md`, profile envelope/opt-outs |
| Per-user brain state in API | `users/<id>/` between turns | Temporary root swap during turn |
| Selection record | Root basal log in desktop | Temporary/discarded on API partition route; observer incomplete |

## 10. Cross-Check Against Current Authoritative Documents

The code audit agrees with current authoritative claims that:

- G7 and narrow current-person influence are M4-proven.
- Episodic diary/recall is working but M14 remains unfinished.
- Rapport is connected to depth/prompt/mirror but not M5-proven selector
  influence.
- Mood/affect is advisory at the tested selector seam.
- Observer telemetry is observer-only.
- Nightly gist scheduling is unproven.
- The API path does not equal the full desktop lobe lifecycle.

One older root audit, `AUDIT_REPORT_COGNITIVE_PATH.md`, contains superseded
pre-M2/M4/M13 conclusions about G7/current-person/episodic connection. It is
historical evidence, not current authority, and was not rewritten.

Documentation check: no current authoritative architecture, product, policy,
roadmap, governance, or test-contract document required a truth change. This
pass adds a dedicated audit artifact and changelog record only.

## 11. Audit Limits

- Static code and current test-evidence inspection only.
- No runtime was launched.
- No tests were run because the pass made no runtime/test changes and the task
  prohibited surgery.
- No live state, user partition, observer trace, backup, launcher, character
  pack, or historical/reference artifact was modified.
- No M14 policy was designed or implemented.
- No M16 observer work was designed or implemented.
- Findings are architecture evidence, not authorization to fix them in this
  pass.

## 12. Final Determination

The GF layer is partially integrated into the UKFT brain rather than merely
wrapped around it. Its strongest in-brain integrations are G7/current-person
selection context and the explicit people/agenda/belief/teach branches.
Episodic memory already has a positive recall route through reasoning, but it
lacks the explicit boost/suppress policy and causal receipt required for M14.
Rapport, mood, personality, and romance boundaries primarily govern the final
voice after selection. Character packs are birth-time writers. Observer
telemetry is a non-causal sidecar. Writeback is real and widely read back, but
it is distributed, lossy, route-dependent, and non-transactional.

No surgery is justified by this audit alone. The findings are ready for the
Architect to choose the M14 architecture with the actual Brain<->GF boundary
visible.
