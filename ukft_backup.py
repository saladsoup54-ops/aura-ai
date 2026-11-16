# ukft_backup.py — AURA Backup & Restore
# ========================================
# Point-in-time snapshots of everything irreplaceable.  The vault is the
# crown jewel; the models (trigram_model.txt, temporal_links.txt) are
# deliberately excluded — they self-rebuild from the vault in seconds and
# would otherwise dominate snapshot size.
#
#   snapshot()  — copy the live files into backups/aura_<timestamp>/,
#                 with a sha1 manifest and a copy-time stability retry.
#   restore()   — copy a snapshot's files back over the live workspace.
#   rotate()    — keep the newest KEEP snapshots, delete older ones.
#
# Runs as a lobe (boot + every 30 minutes) and as a CLI:
#   python ukft_backup.py            take a snapshot now
#   python ukft_backup.py list       list snapshots
#   python ukft_backup.py verify [name]
#   python ukft_backup.py restore <name|latest>
# ========================================

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

from aura_constants import BACKUP_DIR

BACKUP_FILES = [
    "locked_patterns.txt",     # the vault — irreplaceable
    "identity_core.txt",       # who she is
    "episodic_memory.txt",     # what happened to her
    "discoveries.txt",         # what she found
    "working_memory.txt",      # the current conversation thread
    "ebbinghaus_traces.txt",   # the forgetting curves
    "forgotten_memories.txt",  # archive of faded episodes
    "field_state.txt",         # her resting manifold
    "sleep_state.txt",         # the rhythm
    "parietal_links.txt",      # association map
    "emotional_core.txt",      # emotional history
    "inner_monologue.txt",     # her thoughts
    "sleep_log.txt",
    "dream_log.txt",
    # Reasoning layer (small; rebuilds hourly, but a restore must not
    # leave a new-vault/old-graph mismatch behind for that hour).
    "extracted_relations.txt",
    "knowledge_graph.txt",
    "inferences.txt",
    "contradictions.txt",
    "knowledge_gaps.txt",
    "evaluation_report.txt",
    "relation_audit_sample.txt",
    "action_log.txt",
    "pending_action.txt",
    # Companion layer (small; a restore must not orphan her people).
    "people.txt",
    "pending_people.txt",
    "self_state.txt",
    "threads.txt",
    "beliefs.txt",
    "pending_belief.txt",
    "lessons.txt",
    # Rapport layer (small; a restore must not orphan how she feels).
    "rapport.txt",
    # Voice layer (tiny; without it she repeats her shapes).
    "register_state.txt",
]

KEEP_SNAPSHOTS = 14
CYCLE_SECONDS = 1800.0   # backup lobe cadence (30 minutes)
PREFIX = "aura_"


def _sha1(path, chunk=1 << 20):
    h = hashlib.sha1()
    try:
        with open(path, "rb") as f:
            while True:
                block = f.read(chunk)
                if not block:
                    break
                h.update(block)
    except OSError:
        return ""
    return h.hexdigest()


def _copy_stable(src, dst):
    """
    Copy src -> dst; retry while the source changes mid-copy (the vault
    appends while we snapshot).  Returns sha1 of dst, or None when the
    source never held still — certifying a torn copy as good would make
    verify() bless garbage, so unstable files are marked, not hashed.
    """
    for _ in range(3):
        try:
            before = os.stat(src)
            shutil.copy2(src, dst)
            after = os.stat(src)
        except OSError:
            return None
        if before.st_size == after.st_size and before.st_mtime == after.st_mtime:
            return _sha1(dst)
    return None


def _organism_running(lock_path="aura_instance.lock"):
    """
    True when a live organism holds the instance lock.  PIDs are matched
    exactly against the tasklist CSV column — never substring-matched
    (stale PID 12 must not match live PID 112).  Any doubt returns False
    so restores are never bricked by a broken check.
    """
    try:
        with open(lock_path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
        if not raw.isdigit():
            return False
        out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"],
                             capture_output=True, text=True, timeout=10)
        for line in (out.stdout or "").splitlines():
            cells = [c.strip().strip('"') for c in line.split('","')]
            if len(cells) >= 2 and cells[1] == raw:
                return True
        return False
    except Exception:
        return False


