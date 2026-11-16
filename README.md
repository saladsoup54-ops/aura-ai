# AURA

## Project Overview

AURA is an open-source **stateful Python agent framework** for local, long-running conversational applications. It combines a **modular cognitive architecture simulation** with persistent local state, long-term memory, a **Tkinter desktop GUI**, and optional **espeak-ng local text-to-speech** integration.

The core response-selection loop is implemented in Python and does not require a cloud service. An optional local phrasing model can be attached for more natural surface wording; without one, the agent uses deterministic templates.

The project is experimental and under active development. The primary runnable source tree is [`_recovery/src/`](_recovery/src/). The Python files at the repository root are preserved reference copies from the original project layout and are not the primary build target.

**Original author:** Matthew (`saladsoup54-ops`)

---

## Key Architecture & Components

AURA is organized as a set of cooperating modules around a shared state layer. The main implementation lives in `_recovery/src/`.

| Component | Role |
|---|---|
| `_recovery/src/` | Primary source directory containing the runnable implementation and tests. |
| `aura_master.py` | Process entry point and main runtime loop. |
| `aura_bridge.py` | Central orchestration and response-selection pipeline. |
| `ukft_*.py` | Modular cognitive subsystems: activation/field behaviour, memory, reasoning, rapport, boundaries, policy, intake, and related processes. |
| `aura_ui.py` | Tkinter desktop GUI. |
| `aura_synapse_view.py` | Optional Pygame-based visualisation of internal state. |
| `aura_state.py` | Central state-root resolution, XDG compliance, and test/write protections. |
| `aura_bus.py` | Lock-protected file-based message and state primitives. |
| `ukft_user_state.py` | Per-user partition storage. |
| `ukft_backup.py` | Snapshot, restore, and verification tooling. |
| `observer_telemetry.py` | Observer trace emission and export. |
| `characters/` | Authored character/personality packs and related assets. These are source assets, not runtime state. |

Runtime state is written outside the source tree. Authored assets such as character packs and boundary files remain with the code.

---

## Prerequisites & Dependencies

### Supported platform

- Ubuntu 22.04/24.04 or a compatible Debian-based Linux distribution
- Python 3.10 or newer
- CPU-only operation is supported; a GPU is not required for the core system

### System packages

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv python3-tk \
  python3-requests python3-bs4 python3-pypdf python3-pygame espeak-ng
```

| Package | Purpose |
|---|---|
| `python3-tk` | Tkinter desktop GUI |
| `python3-requests` | HTTP calls for local model and intake features |
| `python3-bs4` | HTML parsing for web intake |
| `python3-pypdf` | PDF intake |
| `python3-pygame` | Optional 3D visualisation |
| `espeak-ng` | Local text-to-speech |

Package availability can vary by distribution release. If a package is unavailable, install the equivalent Python package inside a virtual environment.

### Python requirements

Python dependencies are listed in [`requirements.txt`](requirements.txt) and [`_recovery/src/requirements.txt`](_recovery/src/requirements.txt).

Modern Ubuntu/Debian systems block system-wide `pip install` by default (PEP 668). Use distribution packages or a virtual environment; do not use `--break-system-packages`.

### Optional local phrasing model

AURA can use a local model for surface phrasing. This is optional: without it, the agent falls back to deterministic template output. Setup instructions for Ollama and `llama-server` are in [`SETUP.md`](SETUP.md).

---

## Quickstart / Installation

```bash
git clone https://github.com/saladsoup54-ops/aura-ai.git
cd aura-ai

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

cd _recovery/src
./Launch_Aura.sh
```

### Launch commands

Run these from `_recovery/src/`:

```bash
./Launch_Aura.sh            # core process + desktop GUI
./Launch_Aura.sh --view     # core process + desktop GUI + 3D view
./Start_Aura.sh             # headless mode
./Stop_Aura.sh              # stop the running process
python3 aura_diagnostic.py  # read-only diagnostic report
```

If a script is not executable:

```bash
chmod +x Launch_Aura.sh Start_Aura.sh Stop_Aura.sh
```

If you use a virtual environment, activate it before launching so the scripts use the correct Python interpreter.

For a detailed Ubuntu/Debian setup walkthrough, including optional model configuration and troubleshooting, see [`SETUP.md`](SETUP.md).

---

## State & Memory Storage

AURA stores persistent runtime state outside the Git checkout by default.

Resolution order:

1. `AURA_STATE_ROOT`, if set
2. `$XDG_DATA_HOME/aura`, if `XDG_DATA_HOME` is set
3. `~/.local/share/aura` on Linux

The resolved state directory can contain:

- per-user partitions under `users/`
- long-term and working memory data
- locks and runtime markers
- logs and observer traces
- backup snapshots
- PDF intake and processed files

The source tree contains code and authored assets only. Do not commit runtime state, personal data, logs, memories, or model weights.

### Backup

Stop the agent before copying the state directory. Back up the resolved state root, including user partitions and backup snapshots. Use the project backup tooling only when you understand which directory it targets, and do not restore over existing state without verification.

### Test isolation

Tests must not run against production or live state. Use an isolated temporary directory:

```bash
AURA_TEST_MODE=1 AURA_STATE_ROOT=/tmp/aura-test python3 <test>
```

The safe smoke and state-hardening checks in `_recovery/src/tests/` create their own temporary sandboxes.

---

## Project Status & Roadmap

### Current status

- The runnable implementation is under `_recovery/src/` and contains 78 Python modules.
- Modules compile and core modules import successfully in an isolated sandbox.
- Basic boot, Tkinter GUI, Linux launch scripts, optional 3D visualisation, and state-path isolation are present.
- The optional local phrasing model is not bundled. Without a configured local model, template phrasing is used.

### Known gaps

- **Test coverage is incomplete.** `tests/run_all.py` lists 91 suite entries, but only 2 recovered suite files are currently present (`verify_cn0_conversation_trace.py` and `verify_m16_full_route_observability.py`). The full historical suite cannot run until the missing suites are rebuilt.
- Some documentation and character packs remain incomplete or out of date.
- Several large orchestration modules need refactoring and clearer boundaries.
- Remaining hard-coded paths and legacy state access need to be consolidated through the central state layer.
- The optional local model setup is not yet automated.

### Roadmap

1. Rebuild the missing unit and regression test suites.
2. Refactor oversized orchestration modules and document module boundaries.
3. Route all persistent I/O through `aura_state.py` and remove remaining hard-coded paths.
4. Improve Linux packaging, first-run setup, and CI coverage.
5. Expand GUI, visualisation, and optional local model integration.
6. Reconcile documentation with current runtime behaviour.

AURA is not yet production-ready. Treat the current tree as an experimental framework under active maintenance.

---

## Contributing Guidelines

Contributions are welcome. Before opening a pull request:

1. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`tests/README.md`](_recovery/src/tests/README.md).
2. Never run tests against live or production state. Use isolated temporary directories.
3. Do not commit personal data, runtime state, logs, memories, or model weights.
4. Keep changes focused and include tests where possible.
5. Describe the problem, reproduction steps, and verification performed in your pull request.

Useful contribution areas:

- rebuilding missing test suites
- setup and portability improvements
- module refactoring and boundary clarification
- GUI and visualisation improvements
- documentation corrections

For architectural rules and development constraints, see [`AGENTS.md`](AGENTS.md) and [`SYSTEM_WHITEPAPER.md`](SYSTEM_WHITEPAPER.md).

---

## License

Apache License 2.0. See [`LICENSE`](LICENSE).

Copyright 2026 Matthew (`saladsoup54-ops`) and Aura contributors.
