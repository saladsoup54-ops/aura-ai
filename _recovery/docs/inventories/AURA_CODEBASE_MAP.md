# AURA CODEBASE MAP — actual live wiring (19 Sept 2026, read-only)

> Rule used throughout: called != connected. CONNECTED requires evidence the
> output is consumed downstream (state write, bus message consumed, return
> value used, branch taken). Nothing here was executed or changed.

## 1. Turn pipeline (boot → writeback)

| stage | module:function | reads | writes | status — evidence |
|---|---|---|---|---|
| boot | `aura_master:__main__` + `aura_state:check_startup` + lock/lobes | `aura_constants:D_INVARIANT`, env roots | console log, `aura_instance.lock`, 20+ lobe threads, field files | CONNECTED — test-mode boot refused; lock gates second organism |
| input | master terminal/Discord/API (`process_message`, `handle_message`, `ask/roleplay`) | `ui_input.txt`, Discord events, text arg | `sensory_buffer.txt`, `last_architect_input.txt`, thinking lock, observer turn_start/input | CONNECTED — partition swap then `ego.manifest_thought` under one lock |
| attention | thalamus/reticular/PFC/sleep gates + bridge inhibitors | sensory/hypo/PFC signals, temporal links | `cortex_inbox.txt`, field stimulation, focus/sleep candidates | PARTIAL — background path real but live turn never calls thalamus; only inhibitors + executive candidates land |
| context | G7 dialogue resolution + `_assemble_context` + prompt `resolution_note` | WM deque, people, episodes, threads, gaps, self | resolved bindings, `last_trace`, `context` 0.75 candidate | CONNECTED (dialogue) + SHADOW (`self._bundle` computed, never read) |
| working memory | `remember/amend/save/load`, dialogue windows | `working_memory.txt` | WM file, trace context/thread | CONNECTED — resolved query adds vault hits; roleplay consumes dialogue |
| memory activation | voice/respond + `PatternEngine.rank` + 12 detectors | vault, field, graph, people, threads, beliefs, episodes | candidate scalars (voice .9, vault .8, reasoning .95, people/self/agenda/belief/teach .99, recap .92, context .75, field .5, dark .2) | CONNECTED — all feed `ganglia.select`; support zeroed under proof wins |
| memory selection | question plans, composer, recall router, belief verify, quote-first | graph/inferences, episodes, beliefs, anchors | reasoning/recall/belief/quote answers; gap plans | CONNECTED — proof beats association; honest gaps logged |
| reasoning | extraction → graph build → inference + hourly maintenance | vault → relations → graph → inferences | rebuilt proof files; per-turn intent plan | CONNECTED (slow file-mediated loop + per-turn QA run) |
| candidate generation | candidate list + `basal_ganglia.modulate` | vault support, inhibitors | modulated list (support capped, field/dark halved) | CONNECTED — direct input to `compete` |
| route/competition | `basal_ganglia.compete/select/log_decision` | candidates, hysteresis 0.05, beta 0.5 | winner + salience + log line | CONNECTED — winner drives answer branch; log feeds roleplay + viewer |
| winner | 15-way winner branch (execute/focus/sleep/tools/idle/self/people/agenda/belief/teach/voice/recap/context/reasoning/vault/field/dark) | winner + action stores | response + side writes (field, tools queue, agenda, belief, people) | CONNECTED — executives mirrored so roleplay never voices them |
| grounding | mouth verify + roleplay prompt/post-checks + boundaries + activity evidence | proof facts, people terms, thread words, monologue window, envelopes | verified line or template fallback; mirror brief | CONNECTED — explicit deflects at any depth |
| mouth | engine Mouth (:11434) / roleplay runner (:11436 CPU) / TTS / template | prompt facts only | spoken `[AURA]: …` line | PARTIAL — fires only on memory-backed / non-executive wins; daemons fail → template |
| final response | process_message tail / ask return / Discord send / bubbles | response, winner, depth, bubbles | `aura_output.txt`, BrainResponse, Discord chunks, typing sleeps | CONNECTED — motor ONLY on execute winner; roleplayed line amended pre-writeback |
| writeback | WM + episodic + rapport + gaps + identity + field + basal log + observer + partition sync-back | turn query/concepts/winner/response | 9 files + trace + partition restore | WRITEBACK ONLY in-turn, CONNECTED across turns |

