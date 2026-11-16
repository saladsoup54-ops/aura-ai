"""Sandbox guard: refuse to clobber a real vault when a test runs
unsandboxed (the workspace vault is multi-megabyte; test corpora are
a few hundred bytes).  Always run suites via `python tests/run_all.py`,
which executes them in isolated temp sandboxes with a declared
per-suite state root (AURA_STATE_ROOT + AURA_TEST_MODE=1)."""

import os
import sys

REAL_VAULT_MIN_BYTES = 1_000_000


def guard(path="locked_patterns.txt", min_bytes=REAL_VAULT_MIN_BYTES):
    if os.path.exists(path) and os.path.getsize(path) > min_bytes:
        print(
            f"REFUSING: '{path}' is {os.path.getsize(path)} bytes and looks "
            f"like the real vault. Run tests via 'python tests/run_all.py' "
            f"so they execute in an isolated sandbox."
        )
        sys.exit(2)
    # State-root enforcement (hardening): no suite may run with CWD
    # inside the live organism tree, and test-mode runs must declare
    # a non-live state root. Uses aura_state when importable (every
    # supported invocation has the repo on sys.path); otherwise the
    # same check computed locally from this file's own location.
    try:
        import aura_state as _st
        _require = _st.require_test_root
        _test_mode = _st.in_test_mode
        _under_live = _st.under_live
        _Unsafe = _st.UnsafeRootError
    except Exception:
        _here = os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))
        _nc = os.path.normcase

        def _under_live(p):
            try:
                full = _nc(os.path.abspath(str(p)))
            except Exception:
                return False
            return full == _nc(_here) or full.startswith(
                _nc(_here) + os.sep)

        def _test_mode():
            return os.environ.get("AURA_TEST_MODE") == "1"

        class _Unsafe(RuntimeError):
            pass

        def _require():
            if not _test_mode():
                return None
            raw = os.environ.get("AURA_STATE_ROOT")
            if not raw or not str(raw).strip():
                raise _Unsafe("AURA_TEST_MODE=1 without AURA_STATE_ROOT")
            root = _nc(os.path.abspath(str(raw)))
            if root == _nc(_here) or root.startswith(_nc(_here)
                                                     + os.sep):
                raise _Unsafe(f"state root is live: {root}")
            cwd = _nc(os.path.abspath(os.getcwd()))
            if cwd == _nc(_here) or cwd.startswith(_nc(_here)
                                                   + os.sep):
                raise _Unsafe(f"test-mode CWD is live: {cwd}")
            return root
    try:
        if _test_mode():
            _require()
        elif _under_live(os.getcwd()):
            raise _Unsafe(
                "test running with CWD inside the live organism "
                "tree. Run tests via 'python tests/run_all.py' "
                "(sandboxed), or from a temp dir with AURA_TEST_MODE=1 "
                "and AURA_STATE_ROOT pointed at it.")
    except _Unsafe as e:
        print(f"REFUSING: {e}")
        sys.exit(2)