class BackupManager:
    def __init__(self, base_dir=BACKUP_DIR, keep=KEEP_SNAPSHOTS):
        self.base_dir = base_dir
        self.keep     = keep

    # ── SNAPSHOTS ─────────────────────────────────────────────────
    def snapshot(self):
        """Take a snapshot of every live file that exists. Returns info."""
        from aura_state import deny_live_write
        stamp = time.strftime("%Y%m%d_%H%M%S")
        target = os.path.join(self.base_dir, PREFIX + stamp)
        suffix = 1
        while os.path.exists(target):
            suffix += 1
            target = os.path.join(self.base_dir, f"{PREFIX}{stamp}_{suffix}")
        deny_live_write(target)
        try:
            os.makedirs(target, exist_ok=True)
        except OSError as e:
            return {"error": str(e)}

        manifest = {"created": time.time(), "stamp": stamp, "files": {}}
        unstable = []
        for name in BACKUP_FILES:
            if not os.path.exists(name):
                continue
            dst = os.path.join(target, name)
            digest = _copy_stable(name, dst)
            if digest is None:
                unstable.append(name)
                print(f"[Backup] WARNING: {name} never held still — "
                      f"marked unstable, not certified.")
            manifest["files"][name] = {
                "size": os.path.getsize(dst),
                "sha1": digest,
            }

        try:
            with open(os.path.join(target, "manifest.json"), "w",
                      encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
        except OSError:
            pass

        removed = self._rotate()
        info = {"snapshot": target, "files": len(manifest["files"]),
                "rotated_out": removed}
        if unstable:
            info["unstable"] = unstable
        return info

    def _rotate(self):
        snaps = self.list_snapshots()
        removed = []
        while len(snaps) > self.keep:
            oldest = snaps.pop(0)
            try:
                shutil.rmtree(oldest)
                removed.append(os.path.basename(oldest))
            except OSError:
                pass
        return removed

    def list_snapshots(self):
        # Ordered oldest-first by modification time, NOT by name: rapid
        # same-second snapshots reuse base names with numeric suffixes,
        # and lexicographic order would then mistake a newborn
        # ("..._2") for newer than it is — or a reused base name for
        # the oldest, rotating out a snapshot seconds after birth.
        try:
            names = [
                n for n in os.listdir(self.base_dir)
                if n.startswith(PREFIX) and
                os.path.isdir(os.path.join(self.base_dir, n))
            ]
        except OSError:
            return []
        names.sort(key=lambda n: (os.path.getmtime(os.path.join(
            self.base_dir, n)), n))
        return [os.path.join(self.base_dir, n) for n in names]

    def latest(self):
        snaps = self.list_snapshots()
        return snaps[-1] if snaps else None

    def resolve(self, name):
        if name == "latest":
            return self.latest()
        candidate = os.path.join(self.base_dir, name)
        if os.path.isdir(candidate):
            return candidate
        exact = [s for s in self.list_snapshots()
                 if os.path.basename(s) == name]
        if len(exact) == 1:
            return exact[0]
        # A partial name must pick out exactly one snapshot — an
        # ambiguous fragment refuses instead of restoring wrong.
        subs = [s for s in self.list_snapshots() if name in s]
        if len(subs) == 1:
            return subs[0]
        return None

    # ── RESTORE + VERIFY ──────────────────────────────────────────
    def verify(self, name="latest"):
        snap = self.resolve(name)
        if not snap:
            return None
        try:
            with open(os.path.join(snap, "manifest.json"),
                      encoding="utf-8") as f:
                manifest = json.load(f)
        except (OSError, ValueError):
            return None
        report = {"snapshot": snap, "ok": 0, "bad": [],
                  "missing": [], "unstable": []}
        for fname, info in manifest.get("files", {}).items():
            path = os.path.join(snap, fname)
            if not os.path.exists(path):
                report["missing"].append(fname)
                continue
            if not info.get("sha1"):
                report["unstable"].append(fname)
                continue
            if _sha1(path) == info.get("sha1"):
                report["ok"] += 1
            else:
                report["bad"].append(fname)
        return report

    def restore(self, name="latest"):
        """
        Copy a snapshot's files back over the live workspace — but only
        a verified snapshot, only while the organism is stopped, and
        only after a pre-restore safety snapshot of the current state.
        """
        if _organism_running():
            return {"error": "organism is running — stop Aura (Ctrl+C) "
                             "before restoring, then retry"}
        if os.path.exists("aura_instance.lock"):
            # A lock file with no live numeric PID is neither stopped
            # nor running — refuse rather than guess which.
            try:
                with open("aura_instance.lock", "r",
                          encoding="utf-8") as f:
                    raw = f.read().strip()
            except OSError:
                raw = ""
            if not raw.isdigit():
                return {"error": "instance lock is unreadable — refusing "
                                 "to restore blind; delete "
                                 "aura_instance.lock by hand if no Aura "
                                 "runs, then retry"}
        snap = self.resolve(name)
        if not snap:
            return {"error": f"snapshot not found: {name}"}
        report = self.verify(os.path.basename(snap))
        if not report or report["bad"] or report["missing"] \
                or report["unstable"]:
            return {"error": f"snapshot failed verification: {report}",
                    "report": report}
        pre = self.snapshot()
        if "error" in pre:
            return {"error": f"pre-restore safety snapshot failed: {pre}",
                    "report": report}
        if not os.path.isdir(snap):
            # The pre-restore snapshot's rotation may have evicted an
            # oldest restore source — abort, never restore half-blind.
            return {"error": "restore source rotated away during the "
                             "safety snapshot; retry with its pre-restore "
                             f"copy: {pre.get('snapshot')}"}
        restored = []
        extra = []
        from aura_state import deny_live_write
        for fname in BACKUP_FILES:
            src = os.path.join(snap, fname)
            if not os.path.exists(src):
                continue
            deny_live_write(fname)
            try:
                shutil.copy2(src, fname)
                restored.append(fname)
            except OSError as e:
                return {"error": f"restore failed on {fname}: {e}",
                        "restored": restored,
                        "pre_restore": pre.get("snapshot")}
        snap_files = {f for f in os.listdir(snap)
                      if os.path.isfile(os.path.join(snap, f))}
        live_extra = sorted(f for f in BACKUP_FILES
                            if os.path.exists(f)
                            and f not in snap_files)
        # Additive by design: files born after the snapshot (a newer
        # graph beside an older vault) are REPORTED, never deleted —
        # deleting live memory on autopsy is worse than the mismatch.
        result = {"snapshot": snap, "restored": restored,
                  "pre_restore": pre.get("snapshot")}
        if live_extra:
            result["extra_live_files_kept"] = live_extra
        return result


def run_backup():
    print("--- AURA BACKUP: POINT-IN-TIME SNAPSHOTS ACTIVE ---")
    mgr = BackupManager()
    while True:
        try:
            info = mgr.snapshot()
            if "error" in info:
                print(f"[Backup] Friction: {info['error']}")
            else:
                kept = len(mgr.list_snapshots())
                print(f"[Backup] Snapshot: {os.path.basename(info['snapshot'])} "
                      f"({info['files']} files, {kept} kept)")
        except Exception as e:
            print(f"[Backup] Friction: {e}")
        time.sleep(CYCLE_SECONDS)


def _cli():
    args = sys.argv[1:]
    mgr = BackupManager()
    if not args:
        info = mgr.snapshot()
        print(json.dumps(info, indent=2))
        return
    if args[0] == "list":
        for snap in mgr.list_snapshots():
            files = 0
            try:
                files = len(json.load(open(
                    os.path.join(snap, "manifest.json"),
                    encoding="utf-8")).get("files", {}))
            except (OSError, ValueError):
                pass
            print(f"{os.path.basename(snap)}  ({files} files)")
        return
    if args[0] == "verify":
        report = mgr.verify(args[1] if len(args) > 1 else "latest")
        print(json.dumps(report, indent=2))
        return
    if args[0] == "restore":
        if len(args) < 2:
            print("usage: python ukft_backup.py restore <name|latest>")
            return
        print("Stop Aura before restoring. Restoring...")
        print(json.dumps(mgr.restore(args[1]), indent=2))
        return
    print("usage: python ukft_backup.py [list|verify [name]|restore <name>]")


if __name__ == "__main__":
    _cli()
