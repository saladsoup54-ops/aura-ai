# AURA recovery audit — 15 Nov 2026

**Subject:** the 76 `.py` files recovered from the ChatGPT attachment dump (`/home/matty/Desktop/Aura AI`).
**Method:** every file parsed to AST, every import resolved, every imported symbol checked, every `module.attr`
and every call signature compared against the defining file, every name resolved with `symtable` scoping,
plus an isolated import test of all 75 canonical modules.
**Verdict:** one coherent snapshot. One real defect. Zero truncation, zero symbol drift, zero encoding damage.

---

## 1. Results

| Check | Result |
|---|---|
| Files parsed | **76 / 76** |
| Lines of Python | **27,152** |
| Syntax errors | 0 |
| Unresolved internal imports | 0 |
| Missing imported symbols | 0 |
| Nonexistent attributes on imported modules | 0 |
| Arity / unknown-kwarg mismatches (cross-module) | 0 |
| Arity / kwarg mismatches (same module) | 0 |
| Undefined global names (`symtable`) | **1** — `memory_block` |
| Duplicate definitions inside a module | 0 |
| U+FFFD replacement chars / NUL bytes | 0 / 0 |
| Byte-identical duplicate files | 1 pair (`ukft_relations(1)` = `(4)`) |
| Import cycles | 1 (benign, both edges lazy) |
| Modules reachable from `aura_master` | 67 / 76 |
| Isolated import test | **75 / 75 OK** |

The import test ran each module in its own process with `AURA_TEST_MODE=1` and
`AURA_STATE_ROOT=/tmp/...`, so no state was written to the project. Every module loads.

---

## 2. The one defect

`aura_master.py:294`, inside `process_message` (defined at line 165):

```python
try:
    from ukft_roleplay import maybe_debug_dump
    maybe_debug_dump(
        prompt, [
            {"label": "current_user_facts",
             "sources": ["people.txt"],
             "text": str(memory_block)[:300]},   # NameError: memory_block never assigned
            ...
```

`memory_block` appears exactly once in the file — it is never assigned. The surrounding
`except Exception:` swallows the `NameError`, so `maybe_debug_dump(...)` **never executes on the
master route**. Debug/review dumps are silently missing; cognition is unaffected.

**Fix:** pass a variable that is in scope (`_dlg`, or the `assemble_context(...)` result), or drop
that dict entry. One line.

---

## 3. Structural notes (not defects)

- **Third-party packages:** `requests`, `bs4`, `pypdf`.
  `requests` is imported at module top in `ukft_synapse.py` (and `aura_master` imports `ukft_synapse`)
  → it is a hard boot dependency. `bs4` and `pypdf` are guarded with try/except and degrade gracefully.
- **Duplicate module:** `ukft_relations(1).py` and `ukft_relations(4).py` are byte-identical
  (`sha256 d2768629…5dea461`). The canonical tree keeps one.
- **Import cycle:** `ukft_delight ↔ ukft_roleplay`, both function-local (`ukft_delight.py:67`,
  `ukft_roleplay.py:529`). No import-time cycle.
- **Modules not reachable from `aura_master`:** `ukft_brain_api`, `ukft_discord`, `ukft_pack`,
  `ukft_user_state`, `ukft_eval`, `ukft_gist`, `ukft_perpetual`, `ukft_directed_synapse`.
  By design: the BrainModule/engine path is driven by discord and the test suite; `aura_master`
  calls `ukft_roleplay` directly.
- **Constants drift risk:** `aura_master.py` re-declares `UI_INPUT_FILE`, `THOUGHTS_FILE`,
  `OUTPUT_FILE`, `THINKING_LOCK` with identical values instead of importing `aura_constants`.
  188 file-path literals bypass `aura_constants` across the tree (51 of them in `ukft_user_state`,
  which builds per-user paths dynamically). Values agree today; renames would not propagate.
  `observer_telemetry.py:191` hardcodes `0.75` instead of importing `M4_WEAK_CONTEXT`.
