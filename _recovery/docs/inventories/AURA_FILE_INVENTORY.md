# AURA FILE INVENTORY — every file, classified (19 Sept 2026, read-only)

> Method: contents + cross-references inspected (`import`, filename mentions,
> readers/writers traced); no file executed. Confidence HIGH unless marked.
> Classes: runtime / state / test / observer / UI / doc / generated / legacy /
> reference. Recommended actions: KEEP / ARCHIVE CANDIDATE / REFERENCE / REVIEW.
> NOTHING was moved, deleted, or changed to produce this file.

## A. GF-new + safety-critical core (runtime, HOT, KEEP, risk HIGH)

| path | purpose | subsystem | reads / writes | hot | persist | part | pre-GF | risk/action/conf |
|---|---|---|---|---|---|---|---|---|
| `aura_master.py` | Boot, heartbeat, 20+ lobes, live turn + roleplay wiring | boot/turn | reads all lobes+state; writes logs, output, observer events | yes | no | no | SAME NAME, diverged (observer emits, execute-only motor, typing stagger) | HIGH/KEEP/HIGH |
| `aura_bridge.py` | SovereignEgo: detectors, selection branches, answers, trace | turn core | reads vault/field/graph/people/etc; writes response + side stores | yes | no | no | SAME NAME, diverged (context 0.75, interlocutor, reply-exclusion) | HIGH/KEEP/HIGH |
| `aura_bus.py` | Race-free cross-lobe message bus | infra | used by ~all lobes | yes | no | no | SAME NAME, preserved | HIGH/KEEP/HIGH |
| `aura_constants.py` | D_INVARIANT, thresholds, every file contract | infra | imported repo-wide | yes | no | no | SAME NAME, preserved | HIGH/KEEP/HIGH |
| `aura_state.py` | Live-vs-test roots, `LiveRootAccessError`, gates, hashes | safety | read by runner/guard/brain_api/observer | yes | no | no | GF-ONLY (zero AURA hits) | HIGH/KEEP/HIGH |
| `aura_vault_io.py` | Vault parser/writer, dedup, `append_anchor` (sole writer) | vault | writes `locked_patterns.txt` | yes | no | no | SAME NAME, preserved | HIGH/KEEP/HIGH |
| `ukft_brain_api.py` | `ask()` serialized API, partitions, rapport/depth, interest-share | GF API | reads/writes `users/<id>/`; hottest GF path | yes | no | yes | GF-ONLY | HIGH/KEEP/HIGH |
| `ukft_user_state.py` | Per-user partitions + profiles | GF G1 | owns `users/` tree | yes | no | yes | GF-ONLY | HIGH/KEEP/HIGH |
| `ukft_roleplay.py` | Persona voice prompt + post-checks + bubbles | GF G3/G7/G9 | called by brain_api/master; reads depth/people/rapport | yes | no | yes | GF-ONLY | HIGH/KEEP/HIGH |
| `ukft_rapport.py` | Rapport ledger/stages/moods/heat (replaced depth ruler) | GF G8 | reads/writes `rapport.txt` + partitions | yes | no | yes | GF-ONLY | HIGH/KEEP/HIGH |
| `ukft_boundaries.py` | G5 enforcement (`gf_boundaries.md` as code) | GF G5 | read by brain/roleplay | yes | no | no | GF-ONLY | HIGH/KEEP/HIGH |
| `observer_telemetry.py` | Fail-open per-turn event emitter | observer | writes `observer_trace/` only; never cognition | yes | no | yes | GF-ONLY | MED (deletable by design)/KEEP/HIGH |
| `aura_field.py` | Hebbian field nodes/phases/entropy | field | read by bridge/viewer; writes field files | yes | no | no | SAME NAME, preserved | MED/KEEP/HIGH |
| `aura_cortex.py` | Cortical judgement pipeline | cortex | run by master | yes | no | no | SAME NAME, preserved | MED/KEEP/MED |
| `aura_motor.py` | Motor queue, execute-winner only | motor | drains `EXECUTE:` queue | yes | no | no | SAME NAME, preserved | MED/KEEP/MED |
| `ukft_mouth.py` | Verified surface realizer (Ollama/template) | mouth | used by c9/roleplay | yes | no | no | SAME NAME, preserved-ish | MED/KEEP/MED |
| `ukft_pack.py` | Character-pack loader/validator | GF G2 | reads `characters/*` | onboarding | no | yes | GF-ONLY | MED/KEEP/HIGH |
| `ukft_discord.py` | Stdlib Discord gateway+REST (needs token) | GF G4 | calls brain_api; hermetic-tested only | no | no | yes | GF-ONLY | MED/KEEP/HIGH |
| `ukft_delight.py` | Volunteered true history/standings (read-only) | GF G6 | reads episodes/vault | yes | no | no | GF-ONLY | LOW/KEEP/HIGH |
| `ukft_gist.py` | Nightly gist re-ingest (operator CLI; NO scheduler/caller) | GF G6 | writes vault via contract | no | no | no | GF-ONLY | LOW/KEEP (non-causal)/HIGH |
| `ukft_growth.py` | Growth readout + mirror brief scaling | GF G6 | pure reads; brief via roleplay | brief | no | no | GF-ONLY | LOW/KEEP/HIGH |
| `ukft_console_log.py` | Stdout/stderr tee | observability | writes `aura_console.log` | yes | no | no | SAME NAME | LOW/KEEP/HIGH |

