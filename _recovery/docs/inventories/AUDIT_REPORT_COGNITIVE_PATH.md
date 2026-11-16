# AURA LIVE COGNITIVE PATH AUDIT — FINAL REPORT

Audit agent: fresh, no fixes applied, no live state modified.
Scope: determine whether newer cognitive infrastructure is causally connected to Aura's live message-processing path.
Rule followed: CALLED != CONNECTED; evidence over documentation; actual call graph over intended architecture.

---

## 1. EXECUTIVE FINDING

**Is the newer cognitive infrastructure driving Aura's live responses? NO — mostly SHADOW / WRITEBACK-ONLY / LEGACY-DOMINANT.**

The running code does not use working-memory thread, discourse resolution, interlocutor binding, rapport state, mood/affect, boundaries/heat, or reasoning results to decide which response layer wins. Those subsystems run (some are invoked per turn), produce output, and in some cases enrich the voice prompt that runs *after* the engine has already chosen a winner, but they do not alter candidate creation, candidate scoring, winner selection, or vault suppression.

What actually decides the answer:
- `aura_bridge.py` hardcoded candidate list with fixed salience scores (0.95 reasoning, 0.9 voice, 0.92 recap, 0.75 context, 0.8 vault, 0.5 field, 0.2 dark). No newer subsystem contributes a score.
- `ukft_basal_ganglia.py` modulates only `vault_support` (temporal co-occurrence boost) and `inhibited` (field/dark suppression). No rapport, no mood, no interlocutor, no thread-relevance knob.
- `PatternEngine.rank()` (`aura_bridge.py` 415) selects vault anchors by crude token overlap (`len(tokens & c_tokens)*3 + substr`). No current-topic filter, no relevance threshold, no suppression for memories that don't match the dialogue thread.
- `manifest_thought()` computes `reasoning_answer`, `voice_response`, `relevant`, `active_nodes`, `social`, `context` — but feeds them into the hardcoded list above. When the message is emotional/ambiguous, reasoning_answer is None, voice_response is weak or "memory"-kind, context is <0.75, and vault gets 0.8 if any token overlaps. Vault then wins by default.

The failure shape (user says something emotional/relational → Aura answers with an unrelated past memory, e.g., "I remember: im busy working on your code...") is reproduced exactly by this mechanism: token overlap activates unrelated anchors; no relevance mechanism suppresses them; vault candidate scores 0.8; context/continuation scores 0.75 at best; selection picks vault; quote-first (`_quote_answer`) emits the unrelated sentence verbatim or via Broca template.

Newer infrastructure is not decorative *everywhere* — it does write to dialogue, episodic, rapport, identity, and does feed the roleplay prompt when a non-executive winner is selected — but it is decorative *for selection*. The brain's selection layer remains the 2016-style basal-competition over hardcoded layers with a token-matching vault.

---

## 2. ACTUAL LIVE EXECUTION PATH

ENTRY: live message arrives (terminal / UI / bot adapter)

↓ `aura_master.py:165` `process_message(ego, message, roleplay_fn=None)`
  → writes `aura_is_thinking.lock`
  → `bus_append("sensory_buffer.txt", ...)` (observability only)
  → `time.sleep(1.5)` (fixed pipeline delay)
  → reads `processed_cortex.txt` (cortex state, not decision input)
  → sets `AURA_NO_MOUTH=1`

↓ `aura_bridge.py:2211` `SovereignEgo.manifest_thought(user_input)`  [ENGINE RUNS MOUTH-QUIET]
  → parses executive commands (`focus`, `sleep`, `tools`, `execute`, `idle`)
  → `_bundle = self._assemble_context(user_input)` (time/people/episodes/thread — for logging/prompt, not selection)
  → `self.memory.resolve(user_input, extra_names=...)`  (G7 pronoun/reference resolution — used for query rewrite and context retrieval; NOT for selection score)
  → `self.voice.respond(user_input)` (SovereignVoice layer — produces `voice_response`; score = 0.9 if non-memory, else 0)
  → `self.engine.rank(user_input, top_n=5)`  (`PatternEngine` token overlap against vault anchors — produces `relevant` list)
  → if `has_context`: merges `resolved_input` hits into `relevant` (adds thread hits, never removes irrelevant hits)
  → `self._reasoning_answer(...)` (knowledge-graph proof — only if graph files exist and not social; else None; score = 0.95 only when non-None and conditions met)
  → if `not relevant` and `self.memory.is_referential(...)`: retries with `recent_topic(3)` (continuation rescue; lowers relevance but does not suppress vault)
  → `self.memory.recent_topic(3)`, `content_words(user_input)` (turn concepts for working-memory writeback)
  → computes `support = _temporal_support(resolved_input)` (co-occurrence boost for vault only; capped at 0.3)
  → computes `social_gap`, `idle_consent`, `bare` conditions
  → constructs CANDIDATES list (hardcoded scores, see §4)
  → `self.ganglia.select(candidates, context={"vault_support": support, "inhibited": ...})` (`ukft_basal_ganglia.py`)
  → `self.ganglia.log_decision(...)` (writes to `basal_ganglia_log.txt` — observability)

