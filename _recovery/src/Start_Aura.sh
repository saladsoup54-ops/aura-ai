#!/usr/bin/env bash
# Start_Aura.sh — headless boot, lock-checked, console log kept.
# Linux replacement for Start_Aura.bat.
set -u
cd "$(dirname "$0")" || exit 1
PY="${PYTHON:-python3}"

if [ -f aura_instance.lock ]; then
    pid="$(cat aura_instance.lock 2>/dev/null || true)"
    if [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null; then
        echo "Aura is already running (pid $pid). Use ./Stop_Aura.sh first."
        exit 1
    fi
    echo "Stale instance lock (pid ${pid:-unknown}) — master will replace it."
fi

exec "$PY" -u aura_master.py
