# M16 FULL-ROUTE OBSERVABILITY REPORT

Date: 21 Sept 2026
Status: M16 COMPLETE AND HARDENED - READY FOR REVIEW
Scope: truthful observer-only evidence across the real
`BrainModule.roleplay()` route. No cognition, salience, selector, memory
policy, boundary, personality, rapport, or product redesign.

## Purpose

The desktop route had observer events, but the normal GF/Discord roleplay route
did not emit a complete lifecycle and the viewer could not prove which systems
actually affected the selected answer. M16 closes that observability gap while
preserving the observer as a non-causal sidecar.

## Mechanism

- `SovereignEgo.manifest_thought()` leaves an inert `selection_receipt` in the
  existing turn trace after the decision has already been made. It records
  bounded facts already computed for M1/M2/M3/M4/M13/M14, branch candidates,
  old-brain field activity, hearing writeback, and the selected basal winner.
- `BrainModule.roleplay()` creates one UUID-backed same-user turn ID, emits the
  real input-to-completion lifecycle, and classifies the completed selector
  receipt together with downstream stance/mouth facts only after those stages
  run. Standing questions remain pure reads but emit a complete lifecycle with
  no invented selector influence or writeback change.
- `observer_telemetry.route_evidence()` enforces the hierarchy DORMANT -> RAN
  -> OUTPUT PRODUCED -> OUTPUT USED -> INFLUENCED DECISION. It never reruns
  cognition or infers influence from response wording.
- Influence requires an existing system-specific causal basis. M3 selected
  proof/gap/exemption, M4 selected context or ownership guard, M13 applied
  conflict guard, M14 admitted selected episode or duplicate guard, restored
  old-brain field selection, and the basal winner have bounded bases. M1/M2
  consumed verdicts and selected people/belief/agenda/teach branches stop at
  OUTPUT USED without a turn-specific counterfactual or dedicated M5 receipt.
- Pass-2 stance and mouth are reported as downstream use, never as selector
  authority. Pass-1 hearing is future-turn output, not current-turn influence.
- Viewer/export reads explicit `system_evidence` events, validates allowed
  influence bases, renders compact route dots/links, and groups complete turns
  by `(user_id, turn_id)`. Legacy/bypass words in human summaries cannot create
  a route classification.
- `AURA_OBSERVER_DISABLED=1` is checked at runtime. The disabled path skips
  classification and emission and cannot alter selection or response.

## Evidence Levels

| Level | Meaning |
|---|---|
| RAN | The subsystem executed on this turn. |
| OUTPUT PRODUCED | It emitted a candidate, verdict, state, or downstream result. |
| OUTPUT USED | A later real stage consumed that output. |
| INFLUENCED DECISION | An existing causal receipt proves it changed or guarded the selected winner under the recorded condition. |

The hierarchy is monotonic: influence implies use, use implies production, and
production implies execution. Viewer validation downgrades malformed or
unsupported influence claims.

## Causal and Non-Causal Proofs

`tests/verify_m16_full_route_observability.py` exercises the real GF route:

- M13 query-relevant guard: selected conflict is INFLUENCED DECISION; detected
  but unrelated contradiction is only OUTPUT USED.
- M3 proof, M4 strong conversation context, M14 episode admission, and restored
  Pass-1/1A old-brain field selection appear as influential only on their
  proven conditions.
- M1/M2 verdict consumption, a selected people branch, Pass-2 stance, mouth,
  and Pass-1 hearing remain visibly lower than influence.
- Static mouth fallback remains downstream phrasing.
- Forged mood influence is downgraded by the viewer.
- Different users and identical turn IDs remain separate in viewer/export;
  concurrent roleplay calls and repeated no-turn standing reads create unique,
  complete monotonic trace streams.
- Observer-off execution produces the same winner, response, selector receipt,
  and M13 trace while writing no observer trace.

## Original Audit Reconciliation

This table follows the numbered findings in
`AURA_BRAIN_GF_INTEGRATION_AUDIT.md` section 8. Bounded closures do not imply
the complete target cognitive loop is finished.

