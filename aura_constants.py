# aura_constants.py — AURA single source of truth (Phase 0.7)
# ============================================================
# Governed by Unified Kymattik Field Theory 4.3.2

D_INVARIANT = 0.0804245

# ── Phase thresholds ──────────────────────────────────────────────
PHASE_MIDPOINT           = 0.50   # FLUID/FROZEN Woods-Saxon threshold
TENSION_TARGET           = 0.50   # hypothalamus homeostatic target
TENSION_TOLERANCE        = 0.20   # hypothalamus band (+/-); 0.15 was too tight —
                                  # an actively-learning field idles at 0.55-0.65
                                  # and was being permanently INHIBITed
CORTEX_TENSION_TOLERANCE = 0.25   # cortex STABLE band around the midpoint

# ── Field breathing room (saturation fix, 14 Sept 2026) ─────────────
# The field had no activation decay: step() only ever added non-negative
# velocity, so any stimulated node ratcheted to 1.0 and stayed there.
# Forgetting (1h silence below 0.05) could then never drain a live field,
# the dream lobe paused forever at 5000 nodes, and the monologue looped
# on the pinned hub.  Three constants govern the fix:
FIELD_NODE_CEILING    = 5000   # dream pauses stimulation above this
FIELD_TRIM_FRACTION   = 0.90   # pressure valve drains to 90% of ceiling
FIELD_ACTIVATION_LEAK = 0.9999 # per-step (10 Hz) activation decay —
                               # silent hubs halve in ~12 min, so the
                               # 1h forgetting clock can actually fire

# ── Phase 2-E: reticular formation (source salience) ──────────────
# The Architect's voice must dominate background intake.  Every sensory
# record is stimulated with a source-scaled gain; when the Architect has
# spoken recently, background sources are attenuated by the extra
# foreground factor until the window expires.
RETICULAR_ARCHITECT_GAIN         = 1.0
RETICULAR_FEEDBACK_GAIN          = 0.6
RETICULAR_PDF_GAIN               = 0.35
RETICULAR_BACKGROUND_GAIN        = 0.25   # Wikipedia / web ambient intake
RETICULAR_FOREGROUND_ATTENUATION = 0.2    # background multiplier while Architect foreground
RETICULAR_FOREGROUND_WINDOW      = 60.0   # seconds the Architect holds the foreground

# ── Shared file contracts ─────────────────────────────────────────
UI_INPUT_FILE    = "ui_input.txt"
THOUGHTS_FILE    = "aura_thoughts.txt"
OUTPUT_FILE      = "aura_output.txt"   # single spoken slot: all publishers
                               # write atomically through the bus (no torn
                               # reads), last writer wins by design.  A
                               # multi-message queue (append-log + offset
                               # tailing) is scoped for V6 C11 — collisions
                               # need two publishes inside one ~1 s voice
                               # poll and are rare in practice.
THINKING_LOCK    = "aura_is_thinking.lock"

