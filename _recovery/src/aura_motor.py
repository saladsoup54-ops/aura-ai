import os
import re
import subprocess
import time

from aura_bus import (drain as bus_drain, append as bus_append,
                        write as bus_write)

# ── FILE PATHS ────────────────────────────────────────────────────
# aura_master writes the command here after stripping it from the response
THOUGHT_PATH  = "aura_thoughts.txt"

# The UI watches this file for new content to display
OUTPUT_FILE   = "aura_output.txt"

# Feed command results back into the brain so Aura "saw" what happened
SENSORY_PATH  = "sensory_buffer.txt"

# ── SETTINGS ──────────────────────────────────────────────────────
# How long (seconds) to wait before killing a PowerShell command.
# Increase this if you run commands that take a long time to complete.
COMMAND_TIMEOUT = 60

# Maximum output characters captured per command (prevents flooding).
# Set to None to capture everything.
MAX_OUTPUT_CHARS = 8000

# ── EXECUTION POLICY ─────────────────────────────────────────────
# The motor used to run ANY text found in the thought file.  Now every
# command must pass the gate: its head verb comes from the read-only
# diagnostic set the organism actually uses (sweep + tool templates),
# and no destructive/download/eval token may appear anywhere in it.
# Anything else is refused loudly and never executed.
ALLOWED_COMMAND_HEADS = (
    "get-", "select-object", "sort-object", "where-object",
    "measure-object", "format-list", "format-table", "get-date",
    "get-counter", "get-wmiobject", "get-service", "get-childitem",
    "get-process", "get-computerinfo", "get-psdrive", "start-process",
)
DENIED_COMMAND_TOKENS = (
    "remove-item", "stop-process", "stop-service", "restart-computer",
    "stop-computer", "invoke-expression", "invoke-webrequest",
    "invoke-restmethod", "start-bitstransfer", "format-volume",
    "uninstall-", "regedit", "schtasks",
)


def _tokens(text):
    return re.findall(r"[a-z0-9-]+", (text or "").lower())


def command_allowed(command):
    """True only when the command passes the execution policy."""
    s = (command or "").strip()
    if not s:
        return False
    # Statement separators and shell escapes never survive the gate:
    # ";" chains statements, "$" subshells/expands, "`" escapes, "{}"
    # script-blocks.  (Pipes stay: every sweep/template command is a
    # read-only pipeline — but each pipeline SEGMENT below must pass
    # the verb check alone, so "Get-Date | ForEach-Object {evil}" dies
    # on its second segment.  Bare parentheses stay for the fixed
    # Get-Counter sweep path; nothing executable hides in them once
    # "$", "`", ";" and "{}" are gone and every segment is gated.)
    if re.search(r"[;`$}{]", s):
        return False
    # A "& 'path'" script launch: "&" is not alphanumeric, so the head
    # check runs on the raw string.  Scripts must be single-quoted *.ps1
    # paths and nothing else — "& calc.exe" or "& Do-Thing" never passes
    # (confirm-gated upstream in tools, on top of this shape check).
    if s.startswith("&"):
        rest = s[1:].strip()
        if not (len(rest) >= 8 and rest.startswith("'")
                and rest.endswith("'")
                and rest[1:-1].lower().endswith(".ps1")):
            return False
        toks = _tokens(s[1:])
    else:
        if re.search(r"[|&]", s):
            # Pipelines: every segment earns its own verbs.
            for seg in re.split(r"\|", s):
                seg = seg.strip()
                if not seg:
                    return False
                if seg.startswith("&"):
                    return False
                toks = _tokens(seg)
                head = toks[0] if toks else ""
                if not (head.startswith("get-")
                        or head in ALLOWED_COMMAND_HEADS):
                    return False
            toks = _tokens(s)
        else:
            toks = _tokens(s)
            head = toks[0] if toks else ""
            if not (head.startswith("get-")
                    or head in ALLOWED_COMMAND_HEADS):
                return False
    for tok in toks:
        if tok in DENIED_COMMAND_TOKENS:
            return False
        if tok.startswith(("set-", "new-", "add-", "clear-",
                           "remove-", "stop-", "restart-")):
            return False
    return True


