#!/usr/bin/env python3
"""Isolated state-path hardening tests (no live Aura state).

Covers: default/XDG/AURA_STATE_ROOT resolution, persistent writes to
configured state dir, no generated state in git checkout from any launch
CWD, unsafe test-location refusal, and real production state untouched.
"""
import hashlib
import importlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO = os.path.abspath(os.path.join(SRC, "..", ".."))


def _clear_modules():
    for m in list(sys.modules):
        if m in ("aura_state", "aura_bus", "ukft_user_state", "ukft_backup",
                 "observer_telemetry", "aura_constants", "aura_vault_io",
                 "ukft_memory_vault", "ukft_console_log", "ukft_pdf_intake",
                 "aura_diagnostic"):
            del sys.modules[m]


def _prod_hashes():
    env = os.environ.copy()
    env.pop("AURA_TEST_MODE", None)
    env.pop("AURA_STATE_ROOT", None)
    # keep XDG as-is? no: we want real production root hashes; but running
    # this test must not depend on or modify them. Use a subprocess with
    # cleared overrides and SRC on path.
    code = (
        "import aura_state, json;"
        "print(json.dumps(aura_state.live_state_hashes(), sort_keys=True))"
    )
    r = subprocess.run([sys.executable, "-c", code], cwd=SRC, env=env,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError(f"cannot read prod hashes: {r.stderr}")
    return r.stdout.strip()


def _git_status():
    return subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True)


