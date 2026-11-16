#!/usr/bin/env bash
# Boot_Aura.sh — console boot (foreground).
# Linux replacement for Boot_Aura.bat.
set -u
cd "$(dirname "$0")" || exit 1
exec ./Start_Aura.sh
