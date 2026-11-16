# ukft_perpetual.py — AURA Perpetual Engineering (V6 C11)
# ==================================================
# Always-on robustness, as executable checks rather than wishes:
#
#   - preflight(): boot safety — refuse a second organism (live
#     lock), note stale locks (the master overwrites those),
#     prove every state file parses with its current reader
#     (upgrade-safety: tolerant readers, version headers), and
#     confirm backups are recent.  Missing files on a fresh
#     workspace are notes, not errors — first boot creates them.
#   - storage_report(): every known store measured against the
#     CAPS registry.  Bounded stores flag over-cap; unbounded
#     ones (vault, beliefs, people records) carry their reason
#     in the registry — growth by design, never by accident.
#   - soak(): the multi-day gate's little sibling — mixed live
#     load (field, bus, ego incl. the C-track) with per-round
#     invariants (no exceptions, state parses, vault never
#     shrinks).  Run `python ukft_perpetual.py soak <minutes>`
#     for C-I evidence; the suite runs a short round.
# ==================================================

import os
import subprocess
import time

CAPS = [
    # (path, kind, limit, note) — kind lines/bytes/count/records.
    ("locked_patterns.txt", "bytes", None,
     "canonical growth: the vault only ever grows, by law"),
    ("episodic_memory.txt", "count", 500, "oldest fades first"),
    ("knowledge_gaps.txt", "count", 2000, "stalest make room"),
    ("identity_core.txt", "count", 60, "founding floor protected"),
    ("lessons.txt", "count", 200, "oldest drop first"),
    ("threads.txt", "count", 50, "closed then oldest go"),
    ("people.txt", "records", None,
     "one small record per person, kept forever by design"),
    ("beliefs.txt", "records", None,
     "the Architect's word is never deleted; trust moves instead"),
    ("dream_log.txt", "lines", 2000, "entropy trimmer"),
    ("inner_monologue.txt", "lines", 500, "self-trimming lobe"),
    ("emotional_core.txt", "lines", 2000, "entropy trimmer"),
    ("short_term_memory.txt", "lines", 50, "entropy trimmer"),
    ("sleep_log.txt", "lines", 5000, "entropy trimmer (C11)"),
    ("basal_ganglia_log.txt", "lines", 200, "decision log cap"),
    ("action_log.txt", "lines", 2000, "entropy trimmer (audit fix)"),
    ("aura_console.log", "bytes", 1000000, "mirror cap, newest kept"),
    ("working_memory.txt", "turns", 8, "thread buffer"),
    ("register_state.txt", "lines", 20, "opener rotation memory (V7 F1)"),
    ("parietal_links.txt", "lines", 5000, "link-map cap"),
    ("trigram_model.txt", "bytes", None,
     "derived artifact, pruned in-engine, rebuildable"),
    ("temporal_links.txt", "bytes", None,
     "in-memory pairs capped at 500k; file follows"),
    ("field_map.json", "bytes", None,
     "heartbeat export, bounded by the 5000-node ceiling"),
]

STATE_FILES = [path for path, _k, _l, _n in CAPS]


def _join(workdir, path):
    return path if os.path.isabs(path) else os.path.join(workdir, path)


def _pid_alive(pid):
    """
    Cross-process liveness with EXACT pid matching (CSV columns).
    A substring test matches stale PID 1908 inside live PID 11908
    and wrongly refuses boot — the same bug class verify_pass05
    killed in aura_master.
    """
    try:
        out = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=10)
        for line in (out.stdout or "").splitlines():
            cells = [c.strip().strip('"') for c in line.split('","')]
            if len(cells) >= 2 and cells[1] == str(int(pid)):
                return True
        return False
    except Exception:
        try:
            os.kill(int(pid), 0)
            return True
        except Exception:
            return False


def check_lock(workdir=".", lock="aura_instance.lock"):
    """
    ("ok" | "stale" | "live", detail).  Live means a second boot
    must refuse; stale is reported (the master overwrites it).
    """
    path = _join(workdir, lock)
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
    except OSError:
        return ("ok", "no lock file — first boot")
    try:
        pid = int(raw.split()[0])
    except (ValueError, IndexError):
        return ("stale", f"unparseable lock {raw!r}")
    if _pid_alive(pid):
        return ("live", f"lock held by live PID {pid} — refuse boot")
    return ("stale", f"lock holds dead PID {pid} — safe to overwrite")


