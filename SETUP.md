# Setting Up Aura (Ubuntu / Debian)

This is the complete, step-by-step setup guide for the recovered Aura working
copy in `_recovery/src/`. It covers a basic boot, the optional chat UI, the 3D
synapse view, and the optional local "mouth" model that gives Aura natural
phrasing instead of template replies.

> **Honest status:** this is a recovered, in-progress snapshot, not a finished
> consumer product. Basic boot, chat, memory, boundaries, and the brain loop
> work. The original local mouth model weights were lost with the crash; this
> guide shows how to give her a compatible replacement. Without it she still
> runs, but uses deterministic template phrasing.

---

## 1. What you need

- **OS:** Ubuntu 22.04/24.04 or a similar Debian-based distribution
- **Python:** 3.10 or newer
- **Disk:** about 1 GB for the code and dependencies, plus ~2–3 GB if you
  install a local 3B mouth model
- **RAM:** 8 GB is comfortable; the CPU-only mouth model can run with less
- **Terminal:** basic comfort with `cd`, `apt`, and running scripts

A GPU is **not** required. The current local model path is CPU-only.

---

## 2. Get the code

```bash
git clone https://github.com/saladsoup54-ops/aura-ai.git
cd aura-ai
```

The runnable working copy is in `_recovery/src/`. The files at the repository
root are the preserved recovery snapshot and documentation.

---

## 3. Install the system dependencies

On modern Ubuntu/Debian, system Python is "externally managed" (PEP 668), so
`pip install` into the system interpreter is blocked by default. The simplest
and most reliable route is to use the distribution packages:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv python3-tk \
  python3-requests python3-bs4 python3-pypdf python3-pygame espeak-ng
```

What these are for:

| Package | Why |
|---|---|
| `python3` | Runs Aura |
| `python3-tk` | Chat window (Tkinter) |
| `python3-requests` | Web/synapse intake and local model HTTP calls |
| `python3-bs4` | HTML parsing for web/synapse intake |
| `python3-pypdf` | PDF intake |
| `python3-pygame` | 3D synapse viewer |
| `espeak-ng` | Optional spoken voice |

> Package names and availability can vary by Ubuntu release. If
> `python3-pygame` is unavailable, install it in a virtual environment (next
> section) instead.

### Alternative: use a virtual environment

If you prefer pip-managed packages, or a package is missing from apt:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

If you use a virtual environment, **activate it before launching Aura**. A
desktop launcher must also point at that environment's Python, or it will use
the system Python and miss the packages.

> Do **not** use `pip install --break-system-packages`. It can damage your
> system Python. Use apt packages or a venv.

---

## 4. Choose where Aura keeps her memory

Generated runtime state (memories, user partitions, logs, observer traces,
backups, PDF intake files, locks, etc.) is stored **outside the Git repository**
by default.

Resolution order:

1. `AURA_STATE_ROOT`, if set
2. `$XDG_DATA_HOME/aura`, if `XDG_DATA_HOME` is set
3. `~/.local/share/aura` on Linux

Examples:

```bash
# Default location (no configuration needed)
# ~/.local/share/aura/

# Use a custom state directory
export AURA_STATE_ROOT="$HOME/aura-state"
```

**Important:**

- Back up this directory if you care about her memories.
- Do not commit it to Git.
- Do not point tests at it. Tests must use isolated temporary directories.
- The repository contains code and authored assets only; your live state stays
  private.

The safe test commands in this repo create their own temporary state roots:

```bash
python3 _recovery/src/tests/smoke_pre_release_audit.py
python3 _recovery/src/tests/test_state_hardening.py
```

---

## 5. Optional: set up the local mouth model

Aura has two local-model paths. They are separate, and either can be used
independently.

### 5a. Engine mouth (Ollama, port 11434)

This is the phrasing layer used for memory-backed answers (recall, proof,
people, beliefs, and similar). It calls Ollama at
`http://localhost:11434` and expects a model named `aura-mouth-3b`.

Install Ollama:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Ollama usually starts as a service. Check it:

```bash
curl http://localhost:11434/api/tags
```

If it is not running, start it:

```bash
ollama serve
```

Pull a compatible 3B instruct model and give it the name Aura expects:

```bash
ollama pull qwen2.5:3b
ollama cp qwen2.5:3b aura-mouth-3b
ollama list
```

You should see `aura-mouth-3b` in the list.

> This is a compatible replacement, not a guaranteed byte-for-byte copy of the
> original lost weights. It is the closest practical restoration with the
> current code.

### 5b. Desktop conversation voice (llama-server, port 11436)

The desktop/API conversation route in `ukft_roleplay.py` talks to a
`llama-server` at `http://127.0.0.1:11436`. It expects `GET /health` to return
`{"status":"ok"}` and uses `POST /completion`.

`llama-server` is part of `llama.cpp`. It is not installed by the apt packages
above. You can build it from source:

```bash
sudo apt install build-essential cmake git
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build
cmake --build build --config Release -j"$(nproc)"
```