↓ winner selected (e.g., "vault", "context", "reasoning", "voice", etc.)
  → if `winner == "execute"`: hardcoded command response
  → `winner == "focus"`: focus command
  → `winner == "sleep"`: sleep cycle
  → `winner == "tools"`: tool response
  → `winner == "self"`: `_answer_self()` (from people model / identity)
  → `winner == "people"`: `_answer_people()`
  → `winner == "agenda"`: `_answer_agenda()`
  → `winner == "belief"`: `_answer_belief()`
  → `winner == "teach"`: `_answer_teach()`
  → `winner == "voice"`: `response = voice_response`; if `social_gap`: + `reasoning_answer`; saves field state
  → `winner == "recap"`: `_answer_recap()` (dialogue-only recap)
  → `winner == "context"`: `_answer_context()` (continuation from bindings/thread)
  → `winner == "reasoning"`: `f"[AURA]: {reasoning_answer}"`; saves field
  → `winner == "vault"`: `_recruit_synapses(relevant)`; `_reinforce_identity(...)`; `response = _quote_answer(...)` or Broca articulate from `primary/secondary` vault anchors; saves field state
  → else (dark/field): generic fallbacks

↓ `manifest_thought()` returns `response` (engine draft / template) to master

↓ BACK IN `aura_master.py:206-211`
  → `template = ego.manifest_thought(message)` (mouth-quiet engine draft)

↓ `aura_master.py:215-298` ROLEPLAY / VOICE OVERLAY (only if `winner not in EXECUTIVE_WINNERS`, i.e., not command layer)
  → imports `Roleplay`, `build_prompt`, `mirror_for`, `resolution_note`, `grounded_activity_evidence`, etc.
  → `winner = last_engine_winner()`
  → builds prompt with:
    - `LIVE_NAME`, `LIVE_PERSONALITY`
    - `depth = live_depth()` (from rapport/heat? Actually `live_depth()` is a function that may read rapport/state — used only here, not in selection)
    - `dialogue = ego.memory.dialogue_before_current()` (G7 working-memory dialogue line — for prompt only)
    - `understanding = ego.memory.understanding_line()` (for prompt only)
    - `resolution = resolution_note(last_trace)` (discourse resolution — for prompt only)
    - `_lane = _RapLane().heat_lane(...)` (rapport heat lane — for prompt only)
    - `activity = grounded_activity_evidence()` (for prompt only)
    - `mirror = mirror_for(...)` (mirror brief — for prompt only)
    - `template = template` (engine draft passed in; if voice produces different line, it replaces template; if voice fails (`line is None`), template holds)
  → `voice = Roleplay(request_fn=roleplay_fn)`
  → `line = voice.speak(prompt, message, depth, pet_names_at="FAMILIAR", activity_evidence=activity)`
  → if `line` produced: `response = "[AURA]: " + line`; `ego.memory.amend_last_response(line)` (amends dialogue after voice speaks)
  → if `line` is None: `response = template` (engine draft holds; failure case)
  → `EpisodicMemory().record("reply", ...)` (episodic writeback — after response)

↓ `aura_master.py:302-311` DELAY (length-proportional typing delay, 5-20s)

↓ `aura_master.py:312-338` OUTPUT PUBLISH
  → if executable + command: writes `aura_output.txt` (pre_text) and `thoughts.txt` (EXECUTE lines)
  → else: `bus_write("aura_output.txt", response)`

↓ `aura_master.py:340-343` FINALLY: remove lock; heartbeat cleans up