def check_states(workdir="."):
    """
    Every state file with a reader must parse; files may be
    absent (fresh workspace).  Returns [(path, "ok"/"missing"/
    "unparseable", detail)] — unparseable is the only failure.
    """
    results = []
    checks = []
    try:
        from ukft_people import _parse_people
        checks.append(("people.txt", lambda t: _parse_people(t)))
        from ukft_belief import _parse_beliefs
        checks.append(("beliefs.txt",
                       lambda t: _parse_beliefs(t)))
        from ukft_agenda import _parse_threads
        checks.append(("threads.txt", lambda t: _parse_threads(t)))
        from ukft_teach import _parse_lessons
        checks.append(("lessons.txt", lambda t: _parse_lessons(t)))
        from ukft_episodic import EpisodicMemory
        checks.append(("episodic_memory.txt",
                       lambda t: EpisodicMemory(
                           path=_join(workdir, "episodic_memory.txt"))))
        from ukft_gaps import KnowledgeGaps
        # NOTE: absolute paths throughout — bus_read/open resolve
        # against the process CWD, not workdir.
        checks.append(("knowledge_gaps.txt",
                       lambda t: KnowledgeGaps(
                           path=_join(workdir,
                                      "knowledge_gaps.txt"))))
        from ukft_identity import IdentityCore
        checks.append(("identity_core.txt",
                       lambda t: IdentityCore(
                           path=_join(workdir, "identity_core.txt"))))
        from ukft_working_memory import WorkingMemory
        checks.append(("working_memory.txt",
                       lambda t: WorkingMemory(
                           path=_join(workdir, "working_memory.txt"))))
        from ukft_self import DriveState
        checks.append(("self_state.txt",
                       lambda t: DriveState(
                           path=_join(workdir, "self_state.txt"))))
        from ukft_register import parse_history
        checks.append(("register_state.txt",
                       lambda t: parse_history(t)))
    except Exception as e:  # pragma: no cover — import-time only
        return [("imports", "unparseable", str(e))]
    for path, load in checks:
        full = _join(workdir, path)
        if not os.path.exists(full):
            results.append((path, "missing", "first boot creates it"))
            continue
        try:
            with open(full, "r", encoding="utf-8",
                      errors="ignore") as f:
                text = f.read()
            load(text)
            results.append((path, "ok", "parses with current reader"))
        except Exception as e:
            results.append((path, "unparseable", str(e)[:120]))
    # The vault: readable with living lines (never fully parsed —
    # 13 MB on every boot would be its own denial of service).
    vault = _join(workdir, "locked_patterns.txt")
    if not os.path.exists(vault):
        results.append(("locked_patterns.txt", "missing",
                        "first boot creates it"))
    else:
        try:
            with open(vault, "r", encoding="utf-8",
                      errors="ignore") as f:
                head = [next(f) for _ in range(50)]
            if not head:
                results.append(("locked_patterns.txt", "unparseable",
                                "vault file is empty"))
            else:
                results.append(("locked_patterns.txt", "ok",
                                f"readable, {len(head)} head lines scan"))
        except Exception as e:
            results.append(("locked_patterns.txt", "unparseable",
                            str(e)[:120]))
    return results


def check_backups(workdir=".", max_age_hours=30.0):
    """Latest snapshot exists and is younger than max_age_hours."""
    bdir = _join(workdir, "backups")
    try:
        snaps = sorted(d for d in os.listdir(bdir)
                       if d.startswith("aura_"))
    except OSError:
        return ("missing", "no backups directory")
    if not snaps:
        return ("missing", "no snapshots yet")
    try:
        age = (time.time() - os.path.getmtime(
            os.path.join(bdir, snaps[-1]))) / 3600.0
    except OSError:
        return ("missing", "latest snapshot unreadable")
    if age > max_age_hours:
        return ("stale",
                f"latest {snaps[-1]} is {age:.1f}h old")
    return ("ok", f"latest {snaps[-1]} is {age:.1f}h old")


def preflight(workdir="."):
    """
    Boot safety as data: {"ok", "fatal", "warnings"}.  Fatal
    only on a live rival lock or an unreadable vault —
    everything else is a warning the organism outlives.
    """
    fatal, warnings = [], []
    status, detail = check_lock(workdir)
    if status == "live":
        fatal.append(f"instance lock: {detail}")
    elif status == "stale":
        warnings.append(f"instance lock: {detail}")
    for path, state, detail in check_states(workdir):
        if state == "unparseable":
            if path == "locked_patterns.txt":
                fatal.append(f"{path}: {detail}")
            else:
                warnings.append(f"{path}: {detail}")
    bstate, bdetail = check_backups(workdir)
    if bstate != "ok":
        warnings.append(f"backups {bstate}: {bdetail}")
    return {"ok": not fatal, "fatal": fatal, "warnings": warnings}