| # | Original finding | Status after Pass 1/1A, Pass 2, M14, M16 | Evidence / remaining boundary |
|---|---|---|---|
| 1 | Empty-file API writeback incomplete | STILL OPEN | No general partition copyback redesign in these passes. |
| 2 | Ego/vault load may precede partition swap | STILL OPEN | No ego-cache or vault-reload redesign. |
| 3 | API field lifecycle never restores persisted field | CLOSED | Pass 1A restores, settles, and persists per-user field state across real API turns; background sleep/decay parity remains outside this finding. |
| 4 | Writeback is non-transactional | STILL OPEN | No transaction boundary added. |
| 5 | Normal roleplay route lacks observer lifecycle | CLOSED | M16 emits and validates the complete partitioned roleplay lifecycle. |
| 6 | Assembled context bundle is mostly shadow | REDUCED / STILL OPEN | Pass 2 creates a brain-owned stance and M14 adds bounded episode provenance; many assembled fields still do not enter selection. |
| 7 | API relationship/person state is temporally inconsistent | CLOSED for roleplay route | Pass 2 uses fresh rapport and live same-turn people state in the brain-owned stance consumed by the mouth. |
| 8 | Lessons are not a general correction mechanism | STILL OPEN | No lesson/correction redesign. |
| 9 | Belief trust and people importance lack behavioral readers | STILL OPEN | M16 reports branch use but does not create readers or causal influence. |
| 10 | `memory_writes` is not a reliable journal | STILL OPEN | M16 telemetry is evidence, not a transaction journal. |
| 11 | Personality and boundary truth are distributed | REDUCED / STILL OPEN | Pass 2 centralizes roleplay stance formation, but runtime authority remains distributed. |
| 12 | Amygdala-only selector influence unknown | STILL OPEN / UNKNOWN | M16 does not invent a causal claim. |
| 13 | Episode-only real-seam influence unknown | CLOSED within M14 scope | M14 proves relevant admission and active-G7 duplicate suppression at the real seam. |
| 14 | Pack knob runtime intent unresolved | STILL OPEN | Product decision unchanged. |
| 15 | Exact winner/writes for arbitrary live state are state-dependent | STILL OPEN by design | M16 proves controlled real-route cases; it does not claim a universal winner. |

## Files Changed

- Runtime: `aura_bridge.py`, `observer_telemetry.py`, `ukft_brain_api.py`,
  `aura_synapse_view.py`.
- Tests: `tests/verify_m16_full_route_observability.py`, `tests/run_all.py`,
  `tests/verify_observatory_contract.py`, `tests/verify_view.py`.
- Current docs: `AGENTS.md`, `SYSTEM_WHITEPAPER.md`,
  `AURA_CURRENT_CAPABILITIES.md`, `AURA_WANTED_FEATURES.md`,
  `GF_PRODUCT_SPEC.md`, `tests/README.md`, `AURA_CHANGELOG.md`.
- Report: `AURA_M16_FULL_ROUTE_OBSERVABILITY_REPORT.md`.

## Preserved Behaviour

- Candidate names, saliences, selector math, winners, proof priority, honest
  gaps, M1/M2/M3/M4/M13/M14 policy, Pass 1/1A field behavior, and Pass-2
  stance content are unchanged.
- Observer remains fail-open, removable, and M5-proven non-causal.
- The mouth still phrases only after the brain decision and cannot move it.
- No live state, user partition, observer trace, boundary, or historical record
  was used as test scratch space.

## Verification

- Pre-work snapshot: `backups/aura_20260921_080450`, verified 20/20.
- Focused M16 suite: all checks passed in a declared temporary state root.
- Observer contract and viewer verification: passed.
- The observer contract now fails closed unless test mode is on and its
  standalone process has a declared temporary test root.
- Final full shipping regression: 80/80 suites passed; embedded production
  isolation passed; live state clean.
- Safe stress workflow: 61/61 passed, 1 existing note.
- Viewer selftest: 40 connectome frames and 17 monitor tabs passed.
- Standalone observer-contract execution outside test mode refuses before any
  trace write.
- Final independent implementation review: no findings; verdict M16 COMPLETE
  AND HARDENED - READY FOR REVIEW.
- Fresh `_review_packet/` contains 17 authoritative-file copies, all verified
  SHA-256-identical to their originals, plus this manifest.
- One full-suite run performed concurrently with stress reported 79/80 without
  retaining the failed suite identity; the required dedicated rerun immediately
  afterward passed 80/80. Final gate status is based on the isolated workflow.
- No restore required.

## Known Boundaries

- M16 reports causality already proven by prior receipts; it is not a new
  causal harness and does not elevate selected legacy branches without proof.
- Traces follow the existing filesystem-safe user partition key. The broader
  pre-existing lossy-ID normalization contract is not redesigned here.
- Desktop observer behavior remains available; M16 specifically closes the
  real Brain API roleplay route required by GF/Discord.
- GF-to-old-brain integration remains IN PROGRESS. Pass 1/1A, Pass 2, M14, and
  M16 are bounded milestones, not proof that all sidecars are unified.

## Result

M16 FULL-ROUTE OBSERVABILITY COMPLETE AND HARDENED - READY FOR REVIEW.
