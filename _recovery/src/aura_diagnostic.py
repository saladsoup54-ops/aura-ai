# aura_diagnostic.py — RECONSTRUCTED 2026-11-16
# ============================================================
# The original was lost in the 2026-11 disk failure.  Rebuilt from the
# operator description in AURA_CURRENT_CAPABILITIES.md: "operator-run,
# not turn-called; classify it as a tool, not a lobe".
#
# Read-only: this tool never writes state, never touches the bus, and
# never imports a lobe.  Safe to run against a live organism.
# ============================================================

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from typing import Dict, List

import aura_state

WATCH_FILES = (
    "identity_core.txt", "self_state.txt", "emotional_core.txt",
    "people.txt", "locked_patterns.txt", "rapport.txt",
    "field_state.txt", "field_map.json", "field_stats.txt",
    "knowledge_graph.txt", "episodic_memory.txt", "working_memory.txt",
    "short_term_memory.txt", "beliefs.txt", "inferences.txt",
    "contradictions.txt", "sensory_buffer.txt", "processed_cortex.txt",
    "aura_output.txt", "aura_thoughts.txt", "aura_console.log",
    "gf_boundaries.md", "boundaries.md",
)


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def _lock_status(root: str) -> Dict:
    path = os.path.join(root, "aura_instance.lock")
    if not os.path.exists(path):
        return {"present": False}
    try:
        raw = open(path, "r", encoding="utf-8").read().strip()
        pid = int(raw)
    except (OSError, ValueError):
        return {"present": True, "pid": raw, "alive": None,
                "note": "unreadable lock"}
    return {"present": True, "pid": pid, "alive": _pid_alive(pid)}


def _state_files(root: str) -> List[Dict]:
    rows = []
    for name in WATCH_FILES:
        path = os.path.join(root, name)
        if not os.path.exists(path):
            rows.append({"file": name, "exists": False})
            continue
        stat = os.stat(path)
        rows.append({
            "file": name,
            "exists": True,
            "bytes": stat.st_size,
            "modified": time.strftime("%Y-%m-%d %H:%M:%S",
                                      time.localtime(stat.st_mtime)),
            "sha256": _sha256(path),
        })
    return rows


def _observer_summary(root: str) -> Dict:
    traces = 0
    turns = 0
    for base, _dirs, names in os.walk(root):
        if os.path.basename(base) != "observer_trace":
            continue
        for name in names:
            if not name.endswith(".jsonl"):
                continue
            traces += 1
            path = os.path.join(base, name)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    if any(line.strip() for line in f):
                        turns += 1
            except OSError:
                pass
    return {"trace_files": traces, "turns_with_events": turns}


def collect(root: str) -> Dict:
    return {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mode": "TEST" if aura_state.in_test_mode() else "LIVE",
        "root": root,
        "live_root": str(aura_state.live_root()),
        "under_live": aura_state.under_live(root),
        "instance_lock": _lock_status(root),
        "observer": _observer_summary(root),
        "state": _state_files(root),
        "python": sys.version.split()[0],
    }


def render(report: Dict) -> str:
    lines = [
        "AURA DIAGNOSTIC — operator report",
        "=" * 36,
        f"generated : {report['generated']}",
        f"mode      : {report['mode']}",
        f"root      : {report['root']}",
        f"live root : {report['live_root']}",
        f"python    : {report['python']}",
    ]
    lock = report["instance_lock"]
    if lock.get("present"):
        lines.append(f"lock      : pid {lock.get('pid')} "
                     f"({'alive' if lock.get('alive') else 'stale'})")
    else:
        lines.append("lock      : none")
    obs = report["observer"]
    lines.append(f"observer  : {obs['trace_files']} trace files, "
                 f"{obs['turns_with_events']} with events")
    lines.append("")
    lines.append("STATE FILES")
    lines.append(f"{'file':<26}{'bytes':>9}  {'modified':<19} sha256")
    for row in report["state"]:
        if not row["exists"]:
            lines.append(f"{row['file']:<26}{'-':>9}  {'MISSING':<19}")
        else:
            lines.append(f"{row['file']:<26}{row['bytes']:>9}  "
                         f"{row['modified']:<19} {row['sha256'][:12]}")
    missing = [r["file"] for r in report["state"] if not r["exists"]]
    lines.append("")
    lines.append(f"missing    : {len(missing)}"
                 + (f" ({', '.join(missing)})" if missing else ""))
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only operator diagnostic for Aura.")
    parser.add_argument("--json", action="store_true",
                        help="emit the report as JSON")
    parser.add_argument("--root", default=None,
                        help="state root to inspect (default: active root)")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.root or aura_state.active_root())
    report = collect(root)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