def run_powershell(command: str) -> str:
    """
    Execute a single PowerShell command and return its output as a string.
    Only ever called with commands passing command_allowed() — never feed
    it raw text.
    """
    try:
        argv = (["/bin/sh", "-c", command] if os.name == "posix"
                else ["powershell", "-NoProfile", "-NonInteractive",
                      "-Command", command])
        result = subprocess.check_output(
            argv,
            text=True,
            stderr=subprocess.STDOUT,
            timeout=COMMAND_TIMEOUT
        ).strip()

        if not result:
            return "(no output)"

        # Trim if result is very large
        if MAX_OUTPUT_CHARS and len(result) > MAX_OUTPUT_CHARS:
            result = result[:MAX_OUTPUT_CHARS] + f"\n... (truncated at {MAX_OUTPUT_CHARS} chars)"

        return result

    except subprocess.TimeoutExpired:
        return f"(timed out after {COMMAND_TIMEOUT}s)"
    except subprocess.CalledProcessError as e:
        raw = e.output.strip() if e.output else str(e)
        return f"(error: {raw[:300]})"
    except FileNotFoundError:
        return "(error: PowerShell not found — is it installed and on PATH?)"
    except Exception as e:
        return f"(friction: {e})"


def process_thought_file(thought_path=THOUGHT_PATH,
                         output_path=OUTPUT_FILE,
                         sensory_path=SENSORY_PATH):
    """
    One motor pass: atomically drain queued EXECUTE: lines, run the ones
    passing the execution policy, refuse the rest loudly.  Returns
    (ran, refused).  Draining under the bus lock (instead of raw
    read-then-truncate) means commands queued mid-pass survive to the
    next pass instead of being wiped unexecuted.
    """
    lines = bus_drain(thought_path)
    content = "\n".join(lines).strip()
    if "EXECUTE:" not in content:
        return 0, []

    # Collect ALL EXECUTE: lines from the thought file
    commands = []
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("EXECUTE:"):
            cmd = line[len("EXECUTE:"):].strip()
            if cmd:
                commands.append(cmd)

    if not commands:
        return 0, []

    print(f"[Motor] Running {len(commands)} command(s)...")
    all_results = []
    refused = []
    ran = 0

    for command in commands:
        if not command_allowed(command):
            refused.append(command)
            all_results.append(f">> {command}\n(refused by safety policy)")
            continue
        print(f"[Motor Action] {command}")
        result = run_powershell(command)
        all_results.append(f">> {command}\n{result}")
        ran += 1

    # Build display block
    full_output = "\n\n".join(all_results)
    display = f"[AURA STATUS REPORT]:\n{full_output}"

    bus_write(output_path, display)

    # Feed summary back into Aura's sensory buffer
    bus_append(sensory_path,
               f"SYSTEM_FEEDBACK: motor sweep complete, "
               f"{ran} command(s) executed, "
               f"{len(refused)} refused\n")

    print(f"[Motor] Report written to UI ({ran} command(s) done).")
    return ran, refused


def run_motor():
    """
    The Motor Cortex — watches aura_thoughts.txt for EXECUTE: commands,
    runs the policy-passing ones in PowerShell, and writes
    the result to aura_output.txt so the UI displays it.

    Trigger phrase:  aap2025
    Format expected in aura_thoughts.txt:
        EXECUTE: <policy-passing PowerShell command>
        EXECUTE: <another command>
        ...
    """
    print("[Motor Cortex] Standing by for neural triggers...")
    print(f"[Motor Cortex] Timeout per command: {COMMAND_TIMEOUT}s | Max output: {MAX_OUTPUT_CHARS} chars")

    while True:
        try:
            process_thought_file()
        except Exception as e:
            print(f"[Motor Error]: {e}")

        time.sleep(0.5)


if __name__ == "__main__":
    run_motor()


