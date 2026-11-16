# aura_state.py — State roots (production hardening)
# ==========================================================
# TWO ROOTS, NEVER CONFUSED:
#   live/code root ... where THIS file lives (the source/asset tree).
#                      Authored assets (packs, boundaries, code) stay here.
#   state root ....... where generated runtime state resolves.
#                      Declared by AURA_STATE_ROOT; in production it
#                      defaults to a per-user data dir OUTSIDE the repo:
#                        $XDG_DATA_HOME/aura  (if XDG_DATA_HOME set)
#                        ~/.local/share/aura  (Linux default)
#                      In test mode a temp AURA_STATE_ROOT is required.
#                      CWD never determines it.
#
# TEST MODE (AURA_TEST_MODE=1):
#   - AURA_STATE_ROOT must point at a safe temp dir (never code root,
#     never the real production state root).
#   - Resolving or WRITING any path under the code root or the real
#     production state root raises (reads stay allowed: hash proofs and
#     character packs read assets legitimately).
#   - require_test_root() is the gate: tests/_sandbox_guard calls it.
#
# Engine/lobe I/O is historically CWD-relative. The hardened path is an
# explicit, consistently applied state-path mechanism (resolve_state_path /
# state_path) used by bus primitives and persistent sinks, so runtime state
# lands in the state root regardless of launch CWD — without chdir tricks
# that would break imports or authored assets.
# ==========================================================

import hashlib
import os

STATE_ROOT_ENV = "AURA_STATE_ROOT"
TEST_MODE_ENV = "AURA_TEST_MODE"
XDG_DATA_HOME_ENV = "XDG_DATA_HOME"
APP_STATE_DIRNAME = "aura"

# Crown-jewel state files whose hashes prove a test run touched nothing
# in the real production state location.
PINNED_LIVE_FILES = (
    "locked_patterns.txt",
    "people.txt",
    "knowledge_graph.txt",
    "episodic_memory.txt",
)


class LiveRootAccessError(RuntimeError):
    """A test-mode write tried to reach live/protected state."""


class UnsafeRootError(RuntimeError):
    """Test-mode root configuration is unsafe or undeclared."""


def _norm(path):
    return os.path.normcase(os.path.abspath(str(path)))


def live_root():
    """Code/install root: directory holding this file (constant, never CWD).
    Use for authored assets; never for generated runtime state."""
    return _norm(os.path.dirname(__file__))


def in_test_mode():
    """True only with AURA_TEST_MODE=1 (exact)."""
    return os.environ.get(TEST_MODE_ENV) == "1"


def production_state_root():
    """Default production state root outside the repository (Linux/XDG).
    Respects XDG_DATA_HOME; explicit AURA_STATE_ROOT still overrides via
    active_root(). This location is protected from test-mode writes."""
    xdg = os.environ.get(XDG_DATA_HOME_ENV)
    if xdg and str(xdg).strip():
        base = os.path.abspath(os.path.expanduser(str(xdg).strip()))
    else:
        base = os.path.join(os.path.expanduser("~"), ".local", "share")
    return _norm(os.path.join(base, APP_STATE_DIRNAME))


def active_root():
    """Declared runtime state root. Consults ONLY the environment — never CWD.
    - AURA_STATE_ROOT set: explicit override (any mode).
    - Test mode without override: production default only as a placeholder;
      require_test_root() refuses unsafe configs before use.
    - Production without override: per-user data dir outside the repo."""
    raw = os.environ.get(STATE_ROOT_ENV)
    if raw and str(raw).strip():
        return _norm(os.path.expanduser(str(raw).strip()))
    return production_state_root()


def under(path, root):
    """True when path resolves inside the given root tree."""
    try:
        full = _norm(path)
        base = _norm(root)
    except Exception:
        return False
    return full == base or full.startswith(base + os.sep)


def under_live(path):
    """True when path resolves inside the code/install root tree."""
    return under(path, live_root())


def under_protected_state(path):
    """True when path resolves inside the real production state root."""
    try:
        return under(path, production_state_root())
    except Exception:
        return False