def main():
    if SRC not in sys.path:
        sys.path.insert(0, SRC)
    before_git = _git_status()
    before_prod = _prod_hashes()

    # --- default + XDG resolution (production mode, isolated XDG) ---
    with tempfile.TemporaryDirectory(prefix="aura_xdg_") as xdg, \
         tempfile.TemporaryDirectory(prefix="aura_cwd_") as cwd:
        env = os.environ.copy()
        env["XDG_DATA_HOME"] = xdg
        env.pop("AURA_STATE_ROOT", None)
        env.pop("AURA_TEST_MODE", None)
        env["PYTHONPATH"] = SRC + os.pathsep + env.get("PYTHONPATH", "")
        env["AURA_TEST_SRC"] = SRC
        code = r'''
import sys, os, json
src = os.environ.get("AURA_TEST_SRC")
cwd = os.path.abspath(os.getcwd())
sys.path = [p for p in sys.path if p not in ("", cwd)]
if src and src not in sys.path: sys.path.insert(0, src)
for m in list(sys.modules):
    if m.startswith("aura_") or m.startswith("ukft_") or m == "observer_telemetry": del sys.modules[m]
import aura_state
from aura_bus import write, read
from ukft_user_state import UserStateManager
import observer_telemetry as ot
ar = aura_state.active_root()
assert ar == aura_state.production_state_root(), (ar, aura_state.production_state_root())
assert ar.startswith(os.path.normcase(os.path.abspath(os.path.join(os.environ["XDG_DATA_HOME"], "aura")))) or os.path.join(os.environ["XDG_DATA_HOME"], "aura") in ar, ar
write("bus.txt", "hello")
assert read("bus.txt") == "hello"
assert os.path.exists(os.path.join(os.environ["XDG_DATA_HOME"], "aura", "bus.txt"))
us = UserStateManager("users")
us.ensure_user("u")
us.write_user_file("u", "people.txt", "x")
assert os.path.exists(os.path.join(os.environ["XDG_DATA_HOME"], "aura", "users", "u", "people.txt"))
td = ot._partition_dir("u")
assert os.path.join(os.environ["XDG_DATA_HOME"], "aura") in td or "observer_trace" in td
print(json.dumps({"ok": True, "active": ar}))
'''
        r = subprocess.run([sys.executable, "-c", code], cwd=cwd, env=env,
                           capture_output=True, text=True)
        assert r.returncode == 0, f"XDG/default test failed\n{r.stdout}\n{r.stderr}"
        assert os.path.exists(os.path.join(xdg, "aura", "bus.txt"))
        assert not os.path.exists(os.path.join(cwd, "bus.txt"))
        assert not os.path.exists(os.path.join(SRC, "bus.txt"))
        assert not os.path.exists(os.path.join(REPO, "bus.txt"))

    # --- AURA_STATE_ROOT override ---
    with tempfile.TemporaryDirectory(prefix="aura_override_") as sroot, \
         tempfile.TemporaryDirectory(prefix="aura_cwd_") as cwd:
        env = os.environ.copy()
        env["AURA_STATE_ROOT"] = sroot
        env.pop("XDG_DATA_HOME", None)
        env.pop("AURA_TEST_MODE", None)
        env["PYTHONPATH"] = SRC + os.pathsep + env.get("PYTHONPATH", "")
        env["AURA_TEST_SRC"] = SRC
        code = r'''
import sys, os
src = os.environ.get("AURA_TEST_SRC")
cwd = os.path.abspath(os.getcwd())
sys.path = [p for p in sys.path if p not in ("", cwd)]
if src and src not in sys.path: sys.path.insert(0, src)
for m in list(sys.modules):
    if m.startswith("aura_") or m.startswith("ukft_") or m == "observer_telemetry": del sys.modules[m]
import aura_state
from aura_bus import write, read
ar = aura_state.active_root()
assert ar == os.path.normcase(os.path.abspath(os.environ["AURA_STATE_ROOT"])), (ar, os.environ["AURA_STATE_ROOT"])
write("ov.txt", "ok")
assert read("ov.txt") == "ok"
assert os.path.exists(os.path.join(os.environ["AURA_STATE_ROOT"], "ov.txt"))
print("OV_OK")
'''
        r = subprocess.run([sys.executable, "-c", code], cwd=cwd, env=env,
                           capture_output=True, text=True)
        assert r.returncode == 0, f"override test failed\n{r.stdout}\n{r.stderr}"
        assert os.path.exists(os.path.join(sroot, "ov.txt"))
        assert not os.path.exists(os.path.join(cwd, "ov.txt"))

    # --- no generated state in checkout from source/repo/unrelated CWD ---
    for label, cwd in [("src", SRC), ("repo", REPO), ("tmp", tempfile.gettempdir())]:
        with tempfile.TemporaryDirectory(prefix="aura_xdg2_") as xdg:
            env = os.environ.copy()
            env["XDG_DATA_HOME"] = xdg
            env.pop("AURA_STATE_ROOT", None)
            env.pop("AURA_TEST_MODE", None)
            env["PYTHONPATH"] = SRC + os.pathsep + env.get("PYTHONPATH", "")
            code = r'''
import sys, os
src = os.environ.get("AURA_TEST_SRC")
cwd = os.path.abspath(os.getcwd())
sys.path = [p for p in sys.path if p not in ("", cwd)]
if src and src not in sys.path:
    sys.path.insert(0, src)
for m in list(sys.modules):
    if m.startswith("aura_") or m.startswith("ukft_") or m == "observer_telemetry":
        del sys.modules[m]
from aura_bus import write
from ukft_user_state import UserStateManager
ok = write("cwdcheck.txt", "1")
assert ok, "write failed"
us = UserStateManager("users"); us.ensure_user("c"); us.write_user_file("c","people.txt","y")
print("OK")
'''
            env["AURA_TEST_SRC"] = SRC
            r = subprocess.run([sys.executable, "-c", code], cwd=cwd, env=env,
                               capture_output=True, text=True)
            assert r.returncode == 0, f"cwd={label} failed\n{r.stdout}\n{r.stderr}"
            assert os.path.exists(os.path.join(xdg, "aura", "cwdcheck.txt")), (label, cwd, r.stdout, r.stderr)
            assert not os.path.exists(os.path.join(cwd, "cwdcheck.txt")), (label, cwd)
    # extra: ensure repo and src checkouts still clean of those artifacts
    assert not os.path.exists(os.path.join(REPO, "cwdcheck.txt"))
    assert not os.path.exists(os.path.join(SRC, "cwdcheck.txt"))

    # --- unsafe test locations refused ---
    with tempfile.TemporaryDirectory(prefix="aura_safe_") as safe:
        env = os.environ.copy()
        env["AURA_TEST_MODE"] = "1"
        env["PYTHONPATH"] = SRC + os.pathsep + env.get("PYTHONPATH", "")
        env["AURA_TEST_SRC"] = SRC
        pre = ("import sys,os; src=os.environ.get('AURA_TEST_SRC'); "
               "cwd=os.path.abspath(os.getcwd()); "
               "sys.path=[p for p in sys.path if p not in ('',cwd)]; "
               "sys.path.insert(0,src) if src and src not in sys.path else None; "
               "[sys.modules.pop(m,None) for m in list(sys.modules) if m.startswith('aura_') or m.startswith('ukft_') or m=='observer_telemetry'];\n")
        # missing AURA_STATE_ROOT
        env.pop("AURA_STATE_ROOT", None)
        r = subprocess.run([sys.executable, "-c", pre + "import aura_state; aura_state.require_test_root()"],
                           cwd=safe, env=env, capture_output=True, text=True)
        assert r.returncode != 0, f"expected refusal without AURA_STATE_ROOT\n{r.stdout}\n{r.stderr}"

        # AURA_STATE_ROOT pointing at code root
        env["AURA_STATE_ROOT"] = SRC
        r = subprocess.run([sys.executable, "-c", pre + "import aura_state; aura_state.require_test_root()"],
                           cwd=safe, env=env, capture_output=True, text=True)
        assert r.returncode != 0, f"expected refusal for code-root AURA_STATE_ROOT\n{r.stdout}\n{r.stderr}"

        # CWD inside code/live tree
        env["AURA_STATE_ROOT"] = safe
        r = subprocess.run([sys.executable, "-c", pre + "import aura_state; aura_state.require_test_root()"],
                           cwd=SRC, env=env, capture_output=True, text=True)
        assert r.returncode != 0, f"expected refusal for code-tree CWD\n{r.stdout}\n{r.stderr}"

    # --- real production state untouched + git unchanged ---
    after_prod = _prod_hashes()
    assert before_prod == after_prod, f"real production state changed!\nBEFORE={before_prod}\nAFTER={after_prod}"
    after_git = _git_status()
    assert before_git == after_git, f"git status changed!\nBEFORE={before_git}\nAFTER={after_git}"

    print("STATE_HARDENING_TESTS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