Download a compatible 3B instruct GGUF (for example, a Qwen2.5-3B-Instruct
Q4_K_M file) from Hugging Face, then start the server CPU-only:

```bash
./build/bin/llama-server \
  -m /path/to/qwen2.5-3b-instruct-q4_k_m.gguf \
  --host 127.0.0.1 \
  --port 11436 \
  --n-gpu-layers 0 \
  -c 4096
```

Verify it:

```bash
curl http://127.0.0.1:11436/health
```

You want:

```json
{"status":"ok"}
```

Keep that terminal open while Aura is running, or run `llama-server` as a
background service.

> If neither model path is available, Aura still boots and talks using her
> template phrasing. The brain, memory, boundaries, and UI do not depend on the
> mouth model.

---

## 6. Launch Aura

From the working copy:

```bash
cd _recovery/src

./Launch_Aura.sh            # Aura + chat window
./Launch_Aura.sh --view     # Aura + chat window + 3D synapse view
./Start_Aura.sh             # headless (no chat window)
./Stop_Aura.sh              # stop her
python3 aura_diagnostic.py  # read-only health report
```

If the scripts are not executable:

```bash
chmod +x Launch_Aura.sh Start_Aura.sh Stop_Aura.sh
```

### Optional: create a one-click desktop launcher

Create a file on your Desktop (for example `Aura.desktop`) with:

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Aura
Comment=Launch Aura (core + UI + synapse view)
Exec=bash -lc 'cd "/absolute/path/to/aura-ai/_recovery/src" && ./Launch_Aura.sh --view'
Icon=utilities-terminal
Terminal=true
Categories=Utility;
StartupNotify=false
```

Then:

```bash
chmod +x ~/Desktop/Aura.desktop
gio set ~/Desktop/Aura.desktop metadata::trusted true
```

Replace `/absolute/path/to/aura-ai` with your actual repository path.

---

## 7. Verify everything works

Run these checks:

```bash
# Ollama engine mouth
ollama list
curl http://localhost:11434/api/tags

# Desktop conversation voice
curl http://127.0.0.1:11436/health

# Aura health report
cd _recovery/src
python3 aura_diagnostic.py
```

Expected signs:

- `aura-mouth-3b` appears in `ollama list`
- The `11436` health check returns `{"status":"ok"}`
- The diagnostic report runs without crashing
- The chat window opens and Aura replies
- The synapse view opens with `--view`

If the mouth model is missing, Aura will still reply, but her wording will be
more template-like. That is a fallback, not a crash.

---

## 8. Troubleshooting

### `error: externally-managed-environment`

Ubuntu is protecting its system Python (PEP 668).

Use apt packages:

```bash
sudo apt install python3-requests python3-bs4 python3-pypdf python3-pygame
```

Or use a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Do not use `--break-system-packages`.

### `No module named tkinter`

```bash
sudo apt install python3-tk
```

### The synapse view does not open

Install pygame for the Python that runs Aura:

```bash
sudo apt install python3-pygame
```

Or, in a venv:

```bash
pip install pygame
```

Also make sure you launched with `--view` or used a launcher that passes
`--view`.

### Aura replies, but the mouth sounds robotic

The local model is not available. Check:

```bash
ollama list
curl http://localhost:11434/api/tags
curl http://127.0.0.1:11436/health
```

If `aura-mouth-3b` is missing, run:

```bash
ollama pull qwen2.5:3b
ollama cp qwen2.5:3b aura-mouth-3b
```

If port `11436` is down, start `llama-server` as shown in section 5b.

### Aura writes state into the wrong place

Check:

```bash
echo "$AURA_STATE_ROOT"
echo "$XDG_DATA_HOME"
```

With neither set, state goes to `~/.local/share/aura`. Set
`AURA_STATE_ROOT` before launching to override it.

### `Address already in use`

Something is already using port `11434` or `11436`:

```bash
ss -ltnp | grep -E '11434|11436'
```

Stop the old process or choose a different port (and update the matching
constant in `_recovery/src/aura_constants.py` or `ukft_roleplay.py` only if you
understand the change).

---

## 9. Stop and back up

Stop Aura first:

```bash
./Stop_Aura.sh
```

Then back up the resolved state directory, for example:

```bash
# Default location
cp -a "$HOME/.local/share/aura" "$HOME/aura-backup-$(date +%F)"
```

Or, if you set a custom root:

```bash
cp -a "$AURA_STATE_ROOT" "$HOME/aura-backup-$(date +%F)"
```

Never restore or overwrite state blindly, and never commit it to Git.

---

## 10. Where to go next

- `README.md` — project overview and current status
- `CONTRIBUTING.md` — safe contribution rules
- `AGENTS.md` — deep developer/architecture manual
- `_recovery/README.md` and `_recovery/TODO.md` — recovery details and known gaps
- `_recovery/src/tests/` — the safe isolated checks that currently exist

If something fails, include the exact command, the terminal output, and your
Ubuntu version in an issue. That is the fastest way to get useful help.