- **Unreferenced public functions (15):** all test/CLI hooks (`require_test_root`,
  `live_state_hashes`, `replay_vault_memories`, `listen_once`, `pack_path`, `under`, `locked`,
  `drain`, `format_trace`, `generate_physics_report`, `pick_voice`, `rapport_audit`,
  `score_signals`, `set_user_state_manager`, `run_tools_demo`). Expected while the suite is missing.
- **Cosmetic:** CRLF line endings in `aura_master`, `aura_vault_io`, `ukft_brain_api`, `ukft_eval`,
  `ukft_trigram`; `ukft_user_state` lacks a final newline.

---

## 4. File-contract graph

25 distinct state-file contracts. Six are written but never read:

| file | reader |
|---|---|
| `aura_output.txt` | `aura_ui.py` — **missing** |
| `aura_console.log` | human |
| `aura_thoughts.txt`, `forgotten_memories.txt`, `parietal_links.txt`, `pfc_signal.txt` | tests / observer tools |

Two are read but never written: `people.txt` (seeded at birth by `ukft_people`) and
`sleep_state.txt`. Every contract is accounted for; nothing is orphaned.

---

## 5. What is still missing

| Category | Count |
|---|---|
| Runtime code | 1 — `aura_diagnostic.py` |
| Test suite files | 89 (specs survive in `tests/run_all.py`, `tests/README.md`, 226 captured assertions) |
| Docs | ~25 (23 phase/finding reports, `AURA_PRE_GF_COMPARISON.md`, root `README.md`) |
| Launchers | 5 (`.bat`/`.vbs` → need `.sh`) |
| Live state | regenerated on first boot (per the KEEP law) |

`aura_synapse_view.py` as recovered predates M16: it has no `ROUTE_SYSTEMS`, no receipt rendering and
no `export_diagnostics()`/`diagnostics.txt`. ~100–150 lines must be re-added to satisfy
`verify_m16_full_route_observability.py`.

---

## 6. Canonical source tree

`_recovery/src/` holds 75 files with suffixes stripped (`(1)`, `(2)`, `(20260924-…)`), one copy per
module. This is the first runnable tree; the original dump has **not** been modified or renamed.
`_recovery/CHECKSUMS.sha256` fingerprints all 93 original files.

Verification commands:

```bash
# static: imports + symbols + syntax
python3 - <<'PY'
# see _recovery/README.md for the full script
PY

# runtime: isolated imports (no project state touched)
AURA_TEST_MODE=1 AURA_STATE_ROOT=$(mktemp -d) PYTHONPATH=_recovery/src \
  python3 -c "import aura_master"
```

---

## Appendix — canonical tree (75 modules)