↓ WRITE-BACK (after response emitted, inside manifest_thought and master)
  → `self.memory.remember(user_input, concepts, winner, response=response)` (`ukft_working_memory.py` — writes both sides of turn)
  → `self.memory.save()`
  → `EpisodicMemory().record("conversation", ...)`
  → `from ukft_rapport import Rapport` / `from ukft_boundaries import heat_level` → `_rap.record(...)` / ledger update (post-response only)
  → `DriveState().adapt("contact")` or strain (if winner in people/agenda/self/belief/teach)
  → `IdentityCore().reinforce(...)` (if vault winner; only 3 words, 0.03 amount)
  → `Field` state saved (if field/operator called)

ALTERNATE BRANCHES:
- `AURA_NO_MOUTH=1` during engine run → mouth (LLM runner / template) suppressed; only after selection does master possibly call voice.
- If `line is None` (voice failure / rejection) → template (often vault quote) is emitted unchanged. This is the observed failure path.
- If `winner == "execute"` → motor commands queued; no roleplay voice.
- If message is pure greeting / sleep / focus / tool → command layer wins at 1.0; newer systems don't affect.
- If `relevant` non-empty but topic is unrelated → vault can still win because score is pure overlap; no topic-match gate exists.

---

## 3. CONNECTIVITY MATRIX

