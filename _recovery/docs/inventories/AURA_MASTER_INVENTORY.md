# AURA MASTER INVENTORY — Phase 2 read-only census (19 Sept 2026)

> FROZEN BASELINE. This phase changed nothing: no cognition edits, no file
> moves, no deletions, no restructuring, no live-state writes. Evidence was
> gathered by content inspection + reference search only (no code executed).
> The four companion documents hold the detail:
> `AURA_FILE_INVENTORY.md` (every file), `AURA_CODEBASE_MAP.md` (live wiring),
> `AURA_PRE_GF_COMPARISON.md` (fork delta), `AURA_RULE_AUDIT.md` (every rule).

## 1. What this repository is

AURA_GF = product branch of the AURA synthetic-intelligence engine (UKFT
4.3.2, D = 0.0804245, stdlib-only Python 3, no LLM in the brain). Same
physics-engine mind (field, vault, R-track reasoning, honest ignorance,
permissioned tools, offline voice) pointed at one job: a companion that
talks, remembers, and grows. Engine law inherited; product law in
`GF_PRODUCT_SPEC.md` + `gf_boundaries.md`.

## 2. Baseline freeze (what "known-good" means today)

- Viewer recovered 19 Sept from the original 905-line upstream file and
  rebuilt forward in checkpoints; field renderer pixel-untouched.
- Gates observed green on this tree: selftest OK · viewer 39/39 ·
  **69/69** full suites · **61/61** stress · isolation green · live clean.
- Live proof: `diagnostics.txt`, turn 1789757628974, ACTIVE PARTITION
  architect, test/probe strings 0 matches, turn traceable across 6 sections.

## 3. Tree census (summary; per-file detail in AURA_FILE_INVENTORY.md)

| Area | Count | Notes |
|---|---|---|
| Top-level engine/product `.py` | ~70 | ~60 inherited engine lobes + 10 GF-new (`brain_api`, `user_state`, `roleplay`, `pack`, `discord`, `boundaries`, `delight`, `gist`, `growth`, `rapport`) + `aura_state`, `observer_telemetry` |
| One-shot/patch scripts (`add_*`, `fix_*`, `modify_*`, `update_*`, `patch_g7`, `test_flow*`, `merge_code`) | 16 | Spent, zero code references; ARCHIVE CANDIDATES |
| Launchers (`.bat` ×4 + `.vbs`) | 5 | Operator hot path; KEEP |
| Tests (`tests/`: runner, stress, guard, 68 `verify_*`, misc) | 75 entries | The contract; KEEP |
| Character packs (`characters/` 10 dirs) | 20 files | `pack.json` + `seed.md` each; KEEP |
| User partitions (`users/`: architect, test_observer, test_user, user1) | 4 dirs | Only architect is live; test_* are probe/fixture residue |
| Live root state (`.txt`/`.json`/`.log`/lock) | ~40 files | Vault, people (hash-pinned), episodes, rapport, field, R-track, signals, console; all KEEP |
| Backups (`backups/` 14 snapshots) | ~300 files | Retention-managed; do not hand-prune |
| Docs (`.md` + 7 binary `.docx` + zip) | ~20 | `.md` readable; `.docx` noted-unread (no conversion attempted) |
| Generated (`__pycache__`, `diagnostics.txt`, `observatory_*.png` ×9, logs) | — | Reference; regenerable |
| Reference/quarantine (`_legacy/` 2 files, `tmp_roadmap/`, `users_probe/`, `pdf_intake|processed/`, `KICKOFF.md`) | — | Do not wire into code |

## 4. Live hot path (one line)

`aura_master.py` boot → terminal/Discord/API input → `SovereignEgo`
(`aura_bridge.py`) detectors → `ukft_basal_ganglia` competition → winner
branch → grounding (`ukft_mouth` / `ukft_roleplay` :11436) → response →
writeback (working memory, episodes, rapport, gaps, identity, field,
observer trace). GF partitions serialize through `ukft_brain_api.ask`
with root stash/restore + field clear under one lock.

## 5. State map (persistent, precious)

Vault (`locked_patterns.txt`), people (hash-pinned), identity floor,
episodes (append-only), working memory (QUERY+RESP), rapport ledger,
field (`field_state/map/stats`), R-track (graph/inferences/contradictions/
gaps), signals (hypo/PFC/basal), sleep/dream/decay traces, console log,
instance lock, 14 snapshots. Full table in FILE_INVENTORY §E.

## 6. Partition map

- Live home = repo root (`architect`); `users/architect/` holds ONLY
  `observer_trace/` (9 turns).
- `users/<id>/` partitions (G1) isolate dialogue/profile state per ask;
  engine-global files (trigram, temporal links, field, buses, basal log)
  stay process-global BY DESIGN (partial isolation, documented).
- `users/test_observer|test_user|user1` = probe/fixture residue; the
  exporter and viewer never read test partitions.

## 7. Observer map (observer-only, never causal)

`observer_telemetry.py` emits 8 turn-boundary event types to
`observer_trace/`; viewer CHAT/ALERTS/PROGRESS + SHADOW/USED wiring +
`diagnostics.txt` consume them. Deleting the observer changes nothing
about her. Several schema event types are defined but never emitted
(see CODEBASE_MAP §4).

## 8. Risk register (do-not-move list)

`locked_patterns.txt` · `people.txt` (hash-pinned) · `aura_state.py` ·
`aura_master.py` · `ukft_brain_api.py` · `aura_constants.py` ·
`aura_bus.py` · `identity_core.txt` · `episodic_memory.txt` ·
`aura_instance.lock` (while running). Reasons in FILE_INVENTORY §H.

## 9. Key audit findings (for the deciders)

1. No engine `.py` was deleted at the fork — loss is artifacts/blobs/notes.
2. New-but-never-causal systems exist: nightly gist (no scheduler), trigram
   speak path (never selected), discovery→`discoveries.txt` (no reader),
   hippocampus/parietal/DMN loops (tails only), Discord live (no token).
3. The turn path is split in two (master+Roleplay vs BrainModule partition
   path) with duplicated depth/mirror logic.
4. Load-bearing critique on record: newer selection infra is largely
   SHADOW — vault token-overlap + hardcoded scores still decide
   (`AUDIT_REPORT_COGNITIVE_PATH.md`); six integration rules are MISSING.
5. 15 rule conflicts + 18 missing rules catalogued (RULE_AUDIT §2–3),
   stalest: KICKOFF birth-state expectations vs live organism; old volume
   depth ruler vs rapport ledger; latency SLA vs CPU reality.

## 10. Decision questions for next phase (no action taken)

- Archive the 16 spent one-shot scripts (+`tmp_roadmap/`) after a snapshot?
- Remove `users/test_user|user1` probe residue after confirming no suite reads them?
- Promote the 6 MISSING selection-wiring rules (M1–M5 + M13/M14/M16) to hard gates?
- Resolve latency SLA (streaming first-words) vs accepted 8–20s stagger?
- Single-source the roadmaps (docx vs hand-edit logs)?
- Prove Discord age-gate + kill-switch before any live deploy?

STOP. Awaiting Architect + reviewer direction. Nothing was moved, deleted,
rewritten, or executed in this phase.
