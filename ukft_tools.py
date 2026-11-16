# ukft_tools.py — AURA Tool Registry & Permissioned Action (V5 I2)
# ==================================================
# Hands in the machine, with permission.  Named tools map to
# PowerShell; each carries a permission level:
#
#   safe    — executes immediately (read-only statuses, opening apps)
#   confirm — requires the Architect's "confirm" before anything runs
#
# The motor cortex still executes the queued EXECUTE lines; this module
# decides WHAT may be queued and records every action to action_log.txt
# and her episodic memory.
# ==================================================

import os
import re
import time

from aura_bus import append as bus_append, read as bus_read, write as bus_write
from aura_constants import ACTION_LOG, PENDING_ACTION, THOUGHTS_FILE

# name -> (permission, description, powershell template with {arg})
TOOLS = {
    "system status": ("safe",
                      "a summary of this machine",
                      "Get-ComputerInfo | Select-Object CsName,CsManufacturer,"
                      "CsModel,OsName | Format-List"),
    "disk space": ("safe",
                   "how full the drives are",
                   "Get-PSDrive -PSProvider FileSystem | "
                   "Select-Object Name,Used,Free | Format-Table -AutoSize"),
    "running processes": ("safe",
                          "the busiest processes",
                          "Get-Process | Sort-Object CPU -Descending | "
                          "Select-Object -First 5 Name,CPU,Id | Format-Table -AutoSize"),
    "current time": ("safe",
                     "the current time",
                     "Get-Date"),
    "list files": ("safe",
                   "files in a folder",
                   "Get-ChildItem '{arg}' | Select-Object -First 20 Name | Format-Table -AutoSize"),
    "open": ("safe",
             "open an application",
             "Start-Process '{arg}'"),
    "run script": ("confirm",
                   "run a PowerShell script",
                   "& '{arg}'"),
}

CONFIRM_WORDS = ("confirm", "yes do it", "go ahead", "proceed", "do it")
CANCEL_WORDS = ("cancel", "abort", "never mind", "stop")

# A parked action goes stale: the Architect's "confirm" belongs to
# the conversational moment, not to next week.  Confirmation
# after this long is refused and the slot cleared (audited).
PENDING_TTL_SECONDS = 3600.0


def _strip_request_words(arg):
    """Leading polite/request words are not tool arguments."""
    arg = (arg or "").strip().strip(":.,")
    while True:
        stripped = re.sub(r"^(?:please|pls|run|the|a|an|show|me|my)\b\s*",
                          "", arg, count=1)
        if stripped == arg:
            return arg
        arg = stripped


def _safe_arg(arg):
    """
    Neutralize PowerShell quote-breakout AND line smuggling.  Tool
    templates interpolate the argument inside single quotes, so a raw
    `'` would end the string and run attacker text ("x'; Remove-Item
    ~ -Recurse -Force; '") — doubling quotes is PowerShell's own
    escaping, keeping the payload literal.  Newlines are flattened to
    spaces first: the motor runs every EXECUTE: line it sees, so an
    embedded newline could smuggle a second command past the template.
    Statement separators and shell escapes (semicolons, pipes, dollar,
    backtick, braces, ampersand, carriage returns) are stripped outright
    — app names never need them, and the motor gate re-checks everything
    anyway.  Empty args keep the old "." default.
    """
    cleaned = "".join(c for c in (arg or ".") if c not in ";\r\n|$`{}&")
    flat = " ".join(cleaned.split()) or "."
    return flat.replace("'", "''")