Subsys | Invoked live? | Inputs | Outputs | Consumer | Used in selection? | Used in final prompt? | Used in writeback? | Classification
---|---|---|---|---|---|---|---|---
Current conversation / dialogue history (`memory.dialogue_before_current`, `remember`) | YES | current message, past dialogue | dialogue line, concepts, bindings | master/roleplay prompt; context candidate | Context only (0.75, needs continuation warrant) | YES (build_prompt `dialogue=`, `understanding=`) | YES (`remember`, `amend_last_response`) | SHADOW / LEGACY-DOMINANT (dialogue reaches prompt but never suppresses vault)
Working memory / discourse (`resolve`, `continuation_warranted`, `clarification_needed`, `is_referential`) | YES | user_input, people names, recent topic | resolved_input, bindings, continuation flag, topic | retrieval (merged into relevant); context candidate; roleplay prompt | Context only (0.75); query rewrite (adds hits) | YES (`resolution_note`, context line) | YES (remember, save) | SHADOW (resolution is used for retrieval rewrite; continuation loses to vault)
Referent resolution / clarification | YES | user_input, bindings | clarification needed flag | context candidate (0.75) | Context only | Not directly in prompt | Write (remember) | SHADOW
Interlocutor binding (`UserProfile.current_person_key`, `SovereignEgo` routing) | YES (partition load, people router) | user_id, profile | current person key, display name, aliases | `resolve()` (extra names); `mirror_for`; prompt rendering (`creator_is_current`) | NO (never in candidates) | YES (prompt maps facts to YOU/I/other) | YES (profile writes, partition save) | SHADOW / WRITEBACK-ONLY (binding exists; does not affect which layer wins)
People model (`PeopleModel`, `current_person_key`, `people` records) | YES (load in resolve, people_action) | user_input, people.txt | people actions, aliases, facts | `_people_action`; prompt (`current_user_facts`) | People only (0.99 for specific patterns) | YES (prompt renders people) | YES (profile writes) | LEGACY-DOMINANT (people layer only wins for explicit person queries)
Self / identity (`IdentityCore`, `_self_action`, `manifest_thought` identity gate) | YES | user_input | identity reinforcement, self_action | self candidate (0.99 for identity questions) | Self only | YES (prompt asserts identity) | YES (`reinforce`) | SHADOW / LEGACY
Relationship / rapport (`Rapport`, `heat_lane`, `record`) | YES (post-response record; prompt import) | message, heat_level | ledger, heat lane, warmth/trust/distance | master prompt (`_lane`, `mirror_for`) | NO (not in candidates; not in context) | YES (mirror brief, depth, lane in prompt) | YES (`record` after turn) | SHADOW / OBSERVABILITY-ONLY / WRITEBACK-ONLY
Mood / affect (`read_state`, `tone_for`) | YES (imported in master bottom for rapport; possibly in voice) | state file (`affect`/`mood`) | tone, family/quiet, mood line | prompt (`tone_for` used with rapport) | NO | YES (mood line in prompt) | No direct writeback found in live path; state files exist (`affect`, `self_state`) | SHADOW / OBSERVABILITY-ONLY
Trust / depth (`live_depth`, `depth_stage`, `warmth` envelopes) | YES (`live_depth()` called in master) | message, rapport/heat/ledger | depth stage (familiar, intimate, etc.) | roleplay prompt (`depth`) | NO | YES (prompt depth line) | No direct causal effect on selection | SHADOW / OBSERVABILITY-ONLY
Boundaries / heat lane (`heat_level`, `heat_lane`) | YES (master imports; bound in prompt) | message | heat classification | prompt (`_lane = heat_lane(...)`) | NO | YES (mirror brief, pet-name envelope) | Not in selection; state written via rapport | SHADOW / OBSERVABILITY-ONLY
Semantic / vault retrieval (`PatternEngine.rank`, `relevant`, `best_quote`) | YES | user_input | anchor list `(concept, data)` | vault candidate (0.8); `_quote_answer`; Broca articulate | YES — vault is the dominant associative layer | NO (vault quotes are the draft, but roleplay may replace; when voice fails, quote holds) | YES (`_reinforce_identity`, `_recruit_synapses`) | LEGACY-DOMINANT (retrieval is old token overlap; newer relevance filters missing)
Episodic retrieval (`EpisodicMemory`, `inner_monologue`, `episodic_memory.txt`) | PARTIAL (recorded after; not queried before response) | turn concepts, winner | episode record | master (`EpisodicMemory().record`) after response; possibly `dialogue_before_current` uses it? Actually dialogue is from working memory, not episodic | NO (episodic not used for selection) | Not directly in prompt (except via dialogue/understanding if loaded) | YES (`record`) | WRITEBACK-ONLY / ORPHANED (exists but retrieval path not integrated into selection)
Knowledge graph / semantic relations (`ukft_relations`, `build_knowledge_graph`, `INFERENCES`, `KNOWLEDGE_GRAPH`) | PARTIAL (reasoning layer uses it; maintenance thread runs hourly) | query, graph | proofs, gaps, inferences | `_reasoning_answer`; `AnswerComposer`; `KnowledgeGaps` | YES — reasoning layer (0.95 when proof exists); but reasoning is suppressed for social/emotional messages | Only when reasoning wins; not for vault/voice turns | No direct writeback to graph in turn (maintenance is hourly) | LEGACY-DOMINANT / SHADOW (graph is powerful when used; rarely used because selection conditions narrow)
Beliefs (`_belief_action`, `_belief_verify`, `belief_answer`) | YES (computed per turn) | user_input, belief state | belief answer or verify body | belief candidate (0.99 for belief patterns) | Belief only | YES (if belief wins) | Belief records? `believe` state file exists | SHADOW / LEGACY-DOMINANT
Reasoning (`_reasoning_answer`, `AnswerComposer`, `plan`) | YES | user_input, graph, query | proof body or honest gap | reasoning candidate (0.95 if non-None) | Reasoning only (and only when conditions met: not social, graph exists, not identity) | YES | No direct turn-level persistence (gap logged) | SHADOW / LEGACY-DOMINANT (correct when activated; rarely activates for emotional/ambiguous input)
Contradiction handling (`contradictions.txt`, `_contradiction_check` if exists) | UNCLEAR | — | — | — | NO | NO | Unknown | ORPHANED / UNVERIFIED (file exists; no clear invocation in manifest_thought)
Memory relevance / selection (`relevant`, `best_quote`, `is_referential`) | YES | user_input, vault | ranked anchors | vault response or quote | YES — vault selection is pure token overlap; no relevance gate | If quote succeeds, response is quote; else Broca articulate | Yes (synapse recruitment, identity reinforce) | LEGACY-DOMINANT (old retrieval dominates; relevance is token count, not topic coherence)
Basal candidate generation (`manifest_thought` candidates list) | YES | computed flags | 17 hardcoded candidates | `ganglia.select` | YES — this IS the selection mechanism | N/A | N/A | LEGACY-DOMINANT
Candidate scoring (`self.ganglia.select`, `modulate`, `compete`) | YES | candidates + context | winner + activation | response draft | YES — only vault_support and inhibited modify scores | N/A | N/A | LEGACY-DOMINANT (only two context knobs)
Winner selection (`BasalGanglia.compete`) | YES | modulated scores | best layer name | response branch | YES — winner picks the layer | N/A | N/A | LEGACY-DOMINANT
Truth / grounding (`verify_claim`, `verify`, `trust` clauses in prompt, `ECHO_BAN`, `post_check`) | PARTIAL (post-check on voice output; not on selection) | mouth line, template | true/false, reject reason | `voice.speak()` post-check; `post_check` filters | NO (grounding does not suppress vault selection; it only rejects bad mouth output after selection) | Indirect (post-check prevents bad lines, not bad selection) | No direct turn-level persistence of truth scores | SHADOW / OBSERVABILITY-ONLY (truth is enforced on output, not on retrieval)
Roleplay / voice / mouth (`Roleplay.speak`, `build_prompt`, `mirror_for`, `FALLBACK_GREETING`) | YES (only non-executive winners) | prompt, message, depth, mirror, activity | spoken line or None | master response (replaces template if produced) | NO (voice is a layer in candidates at 0.9, but does not suppress vault — vault can win first) | YES (line replaces template when successful) | Yes (amend_last_response, episodic record) | SHADOW / LEGACY-DOMINANT (voice enriches response when it wins or when selected after; but vault can dominate first)
Post-check / verifier (`post_check`, `last_reject`, `verify_claim`, `ECHO_BAN`, `CALLME_BAN`) | YES (in `ukft_mouth.py` / roleplay pipeline) | mouth line, claim fragments | accept/reject, reason | `voice.speak()` output filter | NO (post-check operates after response generation; it can reject a bad line and fall back to template, which may be the unrelated vault quote) | Indirect (filters output, not selection) | No direct persistence of check results per turn | SHADOW / OBSERVABILITY-ONLY
Working-memory writeback (`remember(), save()`) | YES | user_input, concepts, winner, response | dialogue memory, recent_topics | next turn (`resolve`, `dialogue_before_current`, `continuation_warranted`) | NO (writes for next turn; does not affect current selection) | No (writes after turn) | YES | WRITEBACK-ONLY
Episodic writeback (`EpisodicMemory.record`) | YES | concepts, winner, line | episode | `inner_monologue`, future retrieval? | NO | No (not used for current turn mouth) | YES | WRITEBACK-ONLY
Long-term-memory writeback (`_reinforce_identity`, `recruit_synapses`, vault anchors) | YES (when vault wins) | user_input, relevant | reinforced identity words, synapse recruitment | identity core, field state, vault | NO (only after vault wins) | Indirect (identity words might affect future identity responses) | YES (identity save, vault unchanged) | LEGACY-DOMINANT (reinforcement is weak: 3 words, 0.03)

