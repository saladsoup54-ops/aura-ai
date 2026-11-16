#!/usr/bin/env bash
# Stop_Aura.sh — stop the organism holding the instance lock.
# Linux replacement for Stop_Aura.bat.
set -u
cd "$(dirname "$0")" || exit 1

if [ ! -f aura_instance.lock ]; then
    echo "No instance lock — nothing to stop."
    exit 0
fi

pid="$(cat aura_instance.lock 2>/dev/null || true)"
if [ -z "${pid:-}" ]; then
    echo "Unreadable lock; removing it."
    rm -f aura_instance.lock
    exit 0
fi

if ! kill -0 "$pid" 2>/dev/null; then
    echo "Process $pid is not running; removing stale lock."
    rm -f aura_instance.lock
    exit 0
fi

echo "Stopping Aura (pid $pid)..."
kill "$pid" 2>/dev/null
for _ in $(seq 1 40); do
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.25
done
if kill -0 "$pid" 2>/dev/null; then
    echo "Still alive after 10s — sending SIGKILL."
    kill -9 "$pid" 2>/dev/null
fi
rm -f aura_instance.lock aura_is_thinking.lock
echo "Stopped."