VAULT_FILE        = "locked_patterns.txt"
SENSORY_BUFFER    = "sensory_buffer.txt"
CORTEX_INBOX      = "cortex_inbox.txt"
CORTEX_PATH       = "processed_cortex.txt"
SHORT_TERM_MEMORY    = "short_term_memory.txt"
ROLEPLAY_DEBUG_FILE = "roleplay_debug_once.json"
PARIETAL_INBOX    = "parietal_inbox.txt"
PARIETAL_LINKS    = "parietal_links.txt"
TEMPORAL_LINKS    = "temporal_links.txt"
BASAL_GANGLIA_LOG = "basal_ganglia_log.txt"
TRIGRAM_MODEL     = "trigram_model.txt"
WORKING_MEMORY    = "working_memory.txt"
DISCOVERIES       = "discoveries.txt"
IDENTITY_CORE_FILE = "identity_core.txt"
SLEEP_STATE_FILE  = "sleep_state.txt"
SLEEP_LOG_FILE    = "sleep_log.txt"
EPISODIC_MEMORY   = "episodic_memory.txt"
BACKUP_DIR        = "backups"
EBBINGHAUS_TRACES = "ebbinghaus_traces.txt"
FORGOTTEN_MEMORIES = "forgotten_memories.txt"
EMOTIONAL_LOG     = "emotional_core.txt"
MONOLOGUE_FILE    = "inner_monologue.txt"
FIELD_STATE       = "field_state.txt"
FIELD_STATS       = "field_stats.txt"
FIELD_MAP         = "field_map.json"
HYPO_SIGNAL_FILE  = "hypothalamus_signal.txt"
PFC_SIGNAL_FILE   = "pfc_signal.txt"
PFC_FOCUS_FILE    = "pfc_focus.txt"
LAST_INPUT_FILE   = "last_architect_input.txt"
INTERNAL_BUFFER   = "internal_stimulus.txt"
DREAM_LOG         = "dream_log.txt"
EXTRACTED_RELATIONS = "extracted_relations.txt"   # V5 R1: typed facts mined from the vault
KNOWLEDGE_GRAPH     = "knowledge_graph.txt"       # V5 R2: assertional node/edge store
INFERENCES          = "inferences.txt"            # V5 R3: derived conclusions with proof trails
CONTRADICTIONS      = "contradictions.txt"        # V5 R3: conflicting assertions flagged
KNOWLEDGE_GAPS      = "knowledge_gaps.txt"        # V5 R6: honest-ignorance gaps, deduplicated with counts
EVALUATION_REPORT   = "evaluation_report.txt"     # V5 R7: gate measurements (R-A..R-D)
RELATION_AUDIT      = "relation_audit_sample.txt" # V5 R7: numbered relation sample for Architect judgement
ACTION_LOG          = "action_log.txt"            # V5 I2: every tool action, logged
PENDING_ACTION      = "pending_action.txt"        # V5 I2: a confirm-required action awaiting the Architect
PEOPLE_FILE         = "people.txt"                # V6 C2: self-updating social memory (one record per person)
PENDING_PEOPLE      = "pending_people.txt"        # V6 C2: an uncertain introduction awaiting confirm/cancel
SELF_FILE           = "self_state.txt"            # V6 C7: drive weights + self-model state
THREADS_FILE        = "threads.txt"               # V6 C6: persistent open threads (agenda)
BELIEFS_FILE        = "beliefs.txt"               # V6 C10: architect-held claims with provenance
PENDING_BELIEF      = "pending_belief.txt"        # V6 C10: a contested claim awaiting confirm/cancel
LESSONS_FILE        = "lessons.txt"               # V6 C8: banked lessons with teacher + topic
REGISTER_STATE      = "register_state.txt"        # V7 F1: last-20 opener ids (voice variety memory)

# ── V6 C9: the Mouth (optional swappable realizer) ──────────
# A local Ollama-served model from the Architect's GGUF file.
# Unplug with MOUTH_ENABLED=False (or stop the daemon): every
# proof answer then falls back to the deterministic template.
MOUTH_MODEL   = "aura-mouth-3b"         # ollama model (Modelfile.mouth3b:
                                          # Qwen2.5-3B-Instruct Q4_K_M, local GGUF)

# ── V7 F7: the spoken voice ───────────────────────────────
# SAPI voice by EXACT installed name ("Microsoft Zira Desktop" —
# the WinRT short name does NOT match and falls back silently;
# measured 16 Sept 2026).  "Zira" because she is her — flip this
# one constant for David, then reboot (defaults bind at import).
AURA_VOICE = "Microsoft Zira Desktop"
MOUTH_URL     = "http://localhost:11434"
MOUTH_TIMEOUT = 25.0                # seconds before the template wins
MOUTH_ENABLED = True
CONSOLE_LOG         = "aura_console.log"          # console mirror: every lobe print, tailed to disk