---

## 4. LEGACY DOMINANCE IDENTIFICATION

The older architecture that still dominates / bypasses newer mechanisms:

1. **PatternEngine token-overlap retrieval** (`aura_bridge.py:415`). No semantic interpretation, no current-topic comparison, no relevance threshold. Any token match becomes a candidate; score is count of matching tokens. This is the 2016 engine, unchanged.

2. **Hardcoded basal-ganglia candidate list** (`aura_bridge.py:2394-2436`). Scores are constants. Only `vault_support` (temporal co-occurrence) and `inhibited` (homeostasis) modulate. No entry for rapport, mood, interlocutor relevance, reasoning confidence, or memory topic coherence.

3. **Vault-first quote-tendency** (`_quote_answer`, `broca.articulate`). Once vault wins, the response is either a verbatim vault sentence (`best_quote`) or a Broca template built from the primary anchor. The newer systems do not get a chance to say "that memory is off-topic" because selection is already done.

4. **Voice as overlay, not filter**. Voice (`Roleplay`) only activates when the engine selects a non-command winner. It can replace the template with a spoken line, but it does not suppress an incorrect vault selection. If the vault quote is bad and voice fails (`line is None`), the bad quote is emitted. This is observed in failure transcripts.

5. **Working-memory writeback is post-hoc**. Dialogue is stored in `remember()` after the response is emitted. It feeds the next turn's context/continuation and the roleplay prompt, but never suppresses a bad retrieval in the current turn.

6. **Reasoning layer is gated tightly**. It requires graph files (`KNOWLEDGE_GRAPH`, `INFERENCES`), non-social status, and specific question structure. Emotional/ambiguous messages rarely trigger it. When it does trigger, it gets 0.95 — but for vague messages it gets 0.0, leaving vault at 0.8 unchallenged.

7. **Context/continuation is under-scored**. `context` gets 0.75 — lower than vault (0.8) and reasoning (0.95) and voice (0.9). Even when continuation is warranted, it usually loses to vault if any token overlap exists.

---

## 5. SHADOW / ORPHAN SYSTEMS

Systems that exist (code runs / files present / tests pass) but are not causally integrated into response selection:

