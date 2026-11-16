#!/usr/bin/env bash
# Launch_Aura.sh — core + UI in one session (optional 3D view).
# Linux replacement for Launch_Aura.bat.
#
#   ./Launch_Aura.sh            core + Tk UI
#   ./Launch_Aura.sh --view     core + Tk UI + synapse view
#   ./Launch_Aura.sh --headless core only (same as Start_Aura.sh)
set -u
cd "$(dirname "$0")" || exit 1
PY="${PYTHON:-python3}"

if [ -f aura_instance.lock ]; then
    pid="$(cat aura_instance.lock 2>/dev/null || true)"
    if [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null; then
        echo "Aura is already running (pid $pid)."
        exit 1
    fi
fi

if [ "${1:-}" = "--headless" ]; then
    exec ./Start_Aura.sh
fi

"$PY" -u aura_master.py &
core=$!
trap 'kill "$core" 2>/dev/null' EXIT INT TERM

# Give the bridge time to build the ego before the UI starts talking.
sleep 2

if [ "${1:-}" = "--view" ]; then
    "$PY" aura_synapse_view.py &
    view=$!
else
    view=""
fi

"$PY" aura_ui.py
[ -n "$view" ] && kill "$view" 2>/dev/null
