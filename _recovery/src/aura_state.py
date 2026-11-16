# aura_state.py — State roots (production hardening)
# ==========================================================
# TWO ROOTS, NEVER CONFUSED:
#   live root .... the organism's home: the directory holding THIS
#                  file (the repo checkout she runs from).
#   active root .. where state files resolve. Declared EXPLICITLY
#                  by AURA_STATE_ROOT; defaults to the live root.
#                  CWD never determines it — CWD is only ever
#                  VERIFIED (test mode refuses a live-tree CWD).
#
# TEST MODE (AURA_TEST_MODE=1):
#   - AURA_STATE_ROOT must point at a temp dir (never live).
#   - Resolving or WRITING any path under the live root raises
#     LiveRootAccessError (reads stay allowed: hash proofs and
#     character packs read live files legitimately).
#   - require_test_root() is the gate: tests/_sandbox_guard calls
#     it, so every guarded suite enforces this at import.
#
# WHY NOT REWRITE ALL I/O: lobe I/O is CWD-relative by frozen
# engine law. The enforceable architecture is: explicit root
# declaration + live-CWD refusal + tripwires on the crown-jewel
# sinks (vault, people, graph, episodic, snapshots, partitions).
# run_all.py gives every suite its own temp root; nothing reachable
# from a test process can then name a live path for writing.
# ==========================================================

import hashlib
import os

STATE_ROOT_ENV = "AURA_STATE_ROOT"
TEST_MODE_ENV = "AURA_TEST_MODE"

# Live stores whose hashes prove a test run touched nothing.
PINNED_LIVE_FILES = (
    "locked_patterns.txt",
    "people.txt",
    "knowledge_graph.txt",
    "episodic_memory.txt",
)


class LiveRootAccessError(RuntimeError):
    """A test-mode write tried to reach live organism state."""


class UnsafeRootError(RuntimeError):
    """Test-mode root configuration is unsafe or undeclared."""


def live_root():
    """The organism's home directory (constant, never CWD)."""
    return os.path.normcase(os.path.abspath(
        os.path.dirname(__file__)))


def in_test_mode():
    """True only with AURA_TEST_MODE=1 (exact)."""
    return os.environ.get(TEST_MODE_ENV) == "1"


def active_root():
    """Declared state root: AURA_STATE_ROOT, else live. Consults
    ONLY the environment — never the current directory."""
    raw = os.environ.get(STATE_ROOT_ENV)
    if raw and str(raw).strip():
        return os.path.normcase(os.path.abspath(str(raw)))
    return live_root()


def under_live(path):
    """True when path resolves inside the live root tree."""
    try:
        full = os.path.normcase(os.path.abspath(str(path)))
    except Exception:
        return False
    root = live_root()
    return full == root or full.startswith(root + os.sep)


def under(path, root):
    """True when path resolves inside the given root tree."""
    try:
        full = os.path.normcase(os.path.abspath(str(path)))
        base = os.path.normcase(os.path.abspath(str(root)))
    except Exception:
        return False
    return full == base or full.startswith(base + os.sep)


def deny_live_write(path):
    """Hard-fail tripwire: test-mode writes under live raise.
    Reads are never gated. Production (not test mode) passes
    through untouched — zero behavioral impact when live."""
    if in_test_mode() and under_live(path):
        raise LiveRootAccessError(
            f"refusing test-mode write under live root: {path}")
    return str(path)


def require_test_root():
    """Gate for every test/stress process. Raises unless: test
    mode is on, a state root is declared, the root is NOT live,
    and CWD is NOT inside the live tree (repo-CWD execution can
    never proceed, guarded or not). Returns the active root."""
    if not in_test_mode():
        return active_root()
    raw = os.environ.get(STATE_ROOT_ENV)
    if not raw or not str(raw).strip():
        raise UnsafeRootError(
            "AURA_TEST_MODE=1 without AURA_STATE_ROOT: run suites via "
            "python tests/run_all.py, or point AURA_STATE_ROOT at an "
            "empty temp dir first.")
    root = active_root()
    if under_live(root):
        raise UnsafeRootError(
            f"AURA_STATE_ROOT points at live state: {root}")
    cwd = os.path.normcase(os.path.abspath(os.getcwd()))
    if under_live(cwd):
        raise UnsafeRootError(
            f"test-mode CWD is inside the live tree: {cwd}. Run via "
            "python tests/run_all.py, or move to a temp dir first.")
    return root


def check_startup(role="master"):
    """Organism boot guard: prints + records the active state root,
    refuses test-mode boots (tests must never boot her). Returns
    {"root": ..., "test_mode": ...}. Raises on mixed mode."""
    root = active_root()
    test = in_test_mode()
    line = (f"[State] ACTIVE STATE ROOT: {root} | "
            f"TEST MODE: {'ON' if test else 'off'} | role={role}")
    print(line, flush=True)
    try:
        with open("aura_console.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    if test:
        raise UnsafeRootError(
            "refusing to boot the organism in test mode "
            f"(root={root})")
    return {"root": root, "test_mode": test}


def live_state_hashes():
    """sha1 pins for the crown-jewel live files + snapshot tree
    listing. Read-only. Shared by run_all and the isolation suite
    so both prove the same thing the same way."""
    pins = {}
    for fname in PINNED_LIVE_FILES:
        try:
            with open(os.path.join(live_root(), fname), "rb") as f:
                pins[fname] = hashlib.sha1(f.read()).hexdigest()
        except OSError:
            pins[fname] = "<missing>"
    snaps = []
    bdir = os.path.join(live_root(), "backups")
    try:
        for name in sorted(os.listdir(bdir)):
            full = os.path.join(bdir, name)
            if os.path.isdir(full):
                try:
                    members = sorted(os.listdir(full))
                except OSError:
                    members = []
                snaps.append(f"{name}:{len(members)}")
    except OSError:
        pass
    pins["backups/"] = ";".join(snaps)
    return pins
