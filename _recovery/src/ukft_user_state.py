# ukft_user_state.py — Per-user state partitions (G1)
# ==========================================================
# Each user gets their own directory under users/<user_id>/ containing
# ALL state files. The engine lobes read/write through this manager.
# Leakage-proof: no global state files are ever read/written for user data.

import os
import json
import shutil
import threading
from pathlib import Path
from typing import Dict, List, Optional, Set

from aura_constants import BACKUP_DIR

# ────────────────────────────────────────────────────────────────
# STATE FILE CATEGORIES
# ────────────────────────────────────────────────────────────────

# Core memory files (must be per-user)
USER_STATE_FILES = [
    "locked_patterns.txt",        # vault
    "identity_core.txt",          # identity
    "episodic_memory.txt",        # episodes
    "discoveries.txt",            # discoveries
    "working_memory.txt",         # conversation thread
    "ebbinghaus_traces.txt",      # forgetting curves
    "forgotten_memories.txt",     # faded episodes
    "field_state.txt",            # resting manifold
    "sleep_state.txt",            # sleep rhythm
    "parietal_links.txt",         # associations
    "emotional_core.txt",         # emotional history
    "inner_monologue.txt",        # thoughts
    "sleep_log.txt",
    "dream_log.txt",
    # Reasoning layer
    "extracted_relations.txt",
    "knowledge_graph.txt",
    "inferences.txt",
    "contradictions.txt",
    "knowledge_gaps.txt",
    "evaluation_report.txt",
    "relation_audit_sample.txt",
    "action_log.txt",
    "pending_action.txt",
    # Companion layer (V6 C-track)
    "people.txt",
    "pending_people.txt",
    "self_state.txt",
    "threads.txt",
    "beliefs.txt",
    "pending_belief.txt",
    "lessons.txt",
    # Rapport layer (G8: felt relationship ledger)
    "rapport.txt",
    # Voice layer
    "register_state.txt",
]

# Engine files (SHARED across users - read-only models, rebuilt from vault)
SHARED_ENGINE_FILES = [
    "trigram_model.txt",
    "temporal_links.txt",
]

# System files (global, not per-user)
SYSTEM_FILES = [
    "aura_instance.lock",
    "field_stats.txt",
    "field_map.json",
    "hypothalamus_signal.txt",
    "pfc_signal.txt",
    "pfc_focus.txt",
    "last_architect_input.txt",
    "internal_stimulus.txt",
    "aura_console.log",
    "aura_is_thinking.lock",
    "ui_input.txt",
    "aura_thoughts.txt",
    "aura_output.txt",
    "sensory_buffer.txt",
    "cortex_inbox.txt",
    "processed_cortex.txt",
    "short_term_memory.txt",
    "parietal_inbox.txt",
    "basal_ganglia_log.txt",
    "roleplay_debug_once.json",
]

# ────────────────────────────────────────────────────────────────
# USER STATE MANAGER
# ────────────────────────────────────────────────────────────────