def ensure_state_dir(path=None):
    """Create the active state root (or a specific directory) if missing."""
    target = active_root() if path is None else str(path)
    try:
        os.makedirs(target, exist_ok=True)
    except Exception:
        pass
    return target


def resolve_state_path(path, root=None):
    """Resolve a persistent path into the state root.
    - Absolute paths are normalized and returned as-is.
    - Relative paths/names are joined with the active state root (or root).
    This is the central mechanism for runtime state I/O."""
    if path is None:
        return active_root() if root is None else _norm(root)
    try:
        p = str(path)
    except Exception:
        p = path
    try:
        if os.path.isabs(os.path.expanduser(p)):
            return _norm(os.path.expanduser(p))
    except Exception:
        pass
    base = active_root() if root is None else _norm(root)
    try:
        return _norm(os.path.join(base, p))
    except Exception:
        return os.path.join(base, str(p))


def state_path(*parts):
    """Join parts under the active state root (convenience helper)."""
    if not parts:
        return active_root()
    return resolve_state_path(os.path.join(*[str(p) for p in parts]))


def asset_path(*parts):
    """Join parts under the code/install root for authored assets."""
    if not parts:
        return live_root()
    return _norm(os.path.join(live_root(), *[str(p) for p in parts]))


def deny_live_write(path):
    """Hard-fail tripwire: in test mode, refuse writes under the code root
    or the real production state root. Reads are never gated. Production
    (not test mode) passes through untouched."""
    if in_test_mode():
        if under_live(path) or under_protected_state(path):
            raise LiveRootAccessError(
                f"refusing test-mode write under protected root: {path}")
    return str(path)


def require_test_root():
    """Gate for every test/stress process. Raises unless: test mode is on,
    a state root is declared, the root is not the code root and not the
    real production state root, and CWD is not inside the code tree.
    Returns the active root."""
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
            f"AURA_STATE_ROOT points at code/live root: {root}")
    try:
        prod = production_state_root()
        if under(root, prod) or root == prod:
            raise UnsafeRootError(
                f"AURA_STATE_ROOT points at real production state: {root}")
    except UnsafeRootError:
        raise
    except Exception:
        pass
    cwd = _norm(os.getcwd())
    if under_live(cwd):
        raise UnsafeRootError(
            f"test-mode CWD is inside the code/live tree: {cwd}. Run via "
            "python tests/run_all.py, or move to a temp dir first.")
    return root


def check_startup(role="master"):
    """Organism boot guard: ensure/record the active state root, refuse
    test-mode boots. Returns {"root": ..., "code_root": ..., "test_mode": ...}.
    Raises on mixed mode."""
    root = active_root()
    code = live_root()
    test = in_test_mode()
    try:
        os.makedirs(root, exist_ok=True)
    except Exception:
        pass
    line = (f"[State] ACTIVE STATE ROOT: {root} | "
            f"CODE ROOT: {code} | "
            f"TEST MODE: {'ON' if test else 'off'} | role={role}")
    print(line, flush=True)
    try:
        log_path = resolve_state_path("aura_console.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    if test:
        raise UnsafeRootError(
            "refusing to boot the organism in test mode "
            f"(root={root})")
    return {"root": root, "code_root": code, "test_mode": test}


def live_state_hashes():
    """sha1 pins for crown-jewel files in the real production state location
    + its backups listing. Read-only. Shared by run_all/isolation proofs to
    show tests did not touch real production state."""
    pins = {}
    # Pin the real production state root (never the temp test root).
    try:
        base = production_state_root()
    except Exception:
        base = live_root()
    for fname in PINNED_LIVE_FILES:
        try:
            with open(os.path.join(base, fname), "rb") as f:
                pins[fname] = hashlib.sha1(f.read()).hexdigest()
        except OSError:
            pins[fname] = "<missing>"
    snaps = []
    bdir = os.path.join(base, "backups")
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
    pins["state_root"] = base
    return pins

