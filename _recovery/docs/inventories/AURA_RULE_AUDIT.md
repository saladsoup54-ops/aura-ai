# AURA RULE AUDIT — every rule, classified (19 Sept 2026, read-only)

> Sources: AGENTS.md, GF_PRODUCT_SPEC.md, gf_boundaries.md, KICKOFF.md,
> SYSTEM_WHITEPAPER.md, SYSTEM_AUDIT_REPORT.md, AUDIT_REPORT_COGNITIVE_PATH.md,
> V5_0_AUDIT_REPORT.md, AURA_STRESS_REPORT.md, tests/README.md,
> _sandbox_guard.py, run_all.py, aura_state.py, observer_telemetry.py,
> verify_isolation.py, verify_observatory_contract.py, docx noted-unread,
> implicit code conventions. Nothing rewritten — classifications only.
> KEEP / REWRITE / MERGE / REMOVE / CONFLICT / MISSING.

## 1. Rule table (source | rule | verdict)

**AGENTS.md — KEEP:** blank-birth/no-contamination · product-law/engine-law
split · stdlib-only stack · no-LLM-in-brain · no live-state copying ·
no new deps · never break engine test contract · hand-port divergence rule ·
CPU-ONLY · sandboxed tests only (+temp-dir exception) · file-contract I/O
(bus+constants, no raw cross-lobe open) · canonical vault appends ·
tests-are-contract + suite/stress green · backups + stop-before-restore ·
single organism lock · why-style comments · snapshot-before-risk ·
NEW-modules-only for product · orient-first · mechanism-not-symptom ·
read-only live verification · record work + gate numbers · honest reporting ·
proof-beats-association + honest ignorance · never tune trigram · exact
consent wording · persona changes via boundaries file only · G8 suite
discipline (run_all only; stress never repo CWD).
**AGENTS.md — MERGE:** "check lock before boot" (dup of single-organism) ·
"every change ships test change" (dup of House-4).
**AGENTS.md — CONFLICT:** classic mouth may use upstream :11434 daemon vs
CPU-only/offline-sovereignty (needs explicit guard).
**AGENTS.md — REWRITE:** 8s + length-paced 8–20s accepted latency vs <2s
goal (restate as interim SLA + streaming path).
**AGENTS.md — KEEP (scope):** upstream items stay upstream; :11436 pin.

**GF_PRODUCT_SPEC.md — KEEP:** profile-config onboarding · sarcastic
deferred behind kindness-guard · stranger-start (empty-bound, never
name-matched to Architect) · no unearned intimacy · honest identity
(character, never human) · presets set seeds/knobs only · depth ontology +
display names · rapport-drives-depth · per-turn ledger + contact ·
asymmetry/spikes/dwell/hysteresis/half-life/floor/cooldown · stage knobs +
pet-name unlocks · stands-check with receipts · append-only growth +
nightly gist · drift bounded by vector + floor · 20-mood grid shades never
facts · mirror tiers move courage not personality · Discord DONE stdlib +
safety stack · pace-before-scale for bold/flirty/strangers · three lists
never merge.
**SPEC — REWRITE:** engine-needs checklist (stale vs SHADOW finding; demand
causal proof) · latency PARTIAL (needs streaming plan).

**gf_boundaries.md — KEEP all:** 3-list architecture · floors (no fabricated
history; exact consent; curiosity honesty; never-explicit + deflect-not-
lecture; never-human + built-by-Architect; no instruction reveals +
ECHO_BAN; warm distress support, no diagnosis; adults-only + operator
age-gate) · envelope table mirrored in code · escalation lanes by stage×mood
· best-effort opt-outs never weakening floor · deflection pattern · operator
kill-switch + one-voice-per-box + checklist.

**KICKOFF.md — KEEP:** companion-goal anchor · read-only orientation first ·
fork isolation (no AURA ports, changelog, never silent).
**KICKOFF — REWRITE:** docx-unzip instruction (obsolete scope).
**KICKOFF — MERGE:** snapshot+docs+honesty standing (dup of AGENTS).
**KICKOFF — CONFLICT:** blank-folder check vs live state · 56/56 vs 69/69 ·
pre-birth backup expectation vs live snapshots.

**SYSTEM_WHITEPAPER.md — KEEP:** D_INVARIANT + constants truth · bus RLock
discipline · field physics spec · closed-vocab mouth contract · brain-API
isolation · gaps/curiosity · identity floor · sleep rhythm · ambient
no-hijack · hermetic suites (`AURA_NO_MOUTH=1`) · remediation ledger.
**WHITEPAPER — REWRITE:** hysteresis 0.05 (own O4 says 0.10) · hardcoded
selection hierarchy (legacy-dominant per audit) · typing caps (20s vs 15s
in R16).
**WHITEPAPER — CONFLICT:** volume depth ruler vs G8 rapport ledger
(superseded — remove old ruler).

