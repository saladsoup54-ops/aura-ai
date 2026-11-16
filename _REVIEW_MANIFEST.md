# REVIEW MANIFEST — CN0 Observability Completion (diagnostic, zero production change)

Date: 24 Sept 2026
Status: COMPLETE — CN0 baseline + observability; CN1 NOT started, no fix claimed
Purpose: close ONLY the observability fields of the CN0 trace contract
(winner -> grounded result -> cognitive_stance -> mouth input -> final
response). No production behavior change; F1/F2/F4 NOT fixed.

## Files changed by this pass (originals in repo root / tests/)

1. `tests/verify_cn0_conversation_trace.py` — full four-seam capture
   (grounded identity, stance record-and-return wrapper, exact mouth
   prompt), seam-integrity gates, four-seam comparison, emotion A/B/C/D
   table, E/F verdicts, F1-wording correction. Still diagnostic-only.
2. `AURA_CN0_CONVERSATIONAL_BASELINE_REPORT.md` — F1 wording corrected
   (roadmap-D withdrawn), new §8 observability completion, §9 next steps.
3. `AURA_CONVERSATION_NORMALIZATION_ROADMAP.md` — CN0 status COMPLETE note.
4. `AGENTS.md` — frontier: CN0 COMPLETE, CURRENT IMPLEMENTATION PHASE CN1.
5. `AURA_WANTED_FEATURES.md` — same frontier sync.
6. `AURA_CURRENT_CAPABILITIES.md` — observability completion + CN1 phase.
7. `AURA_CHANGELOG.md` — append-only observability-completion entry.

Production/runtime files changed: NONE. No weights, saliences, memory
rules, stance, or mouth behavior touched.

## Packet contents (copies only) with SHA-256 (source == copy asserted)

Source == packet-copy equality was asserted mechanically for every file
(Get-FileHash SHA256 both sides, 0 mismatches) at packet build time:

| SHA-256 | Original path |
|---|---|
| D91B53A79A05D270A89F496E8F3F037A97AF769379B081BEEBA9C5FE8900E329 | AURA_CN0_CONVERSATIONAL_BASELINE_REPORT.md |
| F68A23F3CBA11814819330104C98051A1D3F363076F527A8778F783084C5717F | AGENTS.md |
| 9A8ED64948D959A23823FE780CD26497242BBF22C67ACCB0AC6B8488316E6AD8 | SYSTEM_WHITEPAPER.md |
| A645C0D444E805044723DAD94DC46BAF7672916BD386B1E38E59E132FACD5D8F | AURA_CURRENT_CAPABILITIES.md |
| 0AF89C340F18DB63FF05FFD123044975A3A98B22D4561654DEA74C5F0ABEFC81 | AURA_WANTED_FEATURES.md |
| 3432F1FF161688F1C82740404580B7134545AF1B0B9634C6A18CE645EA16790B | AURA_CHANGELOG.md |
| 0CF64F42759C8C0F2845BF0DED43E479A39C8D7429B07340777BE710079499F6 | AURA_CONVERSATION_NORMALIZATION_ROADMAP.md |
| 7B59FB35F00A28E6D9F50FF5E904BE46BBA0747FC89A5614155D789B38AF4CEB | GF_PRODUCT_SPEC.md |
| 518C6BCF9A413B71CC16B7523E5CD6E09F16AEB72741B457A1D3F89D62EAF3C7 | tests/README.md |
| 13140F5D270CDF0B9A62C0083E8C21AF9F8D4F5D58E38FBEFCE0B67237A11A8C | tests/verify_cn0_conversation_trace.py |
| F68122DF3750C6692E38EB7574EDC17270F25C00584EB47A8372CB8704510F9D | tests/run_all.py |

Packet layout: root docs copied flat; test files under `tests/` (COPIES,
original paths in the table above).
Files deliberately NOT included: live state files, users/, observer_trace/,
backups/, logs, model files, archive/reference bulk, screenshots.

## Confirmations

- This packet contains COPIES ONLY. Nothing here replaces any original.
- `_review_packet/` is DISPOSABLE: no runtime, test, launcher, backup, or
  documentation process may use it as an execution source; safe to delete
  after review. (Recreated fresh this pass; previous packet removed first;
  no originals moved.)
- Zero production behavior change in this pass; suite remains diagnostic-only.
- Nothing in this packet is an authoritative replacement for the original
  project files.
