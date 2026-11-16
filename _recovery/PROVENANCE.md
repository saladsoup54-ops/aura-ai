# Provenance of reconstructed test support

Source: `new-session---2026-09-24t09-55-45-857z.json` (OpenCode session
`ses_f2d284fbeffeM70aj1WOrhf353`, cwd `C:\Users\DIYTE\OneDrive\Desktop\AURA_GF`, 24 Sept 2026).
Recovered by `_recovery/extract_tests.py`: full `read`/`write` snapshots with every subsequent
`edit` replayed in order. All 30 edit operations applied cleanly and all five files compile.

| file | lines | bytes | transcript source |
|---|---:|---:|---|
| `tests/run_all.py` | 209 | 10,215 | read msg 9 + edit msg 42 |
| `tests/README.md` | 69 | 22,316 | read msg 2 + edit msg 43 |
| `tests/_sandbox_guard.py` | 78 | 3,073 | read msg 9 |
| `tests/verify_cn0_conversation_trace.py` | 711 | 29,066 | write msg 20, edits 25–86 |
| `tests/verify_m16_full_route_observability.py` | 466 | 19,217 | read msg 4 (24 Sept snapshot) |

Notes:

- `run_all.py` declares **91 suites** — matches the final `RESULT: 91/91 suites passed` in the
  session (msg 98) and the 24 Sept `AGENTS.md`.
- The M16 file recovered here is the **24 Sept** version. The later attachment supplied by the user
  differs in exactly one assertion: `CN4 rejected drifting conflict mouth… evidence_level ==
  "OUTPUT PRODUCED"` vs this tree's `"mouth is downstream realization… OUTPUT USED"`. CN4 is an
  unimplemented roadmap phase, so the 24 Sept version is the correct baseline for this snapshot.
- These files are transcript-faithful but not original bytes. Per the project law, any suite
  *rewritten* rather than replayed must carry a `RECONSTRUCTED 2026-11-15` header. These did not
  need rewriting.