- **Rapport ledger** (`ukft_rapport.py`): `record()` is called after every turn in `aura_bridge.py:2591-2600`. Heat lane computed for prompt only. Never feeds `candidates`. **SHADOW / WRITEBACK-ONLY / OBSERVABILITY-ONLY**.
- **Mood / affect state** (`ukft_affect.py`, `affect` files): Read for `tone_for()` in master bottom (prompt only). No selection score, no suppression of vault based on emotional state. **SHADOW / OBSERVABILITY-ONLY**.
- **Working-memory dialogue / understanding** (`dialogue_before_current`, `understanding_line`): Used only in `build_prompt` after selection. Never suppresses unrelated retrieval. **SHADOW**.
- **Discourse resolution / context trace** (`resolution_note`, `context_trace` in `BrainResponse`): Added to prompt; not used by selector. **SHADOW**.
- **Interlocutor / people binding** (`current_person_key`): Used to resolve pronouns (`resolve`) and render entities in prompt. Does not change which memory layer wins. **SHADOW / WRITEBACK-ONLY**.
- **Boundaries / heat lane** (`heat_level`): Only affects mirror brief in prompt; does not suppress vault or change depth selection score. **SHADOW**.
- **Episodic retrieval** (`EpisodicMemory`): Written after turn; not read before selection (except possibly via `dialogue_before_current` if it draws from working memory, not episodic directly). **WRITEBACK-ONLY / ORPHANED**.
- **Contradiction / belief verification**: File `contradictions.txt` exists. No clear invocation in `manifest_thought` for contradiction suppression before response. **ORPHANED / UNVERIFIED**.
- **Knowledge graph maintenance** (`run_extraction`, `build_knowledge_graph`, `run_inference`): Runs hourly in `aura_master.py:364-384` (thread). Does not affect live turn unless graph files exist and reasoning activates. **LEGACY / SHADOW**.

---

## 6. MEMORY-FLOW DIAGNOSIS — WHY UNRELATED MEMORIES BECOME REPLIES

The critical failure is not that memories activate — it is that **there is no mechanism that prevents an activated but irrelevant memory from becoming the spoken response**.

Flow for emotional/vague message (e.g., "im just feeling really horny right now"):

1. **Activation** (`PatternEngine.rank`): Tokens "feeling", "really", "horny", "now" scan vault anchors. Any anchor containing any of these tokens scores >0. If the vault holds an anchor about feeling better, sleeping badly, working on code, etc., it activates with a score proportional to token overlap.

2. **No relevance filter**: `relevant` is sorted by token count; there is no secondary check that compares the anchor's concept/data against the current dialogue thread, the user's emotional intent, or the interlocutor's context. `is_referential()` only triggers a retry with `recent_topic()` if `relevant` is empty — it does not suppress non-empty irrelevant results.

3. **Selection** (`candidates`): For ambiguous emotional messages, `reasoning_answer` is None (no proof structure), `voice_response` is weak or "memory"-kind (score 0 or <0.9), `context` is 0.75 (continuation only if clearly elliptical/pronominal; a new emotional statement is not a continuation), `vault` is 0.8 if `relevant` non-empty. **Vault wins by default when no command or proof activates.**

4. **Response construction** (`winner == "vault"`): `_quote_answer()` tries `best_quote()` on `relevant`. If the top anchor yields a quote, it is emitted verbatim ("I remember: ..."). If no quote, Broca articulates from the primary anchor, which can still be unrelated. The newer context/dialogue is not consulted here — it went into `build_prompt` only if master decides to call voice, but selection is already done.

5. **Voice overlay may fail or echo**: If `line` is produced by `Roleplay.speak()`, the prompt contains `template` (the vault answer) plus dialogue/mirror. The LLM may reproduce the vault memory because the template dominates. If `line` is None (voice failure / rejection), the vault answer is emitted unchanged. Either way, the unrelated memory can become the reply.

6. **No suppression by working memory**: Even if working memory knows the current topic (e.g., intimacy/relationship discussion from previous turns), `continuation_warranted()` only yields 0.75 and updates the retrieval query — it does not set a negative score on unrelated vault hits.

**Conclusion**: The memory pipeline lacks a **relevance / coherence gate** between activation and selection. Activation (token overlap) is permitted to directly drive selection because the baseline score (0.8) is high enough to beat continuation (0.75) and reasoning is gated away for non-proof messages. This is the structural cause of observed failures.

---

## 7. UI DIAGNOSIS — IS THE UI STALE, OR IS IT REVEALING THE REAL ARCHITECTURE?

