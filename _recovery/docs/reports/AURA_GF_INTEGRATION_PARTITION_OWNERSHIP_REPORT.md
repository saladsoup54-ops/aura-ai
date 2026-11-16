# AUDIT FINDING #2 — PARTITION OWNERSHIP REPORT

Date: 21 Sept 2026
Status: AUDIT FINDING #2 PARTITION OWNERSHIP — READY FOR REVIEW
Scope: ego-creation ordering on the Brain API turn path only. No candidate,
salience, selector, M-gate, memory-policy, mouth, boundary, or product
change. Findings #1, #4, and all later seams untouched.

## Exact Audited Risk

`BrainModule.ask()` / `roleplay()` called `_get_ego(user_id)` BEFORE the
partition `to_root` swap. `SovereignEgo.__init__` eagerly constructs
`PatternEngine`, which eagerly `_load_vault()`s the CURRENT root vault;
later reloads are mtime-gated
(`current_mtime <= last_mtime and anchors: return`). Under adverse mtime
ordering, cached anchors from the wrong pre-swap root survive instead of
the requested user's vault becoming authoritative. The audit classified
this as a static conditional risk, not a reproduced failure.

## Whether It Reproduced Pre-Fix

YES — decisively, through the real `BrainModule.ask()`/`roleplay()` path
in pristine sandboxes (hostile root sentinel `frostglass` vs user
`sunquartz`/`moonopal`, explicit `os.utime` mtime control):

- adverse NEWER root, EQUAL mtime: User A turn quoted `frostglass`;
- old-seed user: quoted `frostglass`, ego anchors held the sentinel;
- cached A/B/A alternation: ALL THREE turns quoted `frostglass`;
- mechanism dump: `engine.anchors == [(Skycrystal, frostglass...)]`,
  `last_mtime` == pre-swap root mtime, `last_m1` passed the sentinel.

Pre-fix record: 8 failures with the wrong-content-wins signature.

## Exact Root Cause

Two compounding facts, both verified in current code (not comments):

1. `_get_ego` ran before `to_root` in both routes, so a fresh ego's
   `PatternEngine` ingested the pre-swap root vault at construction.
2. The mtime gate then preserved it: the user's older/equal-mtime vault
   never triggered a reload, persistently (every later cached turn too).

The `_create_ego_for_user` comment claiming "Ego components lazy-load"
was false for `PatternEngine` (eager) and `WorkingMemory` (eager load).

## Exact Ownership Invariant After The Fix

LOCK → preserve root (stash) → activate requested partition (to_root) →
establish/refresh ego state (_get_ego, G7 reload, field restore) → run
cognition → sync home (settle, from_root) → restore root — in BOTH
`ask()` and `roleplay()`. A swap/ego-birth failure before cognition
restores the pre-turn root and propagates (finding-#2 guard now also
covers `to_root` itself). No ego is ever born seeing a foreign root.

## Production Files Changed

- `ukft_brain_api.py` only: `_get_ego` moved after `to_root` in `ask()`
  and `roleplay()`; restore-on-early-failure guards; `_create_ego_for_user`
  docstring corrected (eager vault load stated, to_root-before-_get_ego
  contract stated). No selection, salience, M-gate, mouth, or policy line
  touched.

## Adversarial Mtime Proof

- NEWER hostile root, EQUAL mtime, OLDER hostile root (normal control):
  user vault wins every turn; sentinel never quoted.
- Old-seed user: no sentinel quote; ego anchors hold seed content only.
- `shutil.copy2` preserves ns mtimes through the swap; 100–400 ms test
  offsets sit far above filesystem granularity.

## Fresh / Cached Ego Proof

- Fresh module per arm: first turns own the partition vault.
- Cached A → B → A alternation under a hostile newer root: A/A/B/B/A/B
  content discipline with zero leakage (response quotes + winners).

## A/B/A Isolation Proof

Covered above; second-user state untouched; per-user ego cache
(`_egos[user_id]`) can only ever hold its own user's anchors because
every birth happens post-swap and rank reloads run only during the
owning user's swapped turns.