## B. Inherited engine lobes (runtime, SAME NAME in AURA, preserved; KEEP; risk MED; conf MED — headers spot-checked)

| path | purpose | reads / writes |
|---|---|---|
| `ukft_affect.py` | Affect/mood mapping (F-track) | read by bridge/roleplay |
| `ukft_agenda.py` | Agenda/threads manager | threads store |
| `ukft_ambient.py` | Ambient watch lobe | run by master; senses-only alerts |
| `ukft_amygdala.py` | Emotional monitor lobe | run by master |
| `ukft_answer.py` | Answer composition (R-track) | read by bridge |
| `ukft_backup.py` | Snapshot lobe + CLI semantics | writes `backups/` |
| `ukft_basal_ganglia.py` | Competitive-inhibition selector | winner + `basal_ganglia_log.txt` |
| `ukft_belief.py` | Belief/trust store | `beliefs.txt`, `pending_belief.txt` |
| `ukft_cerebellum.py` | Cerebellum background loop (no turn reader — SHADOW) | run by master |
| `ukft_context.py` | Context assembly (`_bundle` SHADOW — computed, unread) | stores (reread directly) |
| `ukft_directed_synapse.py` | Directed synapse helper (unwired) | — |
| `ukft_discovery.py` | Discovery lobe → `discoveries.txt` (no turn reader — ORPHANED) | run by master |
| `ukft_dmn.py` / `ukft_dream_state.py` / `ukft_inner_monologue.py` | DMN/dream/monologue loops (tails only, exc. 15-min thought check) | `inner_monologue.txt`, `dream_log.txt` |
| `ukft_ebbinghaus.py` | Forgetting-curve decay (no turn rehearsal — PARTIAL) | `ebbinghaus_traces.txt` |
| `ukft_entropy.py` | Entropy cycle lobe (unwired) | run by master |
| `ukft_episodic.py` | Episodic record/recall | `episodic_memory.txt` |
| `ukft_eval.py` | Evaluation harness | test-adjacent |
| `ukft_gaps.py` | Knowledge-gap log + curiosity | `knowledge_gaps.txt` |
| `ukft_grammar.py` | Grammar skeleton (instantiated, never invoked — unwired) | — |
| `ukft_hippocampus.py` | Active-memory lobe (episodes bypass it — SHADOW) | run by master |
| `ukft_hypothalamus.py` | Homeostasis/tension | `hypothalamus_signal.txt` |
| `ukft_identity.py` | Self-modifying identity (WRITEBACK ONLY) | `identity_core.txt` |
| `ukft_inference.py` | Inference engine w/ proof trails | `inferences.txt` |
| `ukft_knowledge_graph.py` | Graph store rebuild | `knowledge_graph.txt` |
| `ukft_memory_vault.py` | Vault stabilization | vault |
| `ukft_parietal_lobe.py` | Parietal loop (no importer — SHADOW) | `parietal_links.txt` |
| `ukft_pdf_intake.py` | PDF intake (`pdf_intake/`→`pdf_processed/`, both empty) | vault |
| `ukft_people.py` | People model | `people.txt` |
| `ukft_perpetual.py` | Preflight/caps engineering | boot checks |
| `ukft_pfc.py` | PFC focus lobe | `pfc_focus.txt`, `pfc_signal.txt` |
| `ukft_policy.py` | Conversational policy (question-back, daypart) | prompt text |
| `ukft_presence.py` | Boot briefing composer | `aura_output.txt` |
| `ukft_question.py` / `ukft_quote.py` | Question plans / quote-first fallback | reasoning branch |
| `ukft_recall.py` | Recall router (G7 routing-ink strip) | episodes/people/vault |
| `ukft_register.py` | Register/style overhaul | register text |
| `ukft_relations.py` | Relation extraction | `extracted_relations.txt` |
| `ukft_reticular.py` | Source classification | attention path |
| `ukft_self.py` | Self-model | `self_state.txt` |
| `ukft_sleep.py` | Sleep/wake cycle | `sleep_state.txt`, `sleep_log.txt` |
| `ukft_spontaneous.py` | Spontaneous output (unwired beyond lobe) | run by master |
| `ukft_synapse.py` | Synapse cycle lobe (unwired) | run by master |
| `ukft_teach.py` | Lesson ledger + review | `lessons.txt` |
| `ukft_temporal_lobe.py` | Temporal co-occurrence | `temporal_links.txt` |
| `ukft_thalamus.py` | Sensory gate (turn bypasses it — LEGACY DOMINANT) | `cortex_inbox.txt` |
| `ukft_time.py` | Time/situation resolution | episodes window |
| `ukft_tools.py` | Tool registry, confirm-gated | `pending_action.txt`, `action_log.txt` |
| `ukft_trigram.py` | Vault-trained trigram (speak path ORPHANED) | `trigram_model.txt` |
| `ukft_voice.py` | Voice/TTS paths (boot lobes legacy-dominant on API path) | voice tail |
| `ukft_working_memory.py` | Turns + G7 dialogue resolution (QUERY+RESP) | `working_memory.txt` |
| `aura_ui.py` | Tkinter chat face (reads `aura_output.txt`, writes `ui_input.txt`) | UI / not on turn path |
| `aura_synapse_view.py` | Pygame connectome + EXPORT DIAGNOSTICS (observer-only) | UI/observer; writes `diagnostics.txt` only |
| `aura_diagnostic.py` | Read-only system sweep | observer |
| `aura_vocal_manifest.py` | Vocal manifest lobe (unwired) | run by master |