class ToolDirector:
    """Match a query to a tool, enforce permissions, queue actions."""

    def __init__(self, tools=None, thoughts_path=THOUGHTS_FILE,
                 pending_path=PENDING_ACTION, action_log=ACTION_LOG):
        self.tools = tools or TOOLS
        self.thoughts_path = thoughts_path
        self.pending_path = pending_path
        self.action_log = action_log

    # ── MATCHING ─────────────────────────────────────────────────
    def match(self, query):
        """
        Return (tool, arg) for an actionable query, or None.  Multi-word
        tool names are unambiguous; "run <tool>" and "open <app>" are
        explicit forms.  Returns None for ordinary questions.
        """
        q = (query or "").strip().lower()
        if not q:
            return None
        if q.startswith("open ") and q[len("open "):].strip():
            rest = q[len("open "):].strip()
            # "open" launches a process: never a path, a quote, or a
            # second line — those are command shapes, not app names.
            # ("open questions are hard" still matches and safely errors
            # at the motor; this blocks the dangerous shapes here.)
            if re.search(r"[\\/\'\"\r\n]", rest):
                return None
            return "open", rest
        if q.startswith("run script ") and q[len("run script "):].strip():
            return "run script", q[len("run script "):].strip()
        for name in sorted(self.tools, key=len, reverse=True):
            # Whole words AND terse: tool invocations are short
            # ("run disk space"); chat that merely mentions a tool name
            # in a long sentence is answered, not executed.
            if len(name.split()) >= 2 and len(q.split()) <= 6 and re.search(
                    r"\b" + r"\s+".join(map(re.escape, name.split())) + r"\b",
                    q):
                arg = _strip_request_words(
                    re.sub(r"\b" + r"\s+".join(map(re.escape, name.split()))
                           + r"\b", " ", q, count=1))
                return name, arg
        if q.startswith("run ") and q[len("run "):].strip():
            rest = q[len("run "):].strip()
            for name in sorted(self.tools, key=len, reverse=True):
                if rest == name or rest.startswith(name):
                    arg = _strip_request_words(rest.replace(name, "", 1))
                    return name, arg
        return None

    def permission(self, tool):
        return self.tools.get(tool, ("confirm",))[0]

    # ── EXECUTION PATH ───────────────────────────────────────────
    def _log(self, tool, arg, outcome):
        bus_append(self.action_log,
                   f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {tool} | "
                   f"ARG: {arg or '-'} | {outcome}")
        try:
            from ukft_episodic import EpisodicMemory
            EpisodicMemory().record(
                "tool", f"{tool} {arg or ''} — {outcome}".strip(),
                concepts=[tool.split()[0]],
            )
        except Exception:
            pass

    def queue(self, tool, arg):
        """Queue a safe tool's PowerShell to the motor cortex."""
        command = self.tools[tool][2].format(arg=_safe_arg(arg))
        bus_append(self.thoughts_path, f"EXECUTE: {command}")
        self._log(tool, arg, "EXECUTED")
        return command

    def request(self, tool, arg):
        """A confirm-required action: park it and ask the Architect."""
        existing = self.pending()
        if existing:
            # One parked slot: a second request must not silently
            # discard the first.  Refuse loudly instead.
            old_tool, old_arg = existing
            self._log(tool, arg,
                      f"REFUSED (already parked: {old_tool} {old_arg})")
            return (f"You still have '{old_tool} {old_arg}' waiting — say "
                    f"'confirm' to run it or 'cancel' to drop it before "
                    f"parking anything new.")
        bus_write(self.pending_path,
                  f"PENDING: {tool} | ARG: {arg} | TS: {time.time():.0f}")
        self._log(tool, arg, "CONFIRM REQUESTED")
        return f"'{tool}' {arg} requires your confirmation. " \
               f"Say 'confirm' to run it or 'cancel' to abort."

    def pending(self):
        """Return (tool, arg) of the parked action, or None."""
        raw = bus_read(self.pending_path).strip()
        if not raw.startswith("PENDING: "):
            return None
        # Parse from the outside in: the ARG may itself contain " | ",
        # so split the TS tail off the right and the tool off the left.
        body = raw[len("PENDING: "):]
        ts = 0.0
        if " | TS: " in body:
            body, _, tail = body.rpartition(" | TS: ")
            try:
                ts = float(tail.strip().split()[0])
            except (ValueError, IndexError):
                ts = 0.0
        if ts and time.time() - ts > PENDING_TTL_SECONDS:
            # Stale park (even across reboots): clear it and refuse
            # to run ancient orders on a fresh "confirm".
            bus_write(self.pending_path, "")
            self._log("(stale parked action)", "", "EXPIRED")
            return None
        if " | ARG: " in body:
            tool, arg = body.split(" | ARG: ", 1)
        else:
            tool, arg = body, ""
        tool, arg = tool.strip(), arg.strip()
        return (tool, arg) if tool else None

    def confirm(self):
        """Run the parked action.  Returns a response line or None."""
        parked = self.pending()
        if not parked:
            return None
        tool, arg = parked
        if tool not in self.tools:
            # Tampered or stale parking slot: drop it, run nothing.
            # (Blindly queueing KeyErrors the caller otherwise.)
            bus_write(self.pending_path, "")
            self._log(tool, arg, "DROPPED (unknown tool)")
            return ("That parked action is no longer valid — "
                    "dropped it, ran nothing.")
        bus_write(self.pending_path, "")
        self.queue(tool, arg)
        return f"Confirmed. Executing {tool}."

    def cancel(self):
        parked = self.pending()
        if not parked:
            return None
        bus_write(self.pending_path, "")
        self._log(parked[0], parked[1], "CANCELLED")
        return "Aborted. Nothing was run."


def run_tools_demo():
    director = ToolDirector()
    print("--- AURA TOOL REGISTRY ---")
    for name, (perm, desc, _cmd) in sorted(TOOLS.items()):
        print(f"  [{perm:7}] {name:20} — {desc}")