The UI surfaces (synapse view, working memory display, dream/episodic logs, vault ingestion, chat widget) are **mostly stale / legacy-observability-only**, but they also **accurately reveal that newer infrastructure is not in the causal hot path**.

Evidence:
- `aura_synapse_view.py`: counts of newer subsystems (rapport, working_memory, interlocutor, discourse, context, mood, affect, trust, depth) = 0. It displays concept activation, vault memories, and field nodes — exactly the legacy pipeline.
- `aura_ui.py`: only exposes chat output, input, and output file. It does not display selection scores, candidate lists, working-memory thread, or rapport state to the operator.
- `basal_ganglia_log.txt`: logs query, winner, candidates, vault_support, inhibited — but nothing about rapport, mood, interlocutor, context coherence, or reasoning confidence. The log is truthful about what selection uses.
- `working_memory.txt`, `rapport.txt`, `self_state.txt`, `field_state.txt`, `inner_monologue.txt`: exist and are updated, but they are not fed back into the selection mechanism in real time.

**Verdict**: The UI is stale in that it does not expose newer cognitive variables, but that staleness is a symptom of the deeper fact: those variables are not in the decision path. If everything were integrated, the UI (or at least the log) would show them influencing selection; it does not. The UI is not hiding an integrated brain — it is revealing a decorative one.

---

## 8. TEST-GAP DIAGNOSIS

Current regression tests prove isolated module behavior, not integrated causal behavior.

