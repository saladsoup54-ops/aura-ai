#!/usr/bin/env python3
"""Reconstruct tests/ support files from the 24 Sept session JSON (read-only source)."""
import json, glob, os, re, sys

ROOT = "/home/matty/Desktop/Aura AI"
SRC = glob.glob(os.path.join(ROOT, "*2026-09-24t09-55-45*.json"))[0]
OUT = os.path.join(ROOT, "_recovery", "src", "tests")
os.makedirs(OUT, exist_ok=True)

session = json.load(open(SRC, encoding="utf-8"))

def events_for(basename):
    ev = []
    for mi, m in enumerate(session["messages"]):
        for pi, part in enumerate(m.get("parts", [])):
            if part.get("type") != "tool":
                continue
            inp = (part.get("state") or {}).get("input") or {}
            fp = (inp.get("filePath") or "").replace("\\", "/")
            if not fp.endswith("tests/" + basename):
                continue
            ev.append((mi, pi, part.get("tool"), inp,
                       str((part.get("state") or {}).get("output") or "")))
    return ev

PREFIX = re.compile(r"^\s*\d+: ?")

def strip_prefixes(text):
    if "<content>\n" in text:
        text = text.split("<content>\n", 1)[1]
    if "</content>" in text:
        text = text.rsplit("</content>", 1)[0]
    text = re.sub(r"\n\(End of file - total \d+ lines\)\n$", "\n", text)
    out = [PREFIX.sub("", line, count=1) for line in text.split("\n")]
    return "\n".join(out)

def build(basename, base="read"):
    ev = events_for(basename)
    text, log = None, []
    for mi, pi, tool, inp, out in ev:
        if tool == "write":
            text = inp.get("content", "")
            log.append(f"  write @msg{mi}: {len(text)}B")
        elif tool == "read" and inp.get("offset") in (None, 0) and not inp.get("limit"):
            text = strip_prefixes(out)
            log.append(f"  read  @msg{mi}: {len(text)}B (full snapshot)")
        elif tool == "edit" and text is not None:
            old, new = inp.get("oldString", ""), inp.get("newString", "")
            if old and old in text:
                text = text.replace(old, new, -1 if inp.get("replaceAll") else 1)
                log.append(f"  edit  @msg{mi}: OK")
            else:
                log.append(f"  edit  @msg{mi}: *** oldString NOT FOUND ***")
    return text, log

targets = ["run_all.py", "README.md", "_sandbox_guard.py",
           "verify_cn0_conversation_trace.py",
           "verify_m16_full_route_observability.py"]

for name in targets:
    text, log = build(name)
    print(f"\n{name}:")
    print("\n".join(log) if log else "  (no events)")
    if text is None:
        print("  !! nothing reconstructed"); continue
    path = os.path.join(OUT, name)
    open(path, "w", encoding="utf-8", newline="").write(text)
    print(f"  -> {len(text)}B, {len(text.splitlines())} lines")
    if name.endswith(".py"):
        try:
            compile(text, name, "exec"); print("  compile: OK")
        except SyntaxError as e:
            print(f"  compile: FAIL {e.msg} line {e.lineno}")