## ask / roleplay Parity

Both routes share the identical lock body shape; roleplay proven via the
mouth-down template-fallback path (response byte-identical to the engine
template); source-order invariant (`to_root` precedes `_get_ego`)
asserted in-suite for both function bodies.

## Root Restoration Proof

Pre-swap root vault byte-identical after the turn; user vault absent from
root post-turn; partition writes sync home normally. Early-failure guard
traced line-by-line by Reviewer B for both routes.

## Preservation Of Finding #1, G7, Pass 1A

- Finding #1: `verify_finding01_empty_copyback.py` green; `from_root`
  untouched.
- G7: explicit `ego.memory.load()` post-swap kept in both routes;
  `verify_g7_context.py` green.
- Pass 1A: restore/settle ordering untouched; `field_state.txt` handling
  identical; `verify_brain_gf_pass1a.py` green.
- Selection/saliences/M-gates/mouth: byte-identical code paths; M5/M1–M4/
  M13/M14/M16 suites green; real 0.99 people receipt re-proven inside the
  finding-#1 suite run.

## Focused / Full / Stress / Isolation Results

- Pre-work snapshot: `backups/aura_20260921_104018` (verified 20/20).
- Focused pre-fix (hardened setup, pristine): 8 failures, frostglass
  signature (record above).
- Focused post-fix (pristine): ALL PASSED.
- Full `python tests/run_all.py`: 82/82 green; embedded isolation green;
  live state clean (no litter, people.txt pinned).
- Safe stress: 61/61 green, 1 existing note.
- Viewer checks green (pristine); selftest 40 frames + 17 tabs.
- No restore required.

## Independent Reviewer Findings And Resolutions

- Reviewer A (ownership/cache adversary): CHALLENGE PASS, no blockers.
  Residuals logged as future hardening, NOT this pass: cached-ego
  equal-mtime content swaps and deleted-vault staleness (same-user
  shapes; the mtime gate survives for those), per-ARM anchor asserts,
  optional content/size-checked reload.
- Reviewer B (lifecycle/regression adversary): CHALLENGE PASS, no
  blockers. One adopted suggestion: the early-failure guard now wraps
  `to_root` as well as `_get_ego` (pre-existing adjacent hole closed).
- Follow-up confirmation (test-setup reseed discovery): CHALLENGE PASS
  stands; setup change test-only and non-masking; silent-save wart
  correctly out of scope.
- A mid-pass flake (first-turn `dark` winner in one sandbox shape) was
  traced to the reseed confound, not the fix, and eliminated by the
  hardened setup — never by touching production.

## Discovered Issues Left For Their Own Passes (Not Fixed Here)

1. First-create `_save_profile` silently misses when `users/<id>/` does
   not exist yet (save precedes `seed_new_user`'s mkdir; error swallowed),
   so a fresh module re-seeds the user. Production heals at end-of-turn
   save; still, save-after-seed (or ensure-before-save, plus audible
   errors) belongs to a profile-durability pass.
2. Missing `profile.json` + existing partition files ⇒ full reseed
   OVERWRITES vault/identity/people state (recovery/migration policy
   question, M15 territory).
3. `pfc_focus.txt` / `aura_thoughts.txt` are shared-root channels outside
   the partition swap (pre-existing, noted in finding-#1 review too).
4. Non-atomic `bus_write` torn writes (pre-existing hardening note).

## Remaining Audit Findings

Still open: non-transactional writeback (#4), shadow context fields (#6),
lessons-as-correction (#8), belief-trust/people-importance readers (#9),
`memory_writes` journaling (#10), distributed personality/boundary
authority (#11), amygdala influence (#12), pack knob decisions (#14), and
bounded portions of #6/#11/#15. GF EXPERIENCE <-> OLD BRAIN INTEGRATION
remains IN PROGRESS. Finding #4 was not started.

## Result

AUDIT FINDING #2 PARTITION OWNERSHIP — READY FOR REVIEW.
