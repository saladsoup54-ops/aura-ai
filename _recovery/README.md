# AURA recovery workspace

Created 15 Nov 2026. The original dump in the project root is **untouched** — nothing was renamed,
deleted or edited there.

## Contents

| path | what it is |
|---|---|
| `CHECKSUMS.sha256` | sha256 of all 93 original files (91 attachments + `ARCHIVE_README.txt` + zip) |
| `AUDIT_REPORT_2026-11-15.md` | full line-by-line consistency audit + per-file table |
| `src/` | 75 modules, suffixes stripped, one copy per module — the first runnable tree |
| `src/tests/` | recovered test support: `run_all.py` (91 suites), `README.md`, `_sandbox_guard.py`, `verify_cn0…`, `verify_m16…` |
| `PROVENANCE.md` | where each recovered test file came from, with message ids |
| `extract_tests.py` | re-runs the transcript extraction (idempotent) |

## Status

- All 76 original `.py` parse. 27,152 lines.
- Canonical tree: 75 files, all compile, 0 missing symbols.
- Isolated import test: **75/75 modules import cleanly** with
  `AURA_TEST_MODE=1 AURA_STATE_ROOT=<tmp>`.
- One real defect: `aura_master.py:294` references undefined `memory_block`
  (swallowed by `except Exception` → master debug dumps never fire).
- Test support recovered from transcript: `run_all.py` (91 suites), `tests/README.md`,
  `_sandbox_guard.py`, two verify scripts. 89 suite bodies still to rebuild.
- Missing to be runnable/verifiable: `aura_diagnostic.py`, the 89 test files,
  Linux launchers, Linux PID/TTS shims.

## Re-run the verification

```bash
cd _recovery/src
python3 - <<'PY'
import ast, os, sys, builtins
files = sorted(f for f in os.listdir(".") if f.endswith(".py"))
mods = {f[:-3] for f in files}
def top(t):
    out = set()
    for n in ast.walk(t):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)): out.add(n.name)
        elif isinstance(n, ast.Assign):
            out.update(x.id for x in n.targets if isinstance(x, ast.Name))
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            out.update(a.asname or a.name.split(".")[0] for a in n.names)
    return out
tops = {f[:-3]: top(ast.parse(open(f, encoding="utf-8").read())) for f in files}
bad = []
for f in files:
    t = ast.parse(open(f, encoding="utf-8").read())
    for n in ast.walk(t):
        if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module in mods:
            bad += [(f, n.lineno, a.name) for a in n.names
                    if a.name != "*" and a.name not in tops[n.module] and a.name not in dir(builtins)]
print("files", len(files), "missing symbols", len(bad))
PY
```

Import test (safe — writes only to the temp root):

```bash
tmp=$(mktemp -d)
for m in _recovery/src/*.py; do
  mod=$(basename "$m" .py)
  AURA_TEST_MODE=1 AURA_STATE_ROOT="$tmp" PYTHONPATH=_recovery/src \
    python3 -c "import $mod" || echo "FAIL $mod"
done
```

## Next steps

1. Fix `memory_block` (one line) — but only after the suite exists, so the fix is tested.
2. First sandbox boot against `_recovery/src` with a throwaway state root.
3. Rebuild the 89 test suites in the documented order (m5 harness → isolation → causal → M-series →
   findings → G/C/F/R/I → passes), each with a `RECONSTRUCTED 2026-11-15` header.
4. Linux port: `os.kill(pid, 0)` PID probes, TTS/STT replacement, `.sh` launchers, `python3-tk`.
5. Docs reconciliation + new SHA manifest.

## Status 2026-11-16 — runtime rebuilt, boot proven

- Linux port complete (PID probes via `os.kill`, espeak TTS, `/bin/sh` motor).
- `aura_diagnostic.py` rebuilt (read-only operator tool).
- M16 viewer API added to `aura_synapse_view.py` (`ROUTE_SYSTEMS`,
  `evidence_receipts`, `export_real_turns`, `format_evidence_table`,
  `build_diagnostics_text`, `export_diagnostics`).
- `memory_block` NameError in `aura_master.py` fixed.
- Launchers: `Boot_Aura.sh`, `Launch_Aura.sh`, `Start_Aura.sh`, `Stop_Aura.sh`.
- First sandbox boot passed: `--- AURA READY ---`, ego established, no
  tracebacks. Evidence in `evidence/first_boot_2026-11-16.log`.
- Plan: `TODO.md` (Phase A runtime -> Phase B 91 suites -> Phase C docs).

Host GUI deps still required: `sudo apt install python3-tk` and `pip install pygame`.