def _count_lines(path):
    try:
        with open(path, "r", encoding="utf-8",
                  errors="ignore") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def _count_records(path, marker):
    try:
        with open(path, "r", encoding="utf-8",
                  errors="ignore") as f:
            return sum(1 for line in f if line.startswith(marker))
    except OSError:
        return 0


def storage_report(workdir="."):
    """
    Every known store measured: [{path, bytes, count, cap_kind,
    cap, over}].  over=True is the C-I tripwire — bounded
    stores must never trip it; unbounded ones document why.
    """
    rows = []
    for path, kind, cap, _note in CAPS:
        full = _join(workdir, path)
        try:
            size = os.path.getsize(full)
        except OSError:
            size = 0
        count = None
        if kind == "lines":
            count = _count_lines(full)
        elif path == "episodic_memory.txt":
            count = _count_records(full, "EPISODE: ")
        elif path == "knowledge_gaps.txt":
            count = _count_records(full, "GAP: ")
        elif path == "identity_core.txt":
            count = _count_records(full, "IDENTITY: ")
        elif path == "lessons.txt":
            count = _count_records(full, "LESSON: ")
        elif path == "threads.txt":
            count = _count_records(full, "THREAD: ")
        elif path == "people.txt":
            count = _count_records(full, "PERSON: ")
        elif path == "beliefs.txt":
            count = _count_records(full, "BELIEF: ")
        elif path == "basal_ganglia_log.txt":
            count = _count_lines(full)
        over = cap is not None and (
            (kind == "bytes" and size > cap)
            or (kind != "bytes" and (count or 0) > cap))
        rows.append({"path": path, "bytes": size, "count": count,
                     "cap_kind": kind, "cap": cap, "over": bool(over)})
    return rows


def soak(minutes=0.25, workdir=".", turns=()):
    """
    Mixed live load with per-round invariants: no exceptions,
    state still parses, the vault never shrinks.  Returns
    {"rounds", "elapsed", "errors"}.  Point it at a sandbox —
    ego turns record episodes where it runs.
    """
    import time as _time
    here = os.path.abspath(os.getcwd())
    os.chdir(workdir)
    errors, rounds = [], 0
    start = _time.time()
    vault0 = os.path.getsize("locked_patterns.txt") \
        if os.path.exists("locked_patterns.txt") else None
    try:
        from aura_bridge import SovereignEgo
        from aura_field import CognitiveField
        ego = SovereignEgo()
        field = CognitiveField()
        script = list(turns) or [
            "hello", "how are you", "is solomon the child of david",
            "who is zorblax", "what did we talk about today",
            "our story so far", "what have you learned",
            "how confident are you about unix",
        ]
        i = 0
        while _time.time() - start < minutes * 60.0:
            try:
                field.step()
                field.stimulate("soak", strength=0.1)
                ego.manifest_thought(script[i % len(script)])
                for path, state, _d in check_states("."):
                    if state == "unparseable":
                        raise AssertionError(f"{path} unreadable")
                if vault0 is not None and os.path.exists(
                        "locked_patterns.txt"):
                    if os.path.getsize("locked_patterns.txt") < vault0:
                        raise AssertionError("vault shrank")
                rounds += 1
                i += 1
            except AssertionError as e:
                errors.append(str(e))
                break
            except Exception as e:  # noqa: BLE001 — the soak logs all
                errors.append(f"{type(e).__name__}: {e}")
                break
    finally:
        os.chdir(here)
    return {"rounds": rounds, "elapsed": _time.time() - start,
            "errors": errors}


if __name__ == "__main__":
    import sys as _sys
    cmd = _sys.argv[1] if len(_sys.argv) > 1 else "preflight"
    if cmd == "preflight":
        rep = preflight()
        print("PREFLIGHT:", "OK" if rep["ok"] else "NOT OK")
        for f in rep["fatal"]:
            print("  FATAL:", f)
        for w in rep["warnings"]:
            print("  warn:", w)
    elif cmd == "storage":
        for row in storage_report():
            flag = " OVER" if row["over"] else ""
            print(f"  {row['path']}: {row['bytes']}B "
                  f"count={row['count']} cap={row['cap']}{flag}")
    elif cmd == "soak":
        mins = float(_sys.argv[2]) if len(_sys.argv) > 2 else 1.0
        rep = soak(minutes=mins)
        print(f"SOAK: {rep['rounds']} rounds in "
              f"{rep['elapsed']:.1f}s errors={rep['errors']}")