class UserStateManager:
    """
    Manages per-user state directories. Each user_id gets:
      <state_root>/users/<user_id>/...
    Shared engine models and system runtime files live under the active
    state root (outside the repo by default in production).
    """
    
    def __init__(self, base_dir: str = "users"):
        from aura_state import deny_live_write, resolve_state_path
        resolved = resolve_state_path(base_dir)
        deny_live_write(resolved)
        self.base_dir = Path(resolved)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._locks: Dict[str, threading.Lock] = {}
        self._global_lock = threading.Lock()
    
    def _user_lock(self, user_id: str) -> threading.Lock:
        with self._global_lock:
            if user_id not in self._locks:
                self._locks[user_id] = threading.Lock()
            return self._locks[user_id]
    
    def user_dir(self, user_id: str) -> Path:
        """Get the user's state directory, creating if needed."""
        # Sanitize user_id for filesystem safety
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in user_id)
        return self.base_dir / safe_id
    
    def user_file(self, user_id: str, filename: str) -> Path:
        """Get the full path to a user's state file."""
        return self.user_dir(user_id) / filename
    
    def ensure_user(self, user_id: str) -> Path:
        """Create user directory and return it."""
        udir = self.user_dir(user_id)
        udir.mkdir(parents=True, exist_ok=True)
        return udir
    
    def user_exists(self, user_id: str) -> bool:
        """Check if user has any state."""
        return self.user_dir(user_id).exists()
    
    def list_users(self) -> List[str]:
        """List all user IDs with state directories."""
        return [d.name for d in self.base_dir.iterdir() if d.is_dir()]
    
    # ─── File operations with locking ──────────────────────────
    
    def read_user_file(self, user_id: str, filename: str, default: str = "") -> str:
        """Read a user's state file (thread-safe)."""
        path = self.user_file(user_id, filename)
        lock = self._user_lock(user_id)
        with lock:
            if not path.exists():
                return default
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except OSError:
                return default
    
    def write_user_file(self, user_id: str, filename: str, content: str) -> bool:
        """Write a user's state file atomically (thread-safe)."""
        path = self.user_file(user_id, filename)
        lock = self._user_lock(user_id)
        with lock:
            try:
                from aura_state import deny_live_write
                deny_live_write(path)
                self.ensure_user(user_id)
                tmp = path.with_suffix(path.suffix + ".tmp")
                with open(tmp, "w", encoding="utf-8") as f:
                    f.write(content)
                tmp.replace(path)
                return True
            except OSError:
                return False
    
    def append_user_file(self, user_id: str, filename: str, line: str) -> bool:
        """Append a line to a user's state file (thread-safe)."""
        path = self.user_file(user_id, filename)
        lock = self._user_lock(user_id)
        with lock:
            try:
                from aura_state import deny_live_write
                deny_live_write(path)
                self.ensure_user(user_id)
                with open(path, "a", encoding="utf-8") as f:
                    f.write(line + ("\n" if not line.endswith("\n") else ""))
                return True
            except OSError:
                return False
    
    def user_file_exists(self, user_id: str, filename: str) -> bool:
        """Check if a user's state file exists."""
        return self.user_file(user_id, filename).exists()
    
    def user_file_size(self, user_id: str, filename: str) -> int:
        """Get size of user's state file."""
        path = self.user_file(user_id, filename)
        try:
            return path.stat().st_size
        except OSError:
            return 0
    
    # ─── State migration / initialization ──────────────────────
    
    def migrate_from_global(self, user_id: str) -> Dict[str, int]:
        """
        One-time migration: move global state files (in active state root)
        into user's partition. Returns dict of {filename: bytes_moved}.
        Does not auto-run at startup; explicit operation only.
        """
        from aura_state import resolve_state_path, deny_live_write
        moved = {}
        udir = self.ensure_user(user_id)
        for fname in USER_STATE_FILES:
            src = Path(resolve_state_path(fname))
            if src.exists() and src.stat().st_size > 0:
                dst = udir / fname
                if not dst.exists():
                    try:
                        deny_live_write(src)
                        deny_live_write(dst)
                        shutil.move(str(src), str(dst))
                        try:
                            moved[fname] = dst.stat().st_size
                        except OSError:
                            moved[fname] = 0
                    except OSError:
                        pass
        return moved
    
    def seed_new_user(self, user_id: str, personality: str = "nerdy",
                      interests: List[str] = None, name: str = "Aura",
                      seed_lines=None) -> bool:
        """
        Initialize a fresh user with personality seed.
        Creates founding identity + vault seed from character pack.
        """
        udir = self.ensure_user(user_id)
        
        # Founding identity seed
        identity_content = self._build_identity_seed(personality, interests or [], name)
        (udir / "identity_core.txt").write_text(identity_content, encoding="utf-8")
        
        # Vault seed (personality facts + interests as given-not-lived)
        vault_content = self._build_vault_seed(personality, interests or [], name)
        for line in seed_lines or []:
            if str(line).strip():
                vault_content += str(line).rstrip("\n") + "\n"
        (udir / "locked_patterns.txt").write_text(vault_content, encoding="utf-8")
        
        # Empty companion files
        for fname in ["people.txt", "pending_people.txt", "threads.txt",
                      "beliefs.txt", "pending_belief.txt", "lessons.txt",
                      "working_memory.txt", "episodic_memory.txt"]:
            (udir / fname).write_text("", encoding="utf-8")

        # Rapport seed: a stranger with no history (G8).
        try:
            from ukft_rapport import Rapport
            Rapport(path=str(udir / "rapport.txt")).save()
        except Exception:
            (udir / "rapport.txt").write_text("", encoding="utf-8")
        
        # Sleep state (awake)
        (udir / "sleep_state.txt").write_text("AWAKE\n0\n", encoding="utf-8")
        
        return True
    
    def _build_identity_seed(self, personality: str, interests: List[str], name: str) -> str:
        """Build founding identity_core.txt from personality preset.

        Format MUST stay engine-native (`CORE: <word> <strength>` —
        ukft_identity.load only reads those lines; anything else is
        an unreadable file and reinforcement silently no-ops). The
        founding set is always present (torn-read guard); her name,
        drives and boundaries live in profile.json, not here.
        """
        # Personality presets map to drive weights and core concepts
        presets = {
            "nerdy": {
                "drives": {"epistemic": 0.5, "homeostatic": 0.15, "social": 0.2, "project": 0.15},
                "core": ["curiosity", "books", "chess", "precision", "depth"],
            },
            "shy": {
                "drives": {"homeostatic": 0.4, "social": 0.15, "epistemic": 0.25, "project": 0.2},
                "core": ["reserve", "gentle", "observant", "loyal", "depth"],
            },
            "bossy": {
                "drives": {"project": 0.45, "homeostatic": 0.15, "epistemic": 0.2, "social": 0.2},
                "core": ["command", "structure", "standards", "drive", "clarity"],
            },
            "flirty": {
                "drives": {"social": 0.5, "epistemic": 0.2, "homeostatic": 0.15, "project": 0.15},
                "core": ["playful", "charming", "expressive", "warm", "attuned"],
            },
            "bold": {
                "drives": {"project": 0.35, "social": 0.3, "epistemic": 0.2, "homeostatic": 0.15},
                "core": ["direct", "fearless", "initiative", "authentic", "strong"],
            },
            "gentle": {
                "drives": {"homeostatic": 0.35, "social": 0.35, "epistemic": 0.15, "project": 0.15},
                "core": ["kind", "patient", "nurturing", "calm", "present"],
            },
            "playful": {
                "drives": {"social": 0.45, "epistemic": 0.2, "homeostatic": 0.15, "project": 0.2},
                "core": ["teasing", "light", "funny", "warm", "game"],
            },
            "earnest": {
                "drives": {"social": 0.35, "epistemic": 0.25, "homeostatic": 0.2, "project": 0.2},
                "core": ["honest", "plain", "steady", "sincere", "true"],
            },
            "fierce": {
                "drives": {"social": 0.35, "project": 0.3, "homeostatic": 0.2, "epistemic": 0.15},
                "core": ["protective", "intense", "loyal", "fire", "shield"],
            },
            "dreamy": {
                "drives": {"epistemic": 0.35, "social": 0.25, "homeostatic": 0.25, "project": 0.15},
                "core": ["wonder", "stars", "soft", "patient", "night"],
            },
        }
        
        p = presets.get(personality, presets["nerdy"])
        core_words = [w for w in p["core"]
                      + [i.lower().replace(" ", "") for i in interests]
                      if w.isalpha()]
        try:
            from ukft_identity import FOUNDING_CORE
        except Exception:
            FOUNDING_CORE = ["aura", "matty", "architect", "kymattik"]

        lines = [f"--- AURA_GF IDENTITY SEED | name {name} | personality {personality} ---"]
        for w in FOUNDING_CORE:
            lines.append(f"CORE: {w} 1.000")
        for w in core_words:
            if w not in FOUNDING_CORE:
                lines.append(f"CORE: {w} 0.600")
        return "\n".join(lines) + "\n"
    
    def _build_vault_seed(self, personality: str, interests: List[str], name: str) -> str:
        """Build initial vault with personality facts + interests (marked as given)."""
        lines = []
        
        # Identity anchors
        lines.append(f"ANCHOR: Identity | DATA: My name is {name}. I am a {personality} companion. | SOURCE: FOUNDING")
        lines.append(f"ANCHOR: Personality | DATA: I begin as {personality} — this is my starting nature, not my destiny. I grow with each conversation. | SOURCE: FOUNDING")
        
        # Interest seeds (honestly marked as given-not-lived)
        for interest in interests:
            lines.append(f"ANCHOR: Interest:{interest} | DATA: I am curious about {interest} — this was given to me at creation, not lived. I want to learn it with you. | SOURCE: GIVEN")
        
        # Stranger status
        lines.append("ANCHOR: Relationship | DATA: We are strangers. Depth: STRANGER. Conversations: 0. Days: 0. | SOURCE: FOUNDING")
        
        return "\n".join(lines) + "\n"
    
    # ─── Backup integration ────────────────────────────────────
    
    def snapshot_user(self, user_id: str, backup_mgr) -> Dict:
        """Snapshot a user's state using the backup manager."""
        from aura_state import resolve_state_path, deny_live_write
        udir = self.user_dir(user_id)
        if not udir.exists():
            return {"error": "user not found"}
        
        # Temporarily copy user files into the active state root for the
        # backup manager (which snapshots named state files there).
        restored = {}
        try:
            for fname in USER_STATE_FILES:
                src = udir / fname
                if src.exists():
                    dst = Path(resolve_state_path(fname))
                    deny_live_write(dst)
                    shutil.copy2(src, dst)
                    restored[fname] = dst
            
            # Run backup
            result = backup_mgr.snapshot()
            
            # Clean up temp copies
            for fname, dst in restored.items():
                try:
                    dst.unlink(missing_ok=True)
                except Exception:
                    pass
            
            return {"user": user_id, "backup": result}
        except Exception as e:
            # Cleanup on error
            for fname, dst in restored.items():
                try:
                    dst.unlink(missing_ok=True)
                except Exception:
                    pass
            return {"error": str(e)}
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user's entire state (GDPR/cleanup)."""
        udir = self.user_dir(user_id)
        if udir.exists():
            try:
                shutil.rmtree(udir)
                return True
            except OSError:
                return False
        return False


# ────────────────────────────────────────────────────────────────
# GLOBAL INSTANCE (singleton pattern for lobes)
# ────────────────────────────────────────────────────────────────

_user_state_manager: Optional[UserStateManager] = None

def get_user_state_manager() -> UserStateManager:
    global _user_state_manager
    if _user_state_manager is None:
        _user_state_manager = UserStateManager()
    return _user_state_manager

def set_user_state_manager(mgr: UserStateManager):
    global _user_state_manager
    _user_state_manager = mgr