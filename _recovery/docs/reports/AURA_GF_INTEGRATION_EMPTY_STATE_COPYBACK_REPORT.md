# AUDIT FINDING #1 — EMPTY-STATE COPYBACK INTEGRITY REPORT

Date: 21 Sept 2026
Status: AUDIT FINDING #1 EMPTY-STATE COPYBACK — READY FOR REVIEW
Scope: partition sync-back only. No candidate, salience, selector, memory
policy, contradiction, episodic, mouth, boundary, or product change. Finding
#2, transactional writeback, `memory_writes` journaling, and all other audit
findings are untouched.

## Exact Bug Reproduced

`BrainModule._sync_user_files_to_root(user_id, "from_root")`
(`ukft_brain_api.py`) copied a root state file back to the user partition
only when the root file existed **and** its size was greater than zero.

A legitimate non-empty → empty transition during the swapped turn was
therefore lost. Proven pre-fix record (focused suite, 3 failures):

- staged `pending_people.txt` (`NAME: John | ...`) + real `ask("cancel")`
  → response correct (`people` / "Dropped — I will not remember that.")
  but the partition kept the stale staged line;
- a fresh `BrainModule` later turn resurrected the stale pending state;
- staged pending + real `ask("confirm")` committed the person (non-empty
  path worked) but left the pending slot stale.

Root cause chain: `to_root` copies the partition file to root (empty or
not); the swapped-turn writer (`PeopleModel.clear_pending()` /
`BeliefStore.clear_pending()` / `ToolDirector.confirm|.""cancel` via
`aura_bus.write(path, "")`) clears the **root** copy to zero bytes;
`from_root` then skipped it and the stale partition copy survived.

## Exact State Contract After The Fix

`ukft_brain_api.py: EMPTY_COPYBACK_FILES` (`pending_people.txt`,
`pending_belief.txt`, `pending_action.txt` — the only partitioned files
with legitimate whole-file-clear writers) plus a reworked `from_root`:

- root file **missing** → partition untouched, for every name;
- `field_state.txt` → legacy rule (copy only if non-empty); Pass 1A's
  `_settle_user_field` still owns its empty manifold (deletes root +
  partition before this sync in both `ask()` and `roleplay()`);
- allowlisted name with **existing** root file (even zero bytes) → copy
  back, so an intentional clear survives;
- every other name → copy back only if non-empty (unchanged), so a corrupt
  or accidental empty root can never wipe vault, people, beliefs, threads,
  lessons, or other partition state.

`to_root`, `_stash_root`, `_restore_root`, selection, saliences, mouth,
and write accounting are untouched. The sync runs strictly after
`manifest_thought` returns, so current-turn cognition is unaffected by
construction; only the next turn reads the corrected partition.

## Files Changed

- Runtime: `ukft_brain_api.py` (allowlist + `from_root` contract only).
- Tests: `tests/verify_finding01_empty_copyback.py` (new, shipping),
  `tests/run_all.py` (registration before isolation), `tests/README.md`.
- Docs: `AGENTS.md`, `SYSTEM_WHITEPAPER.md`,
  `AURA_CURRENT_CAPABILITIES.md`, `AURA_WANTED_FEATURES.md`,
  `AURA_GF_INTEGRATION_EMPTY_STATE_COPYBACK_REPORT.md`,
  `AURA_CHANGELOG.md`.
- Unchanged: original audit, M16 report, governance/boundaries, all other
  runtime/tests, live state.

## Real-Route Proof

`tests/verify_finding01_empty_copyback.py` drives production
`BrainModule.ask()` (full root swap) throughout:

- ARM 1: staged people pending + "cancel" → `people` winner, "Dropped",
  partition pending empty.
- ARM 2: fresh `BrainModule` + later turn → pending stays empty.
- ARM 3: staged pending + "confirm" → `people` winner, "Confirmed",
  pending empty **and** the committed person record present (non-empty
  copyback intact).
- ARM 6/7: the same clear proven for `pending_belief.txt` ("Kept",
  `belief` winner) and `pending_action.txt` ("Aborted", `tools` winner) —
  every allowlist member, not just people.
- ARM 8: real selector receipt (`explain=True`) keeps `people` at exactly
  0.99 salience; candidate-table source scan pins the bid.

## Negative / Data-Loss Controls

- ARM 4 (helper-level, disclosed): missing root pending file at sync-back
  leaves valid partition state alone — missing is never delete permission.
- Non-allowlisted files keep the `size > 0` gate: an empty root vault,
  people, belief, or thread file cannot propagate.
- Reviewer 1 verified the allowlist is exact (no other partitioned file
  has a whole-clear writer) and missing-never-deletes holds for every name.

## Cross-User Proof

- ARM 5: a second user's staged pending is byte-identical after other
  users' cancel/confirm/hello turns (stash/swap/restore under `_ask_lock`).
- Suite pins temp-root containment and live-state hashes.

## Pass 1A Preservation

- `field_state.txt` excluded from the allowlist with its legacy rule
  intact; settle → sync → restore ordering identical in `ask()` and
  `roleplay()`; empty manifold still deletes root + partition via settle,
  non-empty still copies back. `verify_brain_gf_pass1a.py` green in the
  full run (81/81).

## Verification Results

- Pre-work snapshot: `backups/aura_20260921_104018` (verified 20/20).
- Focused suite pre-fix: 3 failures (the bug record above).
- Focused suite post-fix: ALL PASSED.
- Full shipping regression: 81/81 green; embedded isolation green; live
  state clean (no litter, people.txt pinned).
- Safe stress workflow: 61/61 green, 1 existing note.
- Viewer checks: ALL PASSED in pristine sandbox (a parallel manual run in
  one shared scratch dir showed 3 export failures from leftover state;
  re-run isolated: rc=0); selftest 40 frames + 17 tabs.
- No restore required.

## Independent Review Findings And Resolutions

- Reviewer A (empty-vs-missing, isolation, resurrection): CHALLENGE PASS,
  no blocking issues. Residual notes recorded as future hardening, not
  finding-#1 scope: torn non-empty writes are not integrity-checked
  (pre-existing), `pfc_focus.txt`/`aura_thoughts.txt` are shared-root
  channels outside the partition swap (pre-existing), controls are
  narrow by design.
- Reviewer B (regression safety, Pass 1A, test validity): CHALLENGE FAIL
  with two blocking issues — (1) vacuous `True` salience check, (2) 3-slot
  allowlist with 1-slot proof. Both resolved: ARM-8 real receipt (0.99
  within 1e-9) + source pin; ARM-6/7 real-route belief/tool arms.
  Re-confirmation: RESOLUTIONS ACCEPTED, no new flaws.

## Remaining Audit Findings

Still open per the original audit: ego/vault partition ordering (#2),
non-transactional writeback (#4), shadow context fields (#6),
lessons-as-correction (#8), belief-trust/people-importance readers (#9),
`memory_writes` journaling (#10), distributed personality/boundary
authority (#11), amygdala influence (#12), pack knob decisions (#14), and
bounded portions of #6/#11/#15. GF EXPERIENCE <-> OLD BRAIN INTEGRATION
remains IN PROGRESS. Finding #2 was not started.

## Result

AUDIT FINDING #1 EMPTY-STATE COPYBACK — READY FOR REVIEW.
