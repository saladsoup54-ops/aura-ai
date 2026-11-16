# ukft_episodic.py — AURA Episodic Memory (Phase 5-C)
# ====================================================
# The memory split.  Semantic memory (the vault, temporal links, the
# trigram model) holds what she KNOWS; episodic memory holds what
# HAPPENED — conversations with the Architect, discoveries, spontaneous
# utterances, sleeps and consolidations.
#
#   episodic_memory.txt  — timestamped EPISODE records, capped at
#                          MAX_EPISODES with the oldest fading first.
#   record(kind, content, concepts) — appends one episode.
#   recent(n) / search(word)       — recall what happened.
# ====================================================

import hashlib
import os
import threading
import time

from aura_constants import EPISODIC_MEMORY, FORGOTTEN_MEMORIES

MAX_EPISODES = 500

# Process-wide lock: every event is load -> append -> save, so two
# concurrent recorders (sleep + spontaneous + bridge) without a shared
# lock load the same N episodes and the last writer silently eats the
# other's.  record() and forget_by_hash() re-read under this lock.
_LOCK = threading.RLock()


class EpisodicMemory:
    def __init__(self, path=EPISODIC_MEMORY, max_episodes=MAX_EPISODES):
        self.path         = path
        self.max_episodes = max_episodes
        self.episodes     = []   # {ts, kind, concepts, content}
        self.load()

    # ── PERSISTENCE ───────────────────────────────────────────────
    def load(self):
        if not os.path.exists(self.path):
            return
        # Idempotent: reloading replaces, never duplicates.  record()
        # re-reads under the shared lock so concurrent writers converge.
        self.episodes = []
        try:
            with open(self.path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line.startswith("EPISODE: "):
                        continue
                    try:
                        rest = line[len("EPISODE: "):].rstrip("\n")
                        ts_text, rest = rest.split(" | ", 1)
                        ts = float(ts_text)
                        fields = rest.split(" | ")
                        kind = "event"
                        concepts = []
                        content = ""
                        i = 0
                        while i < len(fields):
                            field = fields[i]
                            if field.startswith("KIND: "):
                                kind = field[len("KIND: "):]
                                i += 1
                            elif field.startswith("CONCEPTS: "):
                                concepts = field[len("CONCEPTS: "):].split()
                                i += 1
                            elif field.startswith("CONTENT: "):
                                content = field[len("CONTENT: "):]
                                if i + 1 < len(fields):
                                    content += " | " + " | ".join(fields[i + 1:])
                                break
                            else:
                                i += 1
                        self.episodes.append({
                            "ts": ts, "kind": kind,
                            "concepts": concepts, "content": content,
                        })
                    except (ValueError, IndexError):
                        continue
        except Exception:
            pass

    def save(self):
        # Atomic + locked: truncate-then-write used to shred the sole
        # episode store on a mid-save crash, and concurrent recorders
        # lost each other.  Temp-file + replace under the shared lock.
        # (Windows refuses replace while another thread holds the file
        # open for reading, so retry briefly, then fall back to a
        # direct overwrite — still race-free under _LOCK, only the
        # crash window reopens for that save.)
        from aura_state import deny_live_write
        deny_live_write(self.path)
        with _LOCK:
            try:
                tmp = self.path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    f.write(f"--- AURA EPISODIC MEMORY (v1) | EPISODES: {len(self.episodes)} ---\n")
                    for e in self.episodes:
                        f.write(
                            f"EPISODE: {int(e['ts'])} | KIND: {e['kind']} | "
                            f"CONCEPTS: {' '.join(e['concepts'])} | "
                            f"CONTENT: {e['content']}\n"
                        )
                replaced = False
                for _ in range(20):
                    try:
                        os.replace(tmp, self.path)
                        replaced = True
                        break
                    except OSError:
                        time.sleep(0.005)
                if not replaced:
                    with open(self.path, "w", encoding="utf-8") as f:
                        with open(tmp, "r", encoding="utf-8") as t:
                            f.write(t.read())
                    try:
                        os.remove(tmp)
                    except OSError:
                        pass
            except Exception:
                pass

    # ── RECORDING / RECALL ────────────────────────────────────────
    def record(self, kind, content, concepts=()):
        """Append one episode; the oldest fades when the cap is hit."""
        with _LOCK:
            self.load()
            self.episodes.append({
                "ts": time.time(), "kind": kind,
                "concepts": list(concepts), "content": content,
            })
            if len(self.episodes) > self.max_episodes:
                del self.episodes[:len(self.episodes) - self.max_episodes]
            self.save()

    def recent(self, n=10):
        if n <= 0:
            return []
        return self.episodes[-n:]

    def all(self):
        """Every episode, oldest first (Phase 5-D: decay sweeps these)."""
        return list(self.episodes)

    def count(self):
        return len(self.episodes)

    def forget_by_hash(self, key):
        """
        Phase 5-D: true forgetting.  Remove the episode whose content
        hashes to `key` and archive it to forgotten_memories.txt.
        """
        with _LOCK:
            self.load()
            for i, e in enumerate(self.episodes):
                content_hash = hashlib.md5(
                    e["content"].encode("utf-8")).hexdigest()
                if content_hash == key:
                    self.episodes.pop(i)
                    try:
                        with open(FORGOTTEN_MEMORIES, "a",
                                  encoding="utf-8") as f:
                            f.write(
                                f"FORGOT EPISODE: {int(e['ts'])} | "
                                f"KIND: {e['kind']} | CONTENT: {e['content']}\n"
                            )
                    except Exception:
                        pass
                    self.save()
                    return True
            return False

    def search(self, word, n=5):
        """Episodes mentioning `word` in their content or concepts."""
        word = word.lower()
        matches = [e for e in self.episodes
                   if word in e["content"].lower()
                   or word in [c.lower() for c in e["concepts"]]]
        return matches[-n:]