## 2. Subsystems

| subsystem | causal role | status |
|---|---|---|
| people/interlocutor | partition-USER binding; 0.99 branch; YOU/AURA/other prompt mapping | CONNECTED |
| rapport/mood/boundaries | ledger→stage→depth/prompt; heat-gated mirror; explicit deflects | CONNECTED (ledger) + PARTIAL (mood/mirror advisory; audit in trace only) |
| beliefs | assertion contests; VERIFY fallback, never overrides proof | CONNECTED |
| identity | founding floor + reinforcement | WRITEBACK ONLY (never read by turn) |
| episodes | turn diary; time/person/topic recall fills proven-nothing | CONNECTED |
| lessons | corrections + review contests | CONNECTED |
| graph/inference/contradictions | R1→R3 proof layer; honest ignorance wins | CONNECTED (contradictions PARTIAL — counted, not gating) |
| background cognition | idle sense-making; sleep gates; gist re-ingest | PARTIAL (ambient/sleep) + SHADOW/ORPHANED (DMN/dream/gist — gist has NO scheduler) |
| web/wiki/PDF intake | accretion → canonical ANCHOR writes | WRITEBACK ONLY (slow loop); `discoveries.txt` unread |
| decay/forgetting | trace decay, silent-node forget, recombination lock | CONNECTED destructively + PARTIAL (no turn rehearsal) |
| actions/tools/motor | confirm-gated tools; EXECUTE queue | CONNECTED (live loop) + PARTIAL (API path has no motor consumer) |
| observer/telemetry | 8 turn-boundary event types; viewer + export consume | OBSERVER ONLY (deletable by design) |
| Discord | DMs/mentions/channels, cooldown, operator cmds, bubbles | CONNECTED when token present (never deployed) |
| partitioning | root swap + field clear + deque reload under `_ask_lock` | CONNECTED, PARTIAL by design (global engine files shared) |

## 3. SHADOW findings (computed, never consumed)

`bridge._bundle` (full context bundle) · FIELD Hebbian graph (display only;
selection never follows edges) · parietal lobe + inbox/links · hippocampus
(episodes bypass it) · DMN/dream narrative · `trigram` speak path (generator
rebuilt, never selected) · observer `reasoning_output_consumed`,
`memory_*`, `candidate_*`, `grounding_*`, `system_output_consumed` schema
(defined, never emitted — viewer derives SHADOW from a pair the brain never
fires together) · `ukft_grammar.GrammarSkeleton` (instantiated, never
invoked) · `rapport_audit` verdicts, `DriveState.adapt`, identity
`reinforce` returns (written, never re-read for selection).

## 4. ORPHANED findings (no caller on any live path)

`gist_user/gist_episodes` (CLI/test only) · `run_discovery`→`discoveries.txt`
· trigram realizer call sites · `cognitive_observatory.html`/pngs (artifacts)
· `aura_ui.py`, `aura_diagnostic.py`, one-shot scripts, `_legacy/`.

## 5. LEGACY-DOMINANT findings (old system still owns the path)

thalamus→cortex→vault assimilation chain (turn ranks vault directly) ·
engine template voice (runner speaks only on narrow wins) · boot TTS/
presence/motor lobes (not on the partitioned API path) · hardcoded
selection hierarchy + saliences (see RULE_AUDIT M-rules).

## 6. Connection-status tally (important connections)

CONNECTED 28 · PARTIAL 9 · SHADOW 9 · WRITEBACK ONLY 5 · LEGACY DOMINANT 4 ·
OBSERVER ONLY 2 (emitter, viewer/export) · ORPHANED 6 · UNKNOWN 0 claimed
(everything above has file:line evidence in the census pass notes).