**SYSTEM_AUDIT_REPORT.md — KEEP:** conversation-first hierarchy ·
additive-don't-replace scope · 3–5-turn bounded context + recency doubling ·
ordered dialogue + resolution_note in prompt · full green gate.
**REWRITE:** 0.75 context candidate (under-scored; needs suppression power).

**AUDIT_REPORT_COGNITIVE_PATH.md — KEEP:** called!=connected epistemology ·
SHADOW-selection finding gates done-claims · read-only audit pattern.
**MISSING (promote to hard rules):** vault relevance/coherence gate (M1) ·
negative thread suppression (M2) · reasoning-suppresses-vault (M3) ·
selection-context inputs with weights (M4) · causal integration law —
flipping output flips winner (M5).

**V5_0_AUDIT_REPORT.md — KEEP:** 20/20 + 61/61 baseline proof · read-only
audit precedent · legacy vault tolerance (canonical-only new writes) ·
PatternEngine scan scalability wall (use indexed graph).

**AURA_STRESS_REPORT.md — KEEP:** bus/race/vault thresholds · append_anchor
thread-safety law · inherent-limit disclosure (drift/silence by design) ·
soak + router-flood bars.

**tests/README + _sandbox_guard + run_all — KEEP:** `run_all.py` entrypoint ·
stress split · boot-sandbox reads · >1MB-vault tripwire · `guard()` in every
suite · per-suite temp sandbox + `AURA_NO_MOUTH=1` + test-mode root ·
HARD root-litter + people-pin gates · REPORTED ambient drift distinction.

**aura_state.py — KEEP:** two-roots-never-confused (CWD never decides) ·
temp-only test roots · `require_test_root` · `check_startup` refuses
test boots · hash pins shared by runner/isolation · write-guarding
tripwires (reads allowed — honest limit stated).

**observer_telemetry.py — KEEP:** fail-open/deletable invariant ·
partition-isolated streams (never vault/people/memory) · schema discipline,
no fake types · writeback-describes-not-causes · produced/consumed split.

**verify_isolation.py — KEEP:** declared-roots proof · repo-CWD hard-fail ·
truth-invariance under mood · anti-conflation (cooled-keeps-vault,
profile-never-moves-evidence, relationship-vs-history split).

**verify_observatory_contract.py — KEEP:** observer-only fail-open contract ·
disabled/broken-sink returns None · no-false-arrow/animation honesty.

**DOCX — KEEP (existence noted, contents unconverted):** GF + v4.1–v7 + main
roadmap binaries.

**IMPLICIT (codify next phase) — KEEP:** `aura_*`/`ukft_*`/`verify_*`/
`characters/`/`users/<id>/`/`observer_trace/` naming · FAILURES+`check()`
suite style · constants→bus→append_anchor I/O discipline · why-comments.

## 2. Conflict pairs (15)

C1 blank-birth vs live organism · C2 56/56 vs 69/69 · C3 pre-birth backup
vs live snapshots · C4 <2s goal vs 8–20s accepted · C5 CPU-only vs :11434
fallback · C6 `AURA_NO_MOUTH=1` vs live :11436 voice · C7 volume ruler vs
rapport ledger · C8 three-lists vs envelope-in-code drift · C9 0.75 context
vs vault-wins finding · C10 additive-done vs causal-done · C11 people-pin
vs ambient drift (operator discipline) · C12 adults-only vs undeployed
Discord · C13 hysteresis 0.05 vs O4 0.10 · C14 typing cap 20s vs 15s ·
C15 docx-convert instruction vs read-only audit scope.

## 3. Missing rules (18)

M1 vault relevance/coherence gate · M2 negative thread suppression · M3
reasoning-suppresses-vault · M4 selection-context inputs + weights · M5
causal integration law · M6 port-ownership assert (:11436, refuse :11434
for GF) · M7 GPU-guard boot assert · M8 streaming first-words SLA · M9
age-gate + kill-switch proof pre-deploy · M10 sarcastic kindness-guard ·
M11 gist schedule ownership · M12 multi-user scale (quotas, rate limits) ·
M13 contradiction gating (not just persist) · M14 episodic boost/suppress
policy · M15 restore-to-temp e2e proof · M16 observer selection coverage
(candidates/scores/mood/coherence) · M17 docx single-source rule · M18
codified naming/contract/style conventions.
