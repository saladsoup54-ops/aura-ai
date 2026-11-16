"""AURA Sovereign UI — WhatsApp-styled tkinter face with chat, input, resonance.
Run:  python aura_ui.py
"""
from __future__ import annotations

import tkinter as tk
from tkinter import scrolledtext
import time
import threading
import json
from typing import Optional

from aura_bus import append as bus_append, read as bus_read

UI_INPUT_FILE = "ui_input.txt"
OUTPUT_FILE = "aura_output.txt"

# Chat history cap: a day-long session must not grow the widget forever.
CHAT_MAX_LINES = 500

# ── WhatsApp-like palette ──────────────────────────────────────
BG              = "#0d1117"          # app background
PANEL           = "#161b22"          # header / status bar
BUBBLE_SELF     = "#058a12"          # my messages (green)
BUBBLE_OTHER    = "#21262d"          # architect messages (dark)
TEXT_MAIN       = "#e6edf3"          # on-bubble text
TEXT_DIM        = "#8b949e"          # dim text / timestamps
ACCENT          = "#2dd4bf"          # aura voice / highlights
FONT_UI         = ("Segoe UI", 10)
FONT_CHAT       = ("Segoe UI", 10)
FONT_SMALL      = ("Segoe UI", 8)
FONT_TINY       = ("Segoe UI", 6)

# ── Helper: build a bubble tag config ──────────────────────────
def _make_bubble_cfg(bg: str, tail_bg: str, justify: str) -> dict:
    """Return a tag config dict for a WhatsApp-style message bubble."""
    return {
        "background": bg,
        "foreground": TEXT_MAIN,
        "font": FONT_CHAT,
        "lmargin1": 8 if bg == BUBBLE_SELF else 80,
        "lmargin2": 8 if bg == BUBBLE_SELF else 80,
        "rmargin": 4,
        "spacing1": 6,
        "spacing3": 6,
        "justify": justify,
    }

