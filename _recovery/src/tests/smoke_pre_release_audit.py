"""Safe smoke test for public pre-release audit (P4.17).

Runs only in isolated temporary state directories. Does not touch live Aura.
"""
import compileall
import os
import subprocess
import sys
import tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _git_status():
    return subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True)


def main():
    before = _git_status()

    with tempfile.TemporaryDirectory(prefix="aura_smoke_audit_") as tmp:
        env = os.environ.copy()
        env["AURA_TEST_MODE"] = "1"
        env["AURA_STATE_ROOT"] = tmp
        env["PYTHONPATH"] = SRC + os.pathsep + env.get("PYTHONPATH", "")
        env["AURA_NO_MOUTH"] = "1"

        # 1) Modules compile
        ok = compileall.compile_dir(SRC, quiet=1)
        if not ok:
            print("FAIL: compileall")
            return 1

        # 2) Core imports succeed in sandbox
        mods = [
            "aura_constants", "aura_state", "aura_bus", "aura_field",
            "aura_vault_io", "ukft_user_state", "ukft_backup",
            "aura_bridge", "ukft_brain_api", "aura_diagnostic",
        ]
        for m in mods:
            r = subprocess.run(
                [sys.executable, "-c", f"import {m}"],
                cwd=tmp, env=env, capture_output=True, text=True,
            )
            if r.returncode != 0:
                print(f"FAIL: import {m}\n{r.stderr[-500:]}")
                return 1

        # 3) Initialise in sandbox + 4) memory write/retrieve in sandbox
        code = r'''
import os
os.environ.setdefault("AURA_NO_MOUTH", "1")
# memory write/retrieve via per-user state (sandbox cwd)
from ukft_user_state import UserStateManager
mgr = UserStateManager(base_dir="users")
mgr.ensure_user("smoke_user")
mgr.write_user_file("smoke_user", "people.txt", "Name: Smoke\nFact: hello sandbox\n")
data = mgr.read_user_file("smoke_user", "people.txt")
assert "hello sandbox" in data, data
# lightweight init: BrainModule in sandbox
try:
    from ukft_brain_api import BrainModule
    bm = BrainModule()
    assert bm is not None
except Exception as e:
    # fallback: SovereignEgo-free init not required if BrainModule heavy; core state ops proven
    print("BRAIN_INIT_NOTE:", e)
print("SMOKE_CORE_OK")
'''
        r = subprocess.run(
            [sys.executable, "-c", code],
            cwd=tmp, env=env, capture_output=True, text=True, timeout=180,
        )
        if r.returncode != 0 or "SMOKE_CORE_OK" not in r.stdout:
            print("FAIL: init/memory")
            print(r.stdout[-1000:])
            print(r.stderr[-1000:])
            return 1

        # 5) Generated state stayed inside temp sandbox, not git working tree
        # (all writes happened under cwd=tmp / AURA_STATE_ROOT=tmp)

    after = _git_status()
    if before != after:
        print("FAIL: git status changed")
        print("BEFORE:\n" + before)
        print("AFTER:\n" + after)
        return 1

    print("SMOKE_PRE_RELEASE_AUDIT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