## C. Spent one-shot scripts (test class, zero code references, ARCHIVE CANDIDATE, risk LOW exc. noted)

| path | purpose | pre-GF | risk note |
|---|---|---|---|
| `add_delay.py` | Inserts typing-delay into master (already inline) | GF-only | LOW |
| `add_feature1.py` | Unfinished interest-share patcher | GF-only | LOW |
| `fix_latency.py` / `fix_spec.py` / `update_spec.py` / `update_spec2.py` | Spec Latency-line rewrites (overlapping; one truncates) | GF-only | LOW (rerun corrupts spec line) |
| `fix_syntax.py` | One-paren fix in brain_api (spent) | GF-only | LOW |
| `merge_code.py` | Concats root `.py` (output absent = never run) | SAME NAME in AURA | LOW |
| `modify_return.py` / `modify_return2.py` | Interest-share return-line patchers (twins) | GF-only | LOW |
| `patch_g7.py` | Rewrites 3 strings in verify_g7 (spent) | GF-only | LOW |
| `test_flow.py` / `test_flow2.py` / `test_flow3.py` | Live-`ask` probes, repo-CWD pattern (BANNED pattern) | GF-only | MED (rerun writes live state) |
| `update_agents.py` / `update_agents2.py` | AGENTS.md rewriters (twins, spent) | GF-only | LOW |

## D. Launchers (runtime, operator hot path, KEEP, HIGH/MED)

`Boot_Aura.bat` (console boot) · `Launch_Aura.bat` (core+UI+view) ·
`Start_Aura.bat` (headless, lock-checked, logs console) ·
`Stop_Aura.bat` (kills lock PID) · `AURA.vbs` (hidden start).
All SAME NAME in AURA. Risk MED (double-boot if lock mishandled).

## E. Live persistent state at root (class=state, hot=yes, persist=yes, KEEP)

| file | store | risk |
|---|---|---|
| `locked_patterns.txt` (1146 anchors) | canonical vault | HIGH |
| `people.txt` (architect/Matty; hash-pinned) | people | HIGH |
| `identity_core.txt` (31) | identity floor | HIGH |
| `episodic_memory.txt` (500-cap, append-only) | episodes | HIGH |
| `working_memory.txt` (QUERY+RESP turns) | dialogue | HIGH |
| `rapport.txt` (ACQUAINTANCE 56.22) | rapport ledger | HIGH |
| `field_state.txt`, `field_map.json`, `field_stats.txt` | field persist + viewer | HIGH |
| `knowledge_graph.txt`, `extracted_relations.txt`, `inferences.txt`, `contradictions.txt`, `knowledge_gaps.txt` | R-track | HIGH |
| `inner_monologue.txt`, `dream_log.txt`, `emotional_core.txt`, `self_state.txt`, `short_term_memory.txt`, `sensory_buffer.txt`, `internal_stimulus.txt` | voice/memory/sense | MED-HIGH |
| `ebbinghaus_traces.txt`, `sleep_state.txt`, `sleep_log.txt`, `parietal_links.txt`, `parietal_inbox.txt`, `cortex_inbox.txt`, `processed_cortex.txt`, `temporal_links.txt`, `pfc_focus.txt`, `pfc_signal.txt`, `hypothalamus_signal.txt`, `basal_ganglia_log.txt`, `last_architect_input.txt`, `trigram_model.txt`, `vault_compacted_v2.flag` | decay/sleep/attention/signal/model | MED |
| `aura_output.txt` (UI tail) | output | MED |
| `aura_console.log` (14132 lines; regenerable) | console tee | LOW |
| `aura_live_event_sync_stdout[_2].log`, `aura_live_event_sync_stderr[_2].log` | boot/event capture | LOW |
| `aura_instance.lock` (live PID) | single-organism lock | HIGH while running |
| `diagnostics.txt` (turn 1789757628974, viewer-generated) | export product | LOW |