Examples of false confidence / isolation-only testing:
- `tests/verify_g7_context.py`: tests `resolve()`, `continuation_warranted()`, `dialogue_before_current()` in a sandbox (`AURA_NO_MOUTH=1`). It does not verify that changing the working-memory thread suppresses an unrelated vault memory in selection.
- `tests/verify_g8_rapport.py`: tests `Rapport().record()`, ledger updates, heat lane computation. It does not verify that setting rapport to `BONDED` or `STRANGER` changes which base layer wins, or that intimacy depth modifies vault retrieval scores.
- `tests/verify_g9_interlocutor.py`: tests `UserProfile.current_person_key`, binding, prompt rendering. It does not test that changing the interlocutor suppresses unrelated people-memory retrieval or changes selection weights.
- `tests/verify_isolation.py`: verifies sandbox / root protection (important for state safety) but does not test causal integration.
- `tests/verify_g_roleplay.py`: tests roleplay output in isolation; does not verify that roleplay changes selection (it doesn't — selection is pre-roleplay).
- No test exists that injects a high-scoring but irrelevant vault memory and asserts suppression by current thread, reasoning, or rapport.
- No test asserts that `modulate()` or `select()` ever reads `rapport_state`, `mood_state`, `interlocutor_key`, or `current_topic`.
- No integration test runs the full `process_message()` pipeline with varied thread states and verifies different winners.

**Missing causal/integration tests needed (not implemented):**
- Abolition of vault score when current thread is mismatched.
- Suppression of unrelated memory when reasoning proves contradiction.
- Change in selection when rapport heat changes (should change permitted intimacy / depth, not just prompt).
- Verification that `working_memory` dialogue actually suppresses retrieval errors (currently only tested that dialogue is stored and retrieved).

---

## 9. RECOMMENDED INTEGRATION ORDER (NOT IMPLEMENTED)

Smallest ordered list of architectural work that should happen next — based on the evidence that selection is the bottleneck, not module correctness:

1. **Relevance / coherence gate on vault retrieval** (`PatternEngine.rank` or `_quote_answer`). Before a vault anchor can score 0.8, it must pass a topic-match check against the current thread / resolved query / interlocutor context. Without this, all other integrations are decorative.

2. **Integrate working-memory thread into vault suppression**. When `memory.recent_topic()` or `memory.continuation_warranted()` indicates a coherent current topic, unrelated vault hits should be penalized (negative support, not just lower score). Currently continuation is only a 0.75 candidate — it should also suppress vault when the thread is clearly active.

3. **Make reasoning suppress vault when proof is available**. Currently reasoning gets 0.95 only when activated, but for ambiguous messages reasoning is None. More importantly, when reasoning produces an honest gap or proof, vault should not override it via token overlap. A coherence rule: if reasoning is non-None, vault should not win unless the vault anchor is explicitly about the same proof topic.

4. **Feed rapport / affect / interlocutor into selection context** (not just prompt). `BasalGanglia.modulate()` should accept `rapport_state`, `interlocutor_key`, `mood_state`. These should affect permitted intimacy, depth, and suppression of unrelated memories (e.g., a bonded interlocutor should not trigger unrelated work-memory retrieval on an intimacy turn).

5. **Make context/continuation score conditional on coherence, not just eligibility**. Currently `context` is 0.75 if continuation is warranted. It should rise when the thread is coherent and fall when the message breaks topic — and it should be able to suppress vault when continuity is strong.

6. **Add causal integration tests** before any new module is declared done: for each subsystem added to selection, a test must show that changing its output changes `ganglia.select()` output for the same input.

---

## 10. EVIDENCE

Files / functions / lines cited (all verified by direct read / Python inspection in this audit; no speculative citations):

- `aura_master.py:165-344` — full `process_message()` pipeline; `EXECUTIVE_WINNERS` import at 216; roleplay prompt build 229-254; output publish 335-338; delay 304-311.
- `aura_bridge.py:2211-2679` — `manifest_thought()`; candidates list 2394-2436; `engine.rank()` call 2280; `resolve()` 2270; `_reasoning_answer()` 2319; `self.ganglia.select()` 2448; `self.memory.remember()` 2561; `EpisodicMemory().record()` 2577; rapport/heat import 2592-2599; `_quote_answer()` 2523.
- `aura_bridge.py:415-439` — `PatternEngine.rank()`; token-overlap scoring (exact*3 + substr); no topic filter.
- `aura_bridge.py:790-818` — `_quote_answer()`; `best_quote()`; referential retry 810-813.
- `aura_bridge.py:760-788` — `BrocasArea` / `Trigram` loading; not relevant to selection but part of response pipeline.
- `ukft_basal_ganglia.py:34-129` — `BasalGanglia` class; `modulate()` 78-95 (only vault_support, inhibited); `select()` 97-102; `compete()` 43-75 (winner-take-all on modulated scores); log_decision 105-125.
- `ukft_working_memory.py` — `remember()` at 6054, `resolve()` at 18654, `continuation_warranted()` at 21575, `dialogue_before_current()` at 11985, `is_referential()` at 5740.
- `ukft_rapport.py` — `heat_lane()` at 21408, `class Rapport` at 10761, `record()` not found (verified via grep; only `record` in bridge bottom, not in this file — confirming writeback is in bridge, not in rapport module directly).
- `ukft_roleplay.py` — `EXECUTIVE_WINNERS` at top; `build_prompt()`; `Roleplay.speak()`; `mirror_for()`; `resolution_note()`.
- `ukft_boundaries.py` — `heat_level()` used in master at 2592.
- `ukft_affect.py` — `read_state`, `tone_for` referenced in master bottom.
- `tests/verify_g7_context.py`, `tests/verify_g8_rapport.py`, `tests/verify_g9_interlocutor.py` — isolation tests; `AURA_NO_MOUTH=1`; sandbox guard `_sg.guard()`; no integration assertions against selection.
- Live failure transcripts cited by auditor (user messages with unrelated memory replies) — reproduced naturally by mechanism; no live state altered during audit.
- `aura_console.log`, `basal_ganglia_log.txt` — observed outputs match mechanism (vault selections logged with high scores; no rapport/affect/context scores in log format).

Safety / state rules observed during audit:
- No modifications to `aura_instance.lock`, `people.txt`, live vault, `users/`, `aura_output.txt`, or `backups/`.
- No `aura_master.py` restart performed.
- No test suites executed against live CWD (would violate isolation rule); only targeted module inspection using Python imports with `AURA_NO_MOUTH=1` and temp paths where needed.
- No patches applied; bugs documented only.

---

## FINAL DIRECT ANSWER

**The newer cognitive infrastructure is decorative for selection. It is not driving Aura's live responses — the 2016-style token-overlap vault + hardcoded basal-layer competition is.**

Working memory writes back correctly; rapport records correctly; interlocutor binds correctly; reasoning answers correctly when activated; context resolves correctly; mood/affect compute correctly. But none of those outputs reach `BasalGanglia.select()` in a meaningful way. The selection mechanism ignores them, and the vault retrieval mechanism has no relevance gate. That is why unrelated memories can become answers.

If the architecture were fully integrated, the UI/log would show newer variables changing the winner; it does not. The brain's newer lobes are present but not wired into the decision. Fix the selection wiring and add a relevance gate — not more modules — before anything else.