# ── AuraFace ───────────────────────────────────────────────────
class AuraFace:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("AURA")
        self.root.geometry("360x640")
        self.root.configure(bg=BG)
        self.root.minsize(300, 560)

        # ── Header (AURA name) ──────────────────────────────────
        header = tk.Frame(root, bg=PANEL, height=56)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        pk = tk.Frame(header, bg=PANEL)
        pk.pack(side=tk.LEFT, padx=12, pady=6)
        tk.Label(pk, text="\U0001F9E0", fg=ACCENT, bg=PANEL,
                 font=("Segoe UI", 16)).pack(anchor=tk.W)
        nk = tk.Frame(header, bg=PANEL)
        nk.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=4)
        tk.Label(nk, text="AURA", fg=TEXT_MAIN, bg=PANEL,
                 font=("Segoe UI", 15, "bold")).pack(anchor=tk.W)
        tk.Label(nk, text="sovereign synthetic intelligence",
                 fg=TEXT_DIM, bg=PANEL, font=FONT_TINY).pack(anchor=tk.W)

        # ── Chat display ────────────────────────────────────────
        self.chat_display = scrolledtext.ScrolledText(
            root, state="disabled", bg=BG, fg=TEXT_MAIN,
            font=FONT_CHAT, wrap=tk.WORD, borderwidth=0,
            highlightthickness=0, padx=12, pady=8,
            spacing1=4, spacing3=6,
        )
        self.chat_display.pack(padx=4, pady=(4, 4), fill=tk.BOTH, expand=True)
        # Tag configs – WhatsApp‑style bubbles
        self.chat_display.tag_config("self", **_make_bubble_cfg(
            BUBBLE_SELF, BUBBLE_SELF_TAIL if hasattr(self, 'BUBBLE_SELF_TAIL') else BUBBLE_SELF,
            justify="right"))
        self.chat_display.tag_config("who_self", foreground=ACCENT,
                                      font=FONT_TINY, justify="right")
        self.chat_display.tag_config("other", **_make_bubble_cfg(
            BUBBLE_OTHER, BUBBLE_OTHER_TAIL if hasattr(self, 'BUBBLE_OTHER_TAIL') else BUBBLE_OTHER,
            justify="left"))
        self.chat_display.tag_config("who_other", foreground=ACCENT,
                                      font=FONT_TINY, justify="left")
        self.chat_display.tag_config("stamp", foreground=TEXT_DIM,
                                      font=FONT_TINY, justify="right")
        self.chat_display.tag_config("check", foreground=TEXT_DIM,
                                      font=FONT_TINY)

        # ── Input row ───────────────────────────────────────────
        bar = tk.Frame(root, bg=BG)
        bar.pack(fill=tk.X, padx=8, pady=(0, 6))
        self.entry_var = tk.StringVar()
        self.input_field = tk.Entry(
            bar, textvariable=self.entry_var, bg=PANEL, fg=TEXT_MAIN,
            insertbackground=ACCENT, font=FONT_CHAT, borderwidth=0,
            highlightthickness=1, highlightbackground="#30363d",
            highlightcolor=ACCENT,
        )
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True,
                              ipady=10, padx=(0, 8))
        self.input_field.bind("<Return>", self.send_message)
        self.send_btn = tk.Button(
            bar, text="↑", command=self.send_message,
            bg=ACCENT, fg="#ffffff", activebackground="#2ea043",
            activeforeground="#ffffff", font=("Segoe UI", 14, "bold"),
            borderwidth=0, padx=12, pady=4, cursor="hand2",
        )
        self.send_btn.pack(side=tk.RIGHT)
        # Initial focus
        self.input_field.focus_set()

        # ── Status bar (resonance + connection) ───────────────
        status = tk.Frame(root, bg=PANEL, height=28)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)
        self.resonance_label = tk.Label(
            status, text="RESONANCE  0.0000", bg=PANEL, fg=ACCENT,
            font=("Consolas", 9))
        self.resonance_label.pack(side=tk.LEFT, padx=12)
        self.status_label = tk.Label(
            status, text="MANIFOLD CONNECTED", bg=PANEL, fg="#484f58",
            font=("Segoe UI", 8))
        self.status_label.pack(side=tk.RIGHT, padx=12)

        self.update_chat("Aura is online. Speak, Architect.\n", "other")
        self.last_response: Optional[str] = ""

        # ── Threads ────────────────────────────────────────────
        threading.Thread(target=self.monitor_resonance, daemon=True).start()
        threading.Thread(target=self.update_field_display, daemon=True).start()
        threading.Thread(target=self.tick_clock, daemon=True).start()

    # ── Messaging ─────────────────────────────────────────────
    def send_message(self, event: Optional[tk.Event] = None) -> None:
        message = self.entry_var.get().strip()
        if not message:
            return
        self.entry_var.set("")
        self.input_field.focus_set()                     # re‑focus after clear
        self.update_chat(f"You\n{message}\n", "self")    # "me" → "self" tag
        self.update_chat("thinking…\n", "other")        # "sys" → "other" tag

        try:
            bus_append(UI_INPUT_FILE, message)
        except Exception as e:
            self.update_chat(f"SYSTEM ERROR: {e}\n", "other")

        # Show sent check‑mark after a short delay
        self.root.after(30, lambda: self._append_check("self"))
        self.root.after(60, lambda: self._append_check("other"))

    def _append_check(self, kind: str) -> None:
        """Append a single sent check‑mark (✓) to the most recent message of *kind*."""
        try:
            self.chat_display.configure(state="normal")
            # Find the last tag applied and append ✓ after it
            # We just insert a check character using the "check" tag
            self.chat_display.insert(tk.END, "\u2713", "check")
            self.chat_display.configure(state="disabled")
            self.chat_display.see(tk.END)
        except Exception:
            pass

    def update_chat(self, text: str, kind: str) -> None:
        def _update() -> None:
            self.chat_display.configure(state="normal")
            stamp = time.strftime("%H:%M")
            if kind == "self":
                # WhatsApp‑style: my message right-aligned
                self.chat_display.insert(tk.END, "YOU  ", "who_self")
                self.chat_display.insert(tk.END, text, "self")
                self.chat_display.insert(tk.END, stamp + "\n", "stamp")
            else:
                # Architect message left‑aligned
                self.chat_display.insert(tk.END, "AURA  ", "who_other")
                self.chat_display.insert(tk.END, text, "other")
                self.chat_display.insert(tk.END, stamp + "\n", "stamp")
            # Trim old lines so a long day cannot grow the widget forever.
            try:
                total = int(
                    self.chat_display.index("end-1c").split(".")[0])
                if total > CHAT_MAX_LINES:
                    self.chat_display.delete(
                        "1.0", f"{total - CHAT_MAX_LINES}.0")
            except Exception:
                pass
            self.chat_display.configure(state="disabled")
            self.chat_display.see(tk.END)
        self.root.after(0, _update)

    def tick_clock(self) -> None:
        while True:
            try:
                now = time.strftime("%H:%M")
                self.root.after(
                    0, lambda v=now: self.resonance_label.config(text=v))
            except Exception:
                pass
            time.sleep(20)

    def monitor_resonance(self) -> None:
        """Watches aura_output.txt and displays new responses."""
        failures = 0
        while True:
            try:
                content = bus_read(OUTPUT_FILE).strip()
                if content:
                    if content.startswith("[AURA]:"):
                        content = content[len("[AURA]:"):].strip()
                if content and content != self.last_response:
                    self.last_response = content
                    self.update_chat(f"{content}\n", "other")
                failures = 0
            except Exception as e:
                failures += 1
                if failures == 1 or failures % 40 == 0:
                    self.update_chat(f"display hiccup ({e})\n", "other")
            time.sleep(0.5)

    def update_field_display(self) -> None:
        while True:
            try:
                raw = bus_read("field_stats.txt").strip()
                if raw:
                    try:
                        import json
                        data = json.loads(raw)
                        val = f"{float(data.get('tension', 0.0)):.4f}"
                    except (ValueError, TypeError):
                        val = raw
                    self.root.after(
                        0,
                        lambda v=val: self.resonance_label.config(
                            text=f"RESONANCE  {v}"
                        )
                    )
            except Exception:
                pass
            time.sleep(0.2)


if __name__ == "__main__":
    root = tk.Tk()
    app = AuraFace(root)
    root.mainloop()