## F. Tests (`tests/`, class=test, KEEP all)

Runner `run_all.py` (sandboxed per-suite temp roots + live gates) ·
`stress_all.py` (61 checks, self-rooting; NEVER repo CWD) ·
`_sandbox_guard.py` (vault tripwire + `guard()`) · `README.md` ·
`gate_analysis.py` · `proof_hebbian.py` ·
`verify_pass05/06/07/08/09` (pipeline hygiene) ·
`verify_2c/2d/2e`, `verify_3a/3b/3c/3full`, `verify_4a/4b/4c/4d`,
`verify_5a/5b/5c/5d` (V2–V5 engine) · `verify_backup` ·
`verify_r1–r7` (relations/graph/inference/QA/gaps/eval) ·
`verify_i1–i4` (voice/tools/ambient/presence) ·
`verify_view` (viewer incl. export partition/probe checks) ·
`verify_safety/races/upkeep/console/diag` (audits) ·
`verify_c1–c11` (companion memory/self/mouth) ·
`verify_f1–f5/f7` (voice track) ·
`verify_g1_leakage`, `verify_g_roleplay`, `verify_g_livevoice`,
`verify_g5_safety`, `verify_g2_packs`, `verify_g4_discord`,
`verify_g6_delight`, `verify_g_growth`, `verify_observatory_contract`,
`verify_g7_context`, `verify_g8_rapport`, `verify_g9_interlocutor`,
`verify_isolation` (G-track + guards; GF-ONLY).

## G. Docs & config (class=doc unless noted)

`GF_PRODUCT_SPEC.md` (product law, GF-only, KEEP/HIGH) ·
`gf_boundaries.md` (safety v1.0, enforced by code, KEEP/HIGH) ·
`AGENTS.md` (onboarding+law+status, diverged from AURA, KEEP/HIGH) ·
`AGENTS_TEMPLATE.md`, `KICKOFF.md` (stale birth expectations),
`SYSTEM_WHITEPAPER.md`, `SYSTEM_AUDIT_REPORT.md`,
`AUDIT_REPORT_COGNITIVE_PATH.md`, `V5_0_AUDIT_REPORT.md`,
`AURA_STRESS_REPORT.md`, `observatory_telemetry.md` (contract, KEEP),
`todo cleanup.txt` (REFERENCE) · `Modelfile.mouth|mouth3b|mouth7b`
(runtime-config; gguf refs dangling in GF — REVIEW) ·
7 binary `.docx` (noted-unread, REFERENCE) · `Aura master v4.zip`
(uninspected contents — LOW conf, REFERENCE) ·
`cognitive_observatory.html` (browser UI, read-only use, KEEP).

## H. Generated trees (summarised; KEEP unless noted)

`backups/` 14 snapshots × ~21 files + `manifest.json` (rotation-managed —
never hand-prune newest) · `__pycache__/` 76 `.pyc` (+tests cache) ·
`users/architect/observer_trace/` 9 live turns (observer+state) ·
`users/test_observer/` 14 files (probe partition — exporter/viewer never
read; KEEP as referenced) · `users/test_user|user1/` 13 files each
(`test_flow*` residue — REVIEW, then ARCHIVE CANDIDATE) ·
`users_probe/u/people.txt` (isolation fixture — KEEP) ·
`characters/` 10 packs × (`pack.json`+`seed.md`) (KEEP) ·
`_legacy/` 2 dead files, zero references (REFERENCE, quarantined) ·
`tmp_roadmap/` unzipped docx XML redundant with `.docx`
(ARCHIVE CANDIDATE) · `pdf_intake|pdf_processed/` empty (KEEP — code
expects them) · 9 `observatory_*.png` (observer evidence, REFERENCE).

## I. Top-10 do-not-move (see MASTER §8)

`locked_patterns.txt` · `people.txt` · `aura_state.py` · `aura_master.py`
· `ukft_brain_api.py` · `aura_constants.py` · `aura_bus.py`
· `identity_core.txt` · `episodic_memory.txt` · `aura_instance.lock`.
