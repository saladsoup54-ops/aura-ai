# REBUILD TODO — Aura recovery

Status: 2026-11-16. Working tree: `_recovery/src/` (canonical). Originals untouched.

## Phase A — rebuild everything (runtime)

- [x] Canonical tree (75 modules, suffixes stripped, one `ukft_relations`)
- [x] Recovered runtime files: `aura_ui.py`, `aura_synapse_view.py`, `tests/m5_harness.py`
- [x] `aura_diagnostic.py` rebuilt as read-only operator tool
- [x] Linux port — PID probes (`aura_master`, `ukft_backup`, `ukft_perpetual`) use `os.kill(pid, 0)`
- [x] Linux port — TTS via `espeak-ng`/`espeak` with silent failure; STT returns silence
- [x] Linux port — motor executes through `/bin/sh` on POSIX
- [x] Linux launchers: `Boot_Aura.sh`, `Launch_Aura.sh`, `Start_Aura.sh`, `Stop_Aura.sh`
- [x] M16 view API: `ROUTE_SYSTEMS`, `evidence_receipts`, `export_real_turns`,
      `format_evidence_table`, `build_diagnostics_text`, `export_diagnostics`
- [x] `memory_block` NameError fixed (hoisted `context_text` from `assemble_context`)
- [x] First sandbox boot — `--- AURA READY ---`, no tracebacks
      (`evidence/first_boot_2026-11-16.log`)
- [ ] GUI deps on host: `sudo apt install python3-tk`, `pip install pygame`
- [ ] View: route-evidence tab rendering (functions exist; no tab yet)
- [ ] Root docs: `README.md`, `seed.md`, `boundaries.md`
- [ ] `characters/` — 10 packs x (`pack.json` + `seed.md`) — deferred by user

## Phase B — rebuild the test suite (91 suites)

Support files already recovered: `tests/run_all.py`, `tests/README.md`,
`tests/_sandbox_guard.py`, `tests/m5_harness.py`,
`tests/verify_cn0_conversation_trace.py`,
`tests/verify_m16_full_route_observability.py`.

Order (the "multimeters" first):

- [ ] `verify_isolation.py` — no README paragraph; reconstruct from `_sandbox_guard`
      + `aura_state` contract + M16's isolation checks
- [ ] `verify_m5_causal.py` — m5_harness consumer (RAN -> OUTPUT PRODUCED ->
      OUTPUT USED -> INFLUENCED DECISION)
- [ ] `verify_m16_full_route_observability.py` — already present; run against src
- [ ] M-series: M1, M2, M3, M4, M13, M14
- [ ] Findings: 01, 02, 04, 06, 08, 09, 10, 11, 12, 14
- [ ] G-series (G1-G9)
- [ ] C-series c1-c11, F-series f1-f5/f7, R-series, I-series
- [ ] pass05-pass09, legacy 2c-5d
- [ ] `stress_all.py` (61 checks), `gate_analysis.py`, `verify_diag`,
      `verify_observatory_contract`, `proof_hebbian`, `verify_view`

Rules for reconstructed suites (AGENTS law):
- header `RECONSTRUCTED 2026-11-16 — NOT the original file`
- no fake green; a check that cannot be proven is a documented SKIP, not a pass
- every suite runs only under `AURA_TEST_MODE=1` + temp `AURA_STATE_ROOT`

## Phase C — docs

- [ ] Refresh `AURA_MASTER_INVENTORY`, `AURA_FILE_INVENTORY`, `AURA_CODEBASE_MAP`,
      `AURA_RULE_AUDIT` against this tree
- [ ] Recover or regenerate the 23 phase/finding reports
- [ ] New SHA-256 manifest for the rebuilt tree