| module | lines | bytes | top-level defs |
|---|---:|---:|---:|
| `aura_bridge.py` | 4882 | 224,868 | 42 |
| `aura_bus.py` | 95 | 2,858 | 6 |
| `aura_constants.py` | 116 | 7,160 | 0 |
| `aura_cortex.py` | 128 | 4,334 | 4 |
| `aura_field.py` | 251 | 11,101 | 2 |
| `aura_master.py` | 552 | 22,972 | 8 |
| `aura_motor.py` | 227 | 8,455 | 5 |
| `aura_state.py` | 171 | 6,162 | 11 |
| `aura_vault_io.py` | 289 | 10,804 | 9 |
| `aura_vocal_manifest.py` | 83 | 3,178 | 2 |
| `observer_telemetry.py` | 479 | 22,331 | 8 |
| `ukft_affect.py` | 102 | 3,699 | 2 |
| `ukft_agenda.py` | 205 | 7,292 | 5 |
| `ukft_ambient.py` | 133 | 4,821 | 6 |
| `ukft_amygdala.py` | 124 | 4,106 | 4 |
| `ukft_answer.py` | 363 | 14,690 | 5 |
| `ukft_backup.py` | 381 | 14,475 | 6 |
| `ukft_basal_ganglia.py` | 129 | 5,854 | 1 |
| `ukft_belief.py` | 423 | 16,239 | 9 |
| `ukft_boundaries.py` | 178 | 7,371 | 6 |
| `ukft_brain_api.py` | 1499 | 65,828 | 5 |
| `ukft_cerebellum.py` | 67 | 2,498 | 1 |
| `ukft_console_log.py` | 88 | 3,002 | 2 |
| `ukft_context.py` | 118 | 4,336 | 3 |
| `ukft_delight.py` | 100 | 3,768 | 5 |
| `ukft_directed_synapse.py` | 40 | 1,211 | 1 |
| `ukft_discord.py` | 538 | 19,286 | 18 |
| `ukft_discovery.py` | 243 | 9,679 | 3 |
| `ukft_dmn.py` | 92 | 3,451 | 2 |
| `ukft_dream_state.py` | 239 | 9,600 | 8 |
| `ukft_ebbinghaus.py` | 243 | 10,780 | 4 |
| `ukft_entropy.py` | 60 | 2,044 | 2 |
| `ukft_episodic.py` | 178 | 7,583 | 1 |
| `ukft_eval.py` | 385 | 16,371 | 9 |
| `ukft_gaps.py` | 208 | 9,122 | 2 |
| `ukft_gist.py` | 101 | 3,390 | 4 |
| `ukft_grammar.py` | 94 | 3,352 | 1 |
| `ukft_growth.py` | 169 | 5,396 | 7 |
| `ukft_hippocampus.py` | 209 | 8,884 | 6 |
| `ukft_hypothalamus.py` | 83 | 2,817 | 3 |
| `ukft_identity.py` | 202 | 8,677 | 2 |
| `ukft_inference.py` | 535 | 23,418 | 7 |
| `ukft_inner_monologue.py` | 615 | 27,370 | 10 |
| `ukft_knowledge_graph.py` | 217 | 9,486 | 2 |
| `ukft_memory_vault.py` | 48 | 1,727 | 1 |
| `ukft_mouth.py` | 272 | 10,641 | 7 |
| `ukft_pack.py` | 94 | 3,411 | 4 |
| `ukft_parietal_lobe.py` | 185 | 6,515 | 7 |
| `ukft_pdf_intake.py` | 272 | 8,913 | 8 |
| `ukft_people.py` | 755 | 32,162 | 14 |
| `ukft_perpetual.py` | 365 | 14,760 | 10 |
| `ukft_pfc.py` | 226 | 7,352 | 7 |
| `ukft_policy.py` | 100 | 3,415 | 5 |
| `ukft_presence.py` | 134 | 4,915 | 4 |
| `ukft_question.py` | 537 | 23,108 | 2 |
| `ukft_quote.py` | 185 | 7,266 | 8 |
| `ukft_rapport.py` | 599 | 23,308 | 10 |
| `ukft_recall.py` | 265 | 10,322 | 8 |
| `ukft_register.py` | 218 | 7,938 | 2 |
| `ukft_relations.py` | 1264 | 57,046 | 13 |
| `ukft_reticular.py` | 113 | 4,171 | 2 |
| `ukft_roleplay.py` | 1067 | 45,669 | 35 |
| `ukft_self.py` | 254 | 9,182 | 7 |
| `ukft_sleep.py` | 195 | 7,646 | 3 |
| `ukft_spontaneous.py` | 192 | 7,973 | 2 |
| `ukft_synapse.py` | 185 | 6,549 | 5 |
| `ukft_teach.py` | 197 | 6,722 | 6 |
| `ukft_temporal_lobe.py` | 349 | 15,151 | 2 |
| `ukft_thalamus.py` | 144 | 5,448 | 5 |
| `ukft_time.py` | 159 | 5,933 | 5 |
| `ukft_tools.py` | 238 | 10,434 | 4 |
| `ukft_trigram.py` | 475 | 19,375 | 5 |
| `ukft_user_state.py` | 407 | 17,013 | 3 |
| `ukft_voice.py` | 209 | 7,189 | 9 |
| `ukft_working_memory.py` | 551 | 23,763 | 3 |
| **total** | **25,888** | **1,079,136** | |
