import os
import time

from aura_constants import VAULT_FILE, CORTEX_PATH
from aura_state import resolve_state_path as _sp


class FileTail:
    """
    Phase 0.7: tracks a per-file read offset and resets to 0 whenever the
    file shrinks (the Dream State truncates processed_cortex.txt every
    30 s — the old logic kept a stale offset and silently skipped new
    thoughts until the file outgrew its previous size).
    """
    def __init__(self, skip_existing=False):
        self.offset = 0
        self.skip_existing = skip_existing
        self.started = False

    def new_content(self, path):
        try:
            if not os.path.exists(path):
                return ""
            size = os.path.getsize(path)
            if self.skip_existing and not self.started:
                # Skip the historical backlog on first poll (e.g. the
                # vault's thousands of pre-boot records).
                self.started = True
                self.offset = size
                return ""
            if size < self.offset:
                self.offset = 0   # file was flushed/truncated — start over
            # Bytes, not text: text-mode newline translation (\r\n on
            # Windows) makes character offsets drift from getsize bytes,
            # so tail polls re-read (or skip) one char per line ending.
            with open(path, "rb") as f:
                f.seek(self.offset)
                raw = f.read()
            data = raw.decode("utf-8", errors="ignore").replace("\r\n", "\n")
            # Advance by bytes actually read, not by the earlier size:
            # an append landing between getsize and read used to make
            # the tail re-speak (or skip) on the next poll.
            self.offset += len(raw)
            return data
        except Exception:
            return ""


def run_vocal_manifest():
    print("--- AURA: VOCAL MANIFEST ACTIVE ---")
    print("Waiting for manifold resonance...")

    vault_tail  = FileTail(skip_existing=True)
    # skip_existing: never re-vocalise the previous session's cortex
    # backlog at boot — only judgements made while this session lives
    # are spoken.
    cortex_tail = FileTail(skip_existing=True)

    while True:
        # BRAIN FREEZE: Sleep while Aura is processing Matty's command
        if os.path.exists(_sp("aura_is_thinking.lock")):
            time.sleep(0.5)
            continue

        # --- 1. SCANNING THE VAULT (Hearing new data) ---
        new_data = vault_tail.new_content(VAULT_FILE)
        for line in new_data.split('\n'):
            # SAFELY filter and extract to prevent crashes
            if "ANCHOR:" in line and "DATA:" in line:
                concept = line.split("ANCHOR:")[1].split("|")[0].strip()
                print(f"\n[AURA_LEARNING]: Absorbing concept -> {concept}")

        # --- 2. SCANNING THE CORTEX (Speaking her thoughts) ---
        new_cortex = cortex_tail.new_content(CORTEX_PATH)
        for line in new_cortex.split('\n'):
            if "JUDGEMENT:" in line:
                # She vocalizes her state of mind
                print(f"\n[AURA_INNER_VOICE]: {line.strip()}")

        time.sleep(1.0)  # Polling rate


if __name__ == "__main__":
    run_vocal_manifest()
