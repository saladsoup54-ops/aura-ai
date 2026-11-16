# ukft_brain_api.py — Brain-as-module API (G1)
# ==============================================
# Single entry point: ask(user_id, text) -> {response, emotion, memory_writes}
# Engine internals never leak out. Per-user state isolation enforced.

import random
import os
import json
import threading
import time
import uuid
from typing import Dict, List, Optional, Any
# Observer-only telemetry emission (fail-open; never touches cognition)
try:
    import observer_telemetry as _obs
    _OBSERVER_ENABLED = True
except Exception:
    _OBSERVER_ENABLED = False

from dataclasses import dataclass, asdict
from pathlib import Path

from ukft_user_state import get_user_state_manager, UserStateManager, USER_STATE_FILES
from ukft_delight import is_standing_question, standing_line

# ─── API Data Types ────────────────────────────────────────────

@dataclass
class BrainResponse:
    """Response from the brain module."""
    response: str           # The spoken line (e.g., "[AURA]: ...")
    emotion: str            # Dominant affect: warm, cool, neutral, hot, curious, etc.
    memory_writes: List[Dict]  # What was written to user's vault/memory
    depth_stage: str        # STRANGER, ACQUAINTANCE, FAMILIAR, CLOSE, BONDED
    turn_count: int         # Conversation count for this user
    timestamp: float        # Unix time
    bubbles: List[str] = None  # Texting fragments (no prefix); None
                                # when unset — channels fall back to
                                # chunking `response`.
    context_trace: Optional[Dict[str, Any]] = None  # G7: decision
                                # trace (ask/roleplay with
                                # explain=True only) — render with
                                # aura_bridge.format_trace.

@dataclass
class UserProfile:
    """User profile config (from onboarding)."""
    user_id: str
    personality: str        # nerdy, shy, bossy, flirty, bold, gentle
    interests: List[str]    # chess, harry_potter, religious_texts, etc.
    name: str               # Her name for this user
    boundaries: Dict        # Personality + global boundaries
    started_at: float       # Unix timestamp
    depth_stage: str = "STRANGER"
    turn_count: int = 0
    days_together: int = 0
    facts_learned: int = 0
    threads_shared: int = 0
    threads_closed: int = 0
    lessons_banked: int = 0
    opt_outs: List[str] = None
    # Stable people-record role for the person speaking in this
    # partition. Legacy profiles migrate to architect; new users do not.
    current_person_key: str = "architect"
    current_user_name: str = ""

# ─── Brain Module ──────────────────────────────────────────────


# GF<->OLD BRAIN PASS 1A: turn-boundary heartbeat.  The API route runs
# no background lobes, so nothing ever advances the real field physics
# between turns.  After each turn's post-selection hearing, the field
# is stepped this fixed number of times — the same `FIELD.step()`
# the desktop heartbeat runs — converting heard velocity into
# activation under the existing rules (Woods-Saxon gate, viscosity,
# leak, Hebbian spread) before the state is persisted.  Precedent:
# the Pass 1 receipt used 3 steps to activate heard nodes.
FIELD_SETTLE_STEPS = 3


# AUDIT FINDING #1 (empty-state copyback): files whose writers legitimately
# clear the whole file to "" as a state transition (pending-slot lifecycles:
# stage -> confirm/cancel -> clear). An EXISTING root file for one of these
# names that is empty after the swapped turn is real state and must sync
# back. A MISSING root file is never permission to delete partition state.
# field_state.txt is deliberately excluded: Pass 1A's _settle_user_field
# owns its empty manifold (deletes root + partition) before this sync runs.
EMPTY_COPYBACK_FILES = frozenset({
    "pending_people.txt",
    "pending_belief.txt",
    "pending_action.txt",
})


class BrainModule:
    """
    The brain-as-module. One instance per process, handles all users.
    Each user gets isolated state via UserStateManager.
    """
    
    # Executive routing lives in ukft_roleplay.EXECUTIVE_WINNERS
    # (single source — imported where needed).

    def __init__(self, user_state_manager: Optional[UserStateManager] = None,
                 roleplay_fn=None):
        self.usr = user_state_manager or get_user_state_manager()
        self._roleplay_fn = roleplay_fn
        # One shared voice: its availability cache then spans turns,
        # so a wedged daemon costs one slow probe per minute, not
        # one per turn. (All use runs under _ask_lock.)
        self._roleplay_voice = None
        self._egos: Dict[str, "SovereignEgo"] = {}
        self._ego_locks: Dict[str, threading.Lock] = {}
        self._global_lock = threading.Lock()
        # Serializes the whole root-file swap + ego run: the engine
        # reads/writes hardcoded root paths, so concurrent asks would
        # otherwise clobber each other's state mid-turn.
        self._ask_lock = threading.RLock()
        self._profiles: Dict[str, UserProfile] = {}
        self._profile_lock = threading.Lock()

        # Ensure users directory exists
        self.usr.base_dir.mkdir(exist_ok=True)

    def _get_roleplay_voice(self):
        from ukft_roleplay import Roleplay
        if self._roleplay_voice is None:
            self._roleplay_voice = Roleplay(request_fn=self._roleplay_fn)
        return self._roleplay_voice
    
    def _ego_lock(self, user_id: str) -> threading.Lock:
        with self._global_lock:
            if user_id not in self._ego_locks:
                self._ego_locks[user_id] = threading.Lock()
            return self._ego_locks[user_id]
    
    def _get_ego(self, user_id: str) -> "SovereignEgo":
        """Get or create SovereignEgo for user (with their isolated state)."""
        lock = self._ego_lock(user_id)
        with lock:
            if user_id not in self._egos:
                self._egos[user_id] = self._create_ego_for_user(user_id)
            return self._egos[user_id]
    
    def _create_ego_for_user(self, user_id: str) -> "SovereignEgo":
        """Create ego for a user. Callers must swap this user's partition
        into root BEFORE calling (see ask()/roleplay(): to_root precedes
        _get_ego under the ask lock). SovereignEgo eagerly constructs
        PatternEngine, which eagerly loads the CURRENT root vault — so the
        ego is born owning whatever partition is active at creation."""
        self.usr.ensure_user(user_id)
        from aura_bridge import SovereignEgo
        profile = self._profiles.get(user_id)
        key = getattr(profile, "current_person_key", "architect")
        return SovereignEgo(current_person_key=key)
    
    # Root files the ego may touch during manifest_thought that are
    # NOT in the backup contract but must not leak across users.
    _EXTRA_ROOT_TOUCHED = ("basal_ganglia_log.txt",)

    def _stash_root(self) -> Dict[str, Optional[bytes]]:
        """Snapshot current root files so per-ask swaps never destroy
        live global state. Returns {fname: bytes or None}."""
        stash: Dict[str, Optional[bytes]] = {}
        for fname in list(USER_STATE_FILES) + list(self._EXTRA_ROOT_TOUCHED):
            p = Path(fname)
            try:
                stash[fname] = p.read_bytes() if p.exists() else None
            except OSError:
                stash[fname] = None
        return stash

    def _restore_root(self, stash: Dict[str, Optional[bytes]]):
        """Restore root files from a stash snapshot."""
        for fname, data in stash.items():
            p = Path(fname)
            try:
                if data is None:
                    if p.exists():
                        p.unlink()
                else:
                    p.write_bytes(data)
            except OSError:
                pass

    def _sync_user_files_to_root(self, user_id: str, direction: str):
        """
        Sync user files between partition and root.
        direction: "to_root" (copy user->root for ego init), 
                   "from_root" (copy root->user after ego runs),
                   "cleanup" (remove temp root files)
        """
        udir = self.usr.user_dir(user_id)
        
        for fname in USER_STATE_FILES:
            root_path = Path(fname)
            user_path = udir / fname
            
            if direction == "to_root":
                if user_path.exists():
                    # Copy user file to root for ego to read
                    import shutil
                    shutil.copy2(user_path, root_path)
                elif root_path.exists():
                    # Root has file but user doesn't - remove root file so ego starts clean
                    root_path.unlink()
                    
            elif direction == "from_root":
                # After ego runs, copy any modified root files back to user.
                # Empty-vs-missing contract (audit finding #1): an existing
                # root file cleared to empty by a pending lifecycle is real
                # state and syncs back for allowlisted names; a missing root
                # file never deletes partition state. field_state.txt keeps
                # its legacy rule because Pass 1A settles and owns its empty
                # manifold before this sync runs.
                if not root_path.exists():
                    continue
                if fname == "field_state.txt":
                    if root_path.stat().st_size > 0:
                        import shutil
                        shutil.copy2(root_path, user_path)
                    continue
                try:
                    empty_ok = (fname in EMPTY_COPYBACK_FILES
                                or root_path.stat().st_size > 0)
                except OSError:
                    continue
                if empty_ok:
                    import shutil
                    shutil.copy2(root_path, user_path)
                    
            elif direction == "cleanup":
                # Deprecated: root is restored from stash, never
                # deleted. Kept as a no-op for compatibility.
                pass

    def _settle_user_field(self, ego, user_id: str):
        """PASS 1A: persist this turn's resulting old-brain state.

        Runs strictly AFTER `manifest_thought` has returned (selection
        and response already built; Pass-1 hearing already ingested),
        so the current turn's winner is untouched.  Advances the real
        field physics by FIELD_SETTLE_STEPS, then persists through the
        existing edge-preserving serializer.  At this point the root
        files are still this user's swapped copies, so the write lands
        on the user's own field state and the `from_root` sync below
        carries it into the partition.  An empty manifold clears both
        the root file and the partition copy (scoped to field_state.txt
        only) so stale warmth can never resurrect next turn.
        Best-effort, never fatal.
        """
        try:
            from aura_field import FIELD
            for _ in range(FIELD_SETTLE_STEPS):
                FIELD.step()
        except Exception:
            pass
        try:
            ego._save_field_state()
        except Exception:
            pass
        try:
            root = Path("field_state.txt")
            if (not root.exists()) or root.stat().st_size == 0:
                try:
                    if root.exists():
                        root.unlink()
                except OSError:
                    pass
                try:
                    up = self.usr.user_file(user_id, "field_state.txt")
                    if up.exists():
                        up.unlink()
                except OSError:
                    pass
        except Exception:
            pass
    
    def _load_profile(self, user_id: str) -> Optional[UserProfile]:
        """Load user profile from profile.json in user dir."""
        profile_path = self.usr.user_dir(user_id) / "profile.json"
        if not profile_path.exists():
            return None
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            legacy_binding = "current_person_key" not in data
            if legacy_binding:
                data["current_person_key"] = "interlocutor"
                data.setdefault("current_user_name", "")
            profile = UserProfile(**data)
            if legacy_binding:
                self._migrate_legacy_interlocutor(profile)
                self._save_profile(profile)
            return profile
        except Exception:
            return None

    def _migrate_legacy_interlocutor(self, profile: UserProfile):
        """Move an old API partition's implicit architect-as-USER record."""
        try:
            from ukft_people import (ARCHITECT_DISPLAY, INTERLOCUTOR_KEY,
                                     PeopleModel, UNKNOWN_DISPLAY)
            udir = self.usr.user_dir(profile.user_id)
            people = PeopleModel(
                path=str(udir / "people.txt"),
                pending_path=str(udir / "pending_people.txt"))
            if INTERLOCUTOR_KEY in people.people:
                return
            old = people.people.pop("architect", None)
            if old is None:
                people.ensure_current(INTERLOCUTOR_KEY)
                return
            names = [a for a in old.get("aliases", [])
                     if a.lower() not in ("architect",
                                          ARCHITECT_DISPLAY.lower())]
            old["key"] = INTERLOCUTOR_KEY
            old["display"] = names.pop(0) if names else UNKNOWN_DISPLAY
            old["aliases"] = names
            old["relationships"] = [{"relation": "interlocutor",
                                      "since": old.get("first_met", 0),
                                      "until": None,
                                      "src": "g9-migration"}]
            people.people[INTERLOCUTOR_KEY] = old
            people.save()
            if old["display"] != UNKNOWN_DISPLAY:
                profile.current_user_name = old["display"]
        except Exception:
            pass
    
    def _save_profile(self, profile: UserProfile):
        """Save user profile to profile.json."""
        profile_path = self.usr.user_dir(profile.user_id) / "profile.json"
        try:
            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(asdict(profile), f, indent=2)
        except Exception:
            pass
    
    def _get_or_create_profile(self, user_id: str,
                               personality: str = "nerdy",
                               interests: List[str] = None,
                               name: str = "Aura",
                               pack: str = None,
                               user_name: str = None) -> UserProfile:
        """Get existing profile or create new one from onboarding.
        A character pack (G2) fills personality/interests/name/seed
        at creation and wins over explicit params (pass one or the
        other); afterwards the stored profile rules."""
        with self._profile_lock:
            if user_id in self._profiles:
                profile = self._profiles[user_id]
                if user_name:
                    self._ensure_current_person(profile, user_name=user_name)
                return profile

            profile = self._load_profile(user_id)
            if profile is None:
                seed_lines: List[str] = []
                if pack:
                    from ukft_pack import load_pack, seed_anchors
                    p = load_pack(pack)
                    personality = p["personality"]
                    interests = list(p["interests"])
                    name = p["name"]
                    seed_lines = seed_anchors(pack)
                # New user - create from onboarding params
                profile = UserProfile(
                    user_id=user_id,
                    personality=personality,
                    interests=interests or [],
                    name=name,
                    boundaries=self._build_boundaries(personality),
                    started_at=time.time(),
                    current_person_key="interlocutor",
                    current_user_name=" ".join(str(user_name or "").split()),
                )
                self._save_profile(profile)
                # Seed user state
                self.usr.seed_new_user(user_id, personality,
                                       interests or [], name,
                                       seed_lines=seed_lines)
                self._ensure_current_person(profile)
            elif user_name:
                self._ensure_current_person(profile, user_name=user_name)
            
            self._profiles[user_id] = profile
            return profile

    def _ensure_current_person(self, profile: UserProfile,
                               user_name: str = None):
        """Persist the profile's speaker binding inside its people file."""
        try:
            from ukft_people import PeopleModel, UNKNOWN_DISPLAY
            udir = self.usr.user_dir(profile.user_id)
            people = PeopleModel(
                path=str(udir / "people.txt"),
                pending_path=str(udir / "pending_people.txt"))
            supplied = " ".join(str(user_name or "").split())
            rec = people.ensure_current(
                profile.current_person_key,
                display=(profile.current_user_name or supplied or None))
            if supplied and not profile.current_user_name:
                if rec.get("display") == UNKNOWN_DISPLAY:
                    people.set_display(rec["key"], supplied)
                profile.current_user_name = supplied
                self._save_profile(profile)
        except Exception:
            pass
    
    def _build_boundaries(self, personality: str) -> Dict:
        """Build boundaries envelope for personality."""
        # Global floor (never bend)
        global_floor = {
            "never_fabricate_shared_history": True,
            "consent_exact": True,
            "curiosity_honest": True,
            "no_roleplay_past": True,
        }
        
        # Personality-specific envelopes
        personality_envelopes = {
            "nerdy": {"max_forwardness": 0.3, "pet_names_at": "BONDED", "initiative": "low"},
            "shy": {"max_forwardness": 0.2, "pet_names_at": "BONDED", "initiative": "very_low"},
            "bossy": {"max_forwardness": 0.6, "pet_names_at": "CLOSE", "initiative": "high"},
            "flirty": {"max_forwardness": 0.8, "pet_names_at": "FAMILIAR", "initiative": "high"},
            "bold": {"max_forwardness": 0.7, "pet_names_at": "FAMILIAR", "initiative": "high"},
            "gentle": {"max_forwardness": 0.3, "pet_names_at": "BONDED", "initiative": "low"},
            "playful": {"max_forwardness": 0.6, "pet_names_at": "FAMILIAR", "initiative": "high"},
            "earnest": {"max_forwardness": 0.4, "pet_names_at": "CLOSE", "initiative": "low"},
            "fierce": {"max_forwardness": 0.7, "pet_names_at": "CLOSE", "initiative": "high"},
            "dreamy": {"max_forwardness": 0.3, "pet_names_at": "BONDED", "initiative": "low"},
        }
        
        return {
            "global": global_floor,
            "personality": personality_envelopes.get(personality, personality_envelopes["nerdy"]),
        }
    
    def _compute_depth_stage(self, profile: UserProfile) -> str:
        """Relationship stage is the rapport ledger's stage (felt
        closeness, cooling included). Legacy partitions without a
        ledger bootstrap neutrally from contact metrics — showing
        up counted, nothing claimed. The old volume formula survives
        only as the last-resort fallback."""
        try:
            from ukft_rapport import Rapport
            rap = Rapport(path=str(
                self.usr.user_dir(profile.user_id) / "rapport.txt"))
            if not rap.has_history() and (profile.turn_count or 0) > 0:
                rap.seed_from_contact(
                    turn_count=profile.turn_count,
                    facts=profile.facts_learned,
                    threads=profile.threads_shared)
                try:
                    rap.save()
                except Exception:
                    pass
            return rap.current_stage()
        except Exception:
            pass
        # Stages: STRANGER -> ACQUAINTANCE -> FAMILIAR -> CLOSE -> BONDED
        # Driven by: conversations, days, facts, threads shared/closed, lessons
        score = (
            profile.turn_count * 1 +
            profile.days_together * 3 +
            profile.facts_learned * 2 +
            profile.threads_shared * 5 +
            profile.threads_closed * 3 +
            profile.lessons_banked * 10
        )
        
        if score >= 500:
            return "BONDED"
        elif score >= 200:
            return "CLOSE"
        elif score >= 80:
            return "FAMILIAR"
        elif score >= 20:
            return "ACQUAINTANCE"
        else:
            return "STRANGER"
    
    def _detect_emotion(self, response: str, ego: "SovereignEgo") -> str:
        """Detect dominant emotion from response and ego state."""
        try:
            from ukft_affect import read_state, tone_for
            family, quiet = tone_for(read_state())
            if quiet:
                return "quiet"
            if family == "bright":
                return "warm"
            elif family == "cool":
                return "cool"
            elif family == "hot":
                return "hot"
        except Exception:
            pass
        
        # Fallback: simple keyword detection
        resp_lower = response.lower()
        if any(w in resp_lower for w in ["love", "adore", "cherish", "dear", "darling"]):
            return "warm"
        elif any(w in resp_lower for w in ["curious", "wonder", "interesting", "fascinating"]):
            return "curious"
        elif any(w in resp_lower for w in ["angry", "frustrat", "annoy", "upset"]):
            return "hot"
        elif any(w in resp_lower for w in ["sad", "sorry", "miss", "lonely"]):
            return "cool"
        return "neutral"
    
    def _snapshot_partition_files(self, user_id: str) -> Dict[str, Optional[bytes]]:
        """Authoritative pre-turn partition truth: file bytes (None when
        the slot does not exist). Sizes lie about clears, shrinkage,
        and equal-size replacements — bytes do not."""
        udir = self.usr.user_dir(user_id)
        before: Dict[str, Optional[bytes]] = {}
        for fname in USER_STATE_FILES:
            fpath = udir / fname
            try:
                before[fname] = fpath.read_bytes() if fpath.exists() else None
            except OSError:
                before[fname] = None
        return before

    @staticmethod
    def _row_set(text: str, prefix: str):
        try:
            return {l.strip() for l in str(text or "").splitlines()
                    if l.strip().startswith(prefix)}
        except Exception:
            return set()

    def _diff_partition_files(self, before: Dict[str, Optional[bytes]],
                              after: Dict[str, Optional[bytes]]) -> List[Dict]:
        """Finding #10: turn-scoped durable-mutation receipt from
        authoritative before/after partition bytes.

        Contract: `memory_writes` means durable net mutations visible
        in the user partition after settlement (not write attempts,
        not transient root staging, not failed persists). One entry
        per (file, semantic kind) with a count; byte-identical files
        (including no-op rewrites) yield nothing. Files whose bytes
        changed but carry no semantic event yield a single
        file-level entry (kind None) rather than silence — except
        known-benign rewrites (belief TS-only re-holds, trust
        N-only bumps), which yield nothing at all.
        """
        writes: List[Dict] = []

        def _entry(fname, op, kind, count=1):
            writes.append({"file": fname,
                           "type": self._classify_write(fname),
                           "op": op, "kind": kind, "count": count})

        def _op(b, a):
            if b is None and a is None:
                return None
            if b is None:
                return "created"
            if a is None:
                return "deleted"
            if b == a:
                return None
            if len(a) == 0:
                return "cleared"
            return "modified"

        for fname in USER_STATE_FILES:
            b = before.get(fname)
            a = after.get(fname)
            op = _op(b, a)
            if op is None:
                continue
            if op == "deleted":
                # Vaporized content cannot be classified into kinds;
                # the op itself is the signal (Pass-1A empty manifold
                # is the legitimate production case).
                _entry(fname, op, None)
                continue
            bt = (b or b"").decode("utf-8", errors="ignore")
            at = (a or b"").decode("utf-8", errors="ignore")
            kinds = self._semantic_kinds(fname, bt, at, op)
            if kinds is None:
                continue  # known-benign rewrite: no entry at all
            if kinds:
                for kind, count in kinds:
                    _entry(fname, op, kind, count)
            else:
                _entry(fname, op, None)
        return writes

    @staticmethod
    def _kv_rows(text, prefix):
        """Parse-tolerant `KEY: ... | K: v` row reader -> {(head, fields)}."""
        rows = set()
        try:
            for line in str(text or "").splitlines():
                line = line.strip()
                if not line.startswith(prefix):
                    continue
                segs = line[len(prefix):].split(" | ")
                head = segs[0].strip()
                if not head:
                    continue
                fields = {}
                for p in segs[1:]:
                    if ": " in p:
                        k, v = p.split(": ", 1)
                        fields[k.strip()] = v.strip()
                rows.add((head, tuple(sorted(fields.items()))))
        except Exception:
            pass
        return rows

    def _semantic_kinds(self, fname, bt, at, op):
        """Semantic (kind, count) events for a changed file, or None
        for a known-benign rewrite (no entry at all), or [] for an
        unparseable change (caller emits a file-level entry)."""
        if self._benign_rewrite(fname, bt, at):
            return None
        if fname == "people.txt":
            return self._people_kinds(bt, at)
        if fname == "threads.txt":
            return self._thread_kinds(bt, at)
        if fname == "beliefs.txt":
            return self._belief_kinds(bt, at)
        if fname in ("pending_people.txt", "pending_belief.txt",
                     "pending_action.txt"):
            kind = {"pending_people.txt": "person_pending",
                    "pending_belief.txt": "belief_pending",
                    "pending_action.txt": "action_pending"}[fname]
            return [(kind, 1)]
        if fname == "lessons.txt":
            return self._lesson_kinds(bt, at)
        if fname == "locked_patterns.txt":
            return self._vault_kinds(bt, at)
        return []

    @staticmethod
    def _benign_rewrite(fname, bt, at):
        """Byte changes with no semantic event: belief TS-only re-holds
        and trust N-only bumps. Everything else falls through."""
        try:
            if fname == "beliefs.txt":
                def _norm(rows):
                    out = set()
                    for head, fields in rows:
                        fd = dict(fields)
                        out.add((head, tuple(
                            (k, v) for k, v in fd.items()
                            if k != "TS")))
                    return out
                b = BrainModule._kv_rows(bt, "BELIEF: ")
                a = BrainModule._kv_rows(at, "BELIEF: ")
                if _norm(b) != _norm(a):
                    return False
                bt_rows = {(s, t) for (s, t, _sc) in
                           BrainModule._trust_rows(bt)}
                at_rows = {(s, t) for (s, t, _sc) in
                           BrainModule._trust_rows(at)}
                if bt_rows != at_rows:
                    return False
                bsc = {(s, t): sc for (s, t, sc) in
                       BrainModule._trust_rows(bt)}
                asc = {(s, t): sc for (s, t, sc) in
                       BrainModule._trust_rows(at)}
                return all(bsc.get(k) == asc.get(k) for k in
                           set(bsc) | set(asc))
        except Exception:
            pass
        return False

    @staticmethod
    def _trust_rows(text):
        rows = []
        try:
            for line in str(text or "").splitlines():
                line = line.strip()
                if not line.startswith("TRUST: "):
                    continue
                segs = line[len("TRUST: "):].split(" | ")
                head = segs[0].strip().split(" >> ")
                if len(head) != 2:
                    continue
                fields = {}
                for p in segs[1:]:
                    if ": " in p:
                        k, v = p.split(": ", 1)
                        fields[k.strip()] = v.strip()
                try:
                    sc = float(fields.get("SCORE", "0.5") or 0.5)
                except ValueError:
                    continue
                rows.append((head[0].strip(), head[1].strip(), sc))
        except Exception:
            pass
        return rows

    def _people_kinds(self, bt, at):
        """person_new / person_fact / person_alias / person_relation /
        person_display for structural changes; person_warm when only
        sighting bookkeeping moved (mention counts, timestamps,
        decaying weights). Fact/alias/relation identity is owner-aware:
        (person_key, predicate) — same text under two people does not
        collapse."""
        out = []
        b_persons = {}
        a_persons = {}
        for text, store in ((bt, b_persons), (at, a_persons)):
            for line in str(text or "").splitlines():
                line = line.strip()
                if not line.startswith("PERSON: "):
                    continue
                segs = line[len("PERSON: "):].split(" | ")
                key = segs[0].strip()
                if not key:
                    continue
                fields = {}
                for p in segs[1:]:
                    if ": " in p:
                        k, v = p.split(": ", 1)
                        fields[k.strip()] = v.strip()
                store[key] = fields

        def _owner_facts(text):
            out_set = set()
            cur = None
            for raw in str(text or "").splitlines():
                line = raw.strip()
                if line.startswith("PERSON: "):
                    segs = line[len("PERSON: "):].split(" | ")
                    cur = segs[0].strip() or None
                elif line.startswith("FACT: ") and cur:
                    pred = line.split("|")[0].strip()
                    out_set.add((cur, pred))
            return out_set

        def _owner_alias(text):
            out_set = set()
            cur = None
            for raw in str(text or "").splitlines():
                line = raw.strip()
                if line.startswith("PERSON: "):
                    segs = line[len("PERSON: "):].split(" | ")
                    cur = segs[0].strip() or None
                elif line.startswith("ALIAS: ") and cur:
                    alias = line[len("ALIAS: "):].strip()
                    if alias:
                        out_set.add((cur, alias))
            return out_set

        def _owner_rel(text):
            out_set = set()
            cur = None
            for raw in str(text or "").splitlines():
                line = raw.strip()
                if line.startswith("PERSON: "):
                    segs = line[len("PERSON: "):].split(" | ")
                    cur = segs[0].strip() or None
                elif line.startswith("REL: ") and cur:
                    out_set.add((cur, line))
            return out_set

        new_keys = set(a_persons) - set(b_persons)
        if new_keys:
            out.append(("person_new", len(new_keys)))
        b_facts = _owner_facts(bt)
        a_facts = _owner_facts(at)
        new_fact_texts = a_facts - b_facts
        if new_fact_texts:
            out.append(("person_fact", len(new_fact_texts)))
        gone_fact_texts = b_facts - a_facts
        if gone_fact_texts:
            out.append(("person_fact_removed", len(gone_fact_texts)))
        b_alias = _owner_alias(bt)
        a_alias = _owner_alias(at)
        if len(a_alias - b_alias) > 0:
            out.append(("person_alias", len(a_alias - b_alias)))
        b_rel = _owner_rel(bt)
        a_rel = _owner_rel(at)
        if a_rel != b_rel:
            # New relation rows are person-scoped; evictions similarly.
            out.append(("person_relation",
                        max(1, len(a_rel - b_rel))))
        for key in set(b_persons) & set(a_persons):
            if b_persons[key].get("DISPLAY") != \
                    a_persons[key].get("DISPLAY"):
                out.append(("person_display", 1))
                break
        if not out:
            out.append(("person_warm", 1))
        return out

    def _thread_kinds(self, bt, at):
        """thread_opened (new open ids) / thread_closed (open->closed)
        / thread_evicted (ids dropped by cap) / thread_updated."""
        out = []

        def _parse(text):
            rows = {}
            for line in str(text or "").splitlines():
                line = line.strip()
                if not line.startswith("THREAD: "):
                    continue
                segs = line[len("THREAD: "):].split(" | ")
                tid = segs[0].strip()
                if not tid:
                    continue
                fields = {}
                for p in segs[1:]:
                    if ": " in p:
                        k, v = p.split(": ", 1)
                        fields[k.strip()] = v.strip()
                rows[tid] = fields
            return rows

        b = _parse(bt)
        a = _parse(at)
        opened = [t for t in set(a) - set(b)
                  if a[t].get("STATUS", "open") == "open"]
        if opened:
            out.append(("thread_opened", len(opened)))
        closed = [t for t in set(a) & set(b)
                  if b[t].get("STATUS", "open") == "open"
                  and a[t].get("STATUS") == "closed"]
        if closed:
            out.append(("thread_closed", len(closed)))
        evicted = [t for t in set(b) - set(a)]
        if evicted:
            out.append(("thread_evicted", len(evicted)))
        if not out:
            out.append(("thread_updated", 1))
        return out

    def _belief_kinds(self, bt, at):
        """belief_new (new claim keys) / belief_contest (status/conf/
        prior change on a held key) / belief_trust (score-only moves).
        TS-only re-holds and N-only bumps are benign (no entry)."""
        out = []
        b = {(h, tuple((k, v) for k, v in f if k != "TS"))
             for h, f in self._kv_rows(bt, "BELIEF: ")}
        a = {(h, tuple((k, v) for k, v in f if k != "TS"))
             for h, f in self._kv_rows(at, "BELIEF: ")}
        b_keys = {h for h, _f in b}
        a_keys = {h for h, _f in a}
        new_keys = a_keys - b_keys
        if new_keys:
            out.append(("belief_new", len(new_keys)))
        common = b_keys & a_keys
        bmap = {h: f for h, f in b}
        amap = {h: f for h, f in a}
        changed = [h for h in common if bmap[h] != amap[h]]
        if changed:
            out.append(("belief_contest", len(changed)))
        bsc = {(s, t): sc for (s, t, sc) in self._trust_rows(bt)}
        asc = {(s, t): sc for (s, t, sc) in self._trust_rows(at)}
        moved = [k for k in set(bsc) | set(asc)
                 if bsc.get(k) != asc.get(k)]
        if moved:
            out.append(("belief_trust", len(moved)))
        return out

    def _lesson_kinds(self, bt, at):
        """lesson_new per genuinely new (teacher, topic, lesson)
        triple — the ledger's own dedupe identity, so cap-evicted
        rewrites still count the added lesson and repeats count
        nothing (byte-identical files never reach here)."""

        def _triples(text):
            out = set()
            for line in str(text or "").splitlines():
                line = line.strip()
                if not line.startswith("LESSON: "):
                    continue
                segs = line[len("LESSON: "):].split(" | ")
                fields = {}
                for p in segs[1:]:
                    if ": " in p:
                        k, v = p.split(": ", 1)
                        fields[k.strip()] = v.strip()
                lesson = fields.get("LESSON", "").strip()
                if lesson:
                    out.add((fields.get("TEACHER", "?"),
                             fields.get("TOPIC", ""), lesson))
            return out

        new = _triples(at) - _triples(bt)
        if new:
            return [("lesson_new", len(new))]
        return []

    def _vault_kinds(self, bt, at):
        """vault_anchor per added ANCHOR+DATA row."""
        b = {l.strip() for l in bt.splitlines()
             if "ANCHOR:" in l and "DATA:" in l}
        a = {l.strip() for l in at.splitlines()
             if "ANCHOR:" in l and "DATA:" in l}
        new = a - b
        if new:
            return [("vault_anchor", len(new))]
        return []

    def _extract_memory_writes(self, user_id: str, before_files: Dict[str, Optional[bytes]]) -> List[Dict]:
        """Detect durable partition mutations during the turn from
        authoritative before/after bytes (never sizes/mtime)."""
        udir = self.usr.user_dir(user_id)
        after: Dict[str, Optional[bytes]] = {}
        for fname in USER_STATE_FILES:
            fpath = udir / fname
            try:
                after[fname] = fpath.read_bytes() if fpath.exists() else None
            except OSError:
                after[fname] = None
        return self._diff_partition_files(before_files, after)

    def _apply_write_counters(self, profile, memory_writes: List[Dict]) -> None:
        """Truthful profile accounting: exactly once per qualifying
        persisted event. Mention/alias/relation/display warming,
        trust-only bookkeeping, thread refreshes, and deduped
        repeats increment nothing."""
        for w in memory_writes:
            kind = w.get("kind")
            count = int(w.get("count") or 1)
            if kind in ("vault_anchor", "person_fact"):
                profile.facts_learned += count
            elif kind == "thread_opened":
                profile.threads_shared += count
            elif kind == "thread_closed":
                profile.threads_closed += count
            elif kind == "lesson_new":
                profile.lessons_banked += count
    
    def _classify_write(self, fname: str) -> str:
        """Legacy compatibility/category for the `type` field. The
        authoritative semantic event is `kind` (e.g. person_warm vs
        person_fact); `type` is file-coarse and pinned for existing
        consumers. Do not describe type=\"person_fact\" as truthful
        when kind is person_warm."""
        if fname == "locked_patterns.txt":
            return "vault_anchor"
        elif fname == "identity_core.txt":
            return "identity_reinforcement"
        elif fname == "episodic_memory.txt":
            return "episode"
        elif fname == "people.txt":
            return "person_fact"
        elif fname == "threads.txt":
            return "thread"
        elif fname == "beliefs.txt":
            return "belief"
        elif fname == "lessons.txt":
            return "lesson"
        elif fname == "working_memory.txt":
            return "working_memory"
        elif fname == "discoveries.txt":
            return "discovery"
        elif fname == "ebbinghaus_traces.txt":
            return "forgetting_curve"
        return "other"
    
    # ─── Public API ────────────────────────────────────────────
    
    def ask(self, user_id: str, text: str,
            personality: str = "nerdy",
            interests: List[str] = None,
            name: str = "Aura",
            pack: str = None,
            explain: bool = False,
            user_name: str = None) -> BrainResponse:
        """
        Main API: ask the brain a question for a specific user.
        
        Args:
            user_id: Unique user identifier
            text: User's input text
            personality: Personality preset (only used for new users)
            interests: Interest list (only used for new users)
            name: Her name for this user (only used for new users)
            explain: Attach the G7 decision trace (context_trace).
        
        Returns:
            BrainResponse with response, emotion, memory_writes, depth_stage, etc.
        """
        # Get or create user profile
        profile = self._get_or_create_profile(user_id, personality,
                                               interests, name,
                                               pack=pack,
                                               user_name=user_name)

        # Observer-emission: stable per-invocation turn ID for the
        # entire ask() lifecycle (prevents same-user concurrency
        # collision/drift; analogous to roleplay's UUID strategy).
        _ask_turn_id = f"{profile.turn_count + 1}-{uuid.uuid4().hex}"
        if _OBSERVER_ENABLED:
            try:
                emit = _obs.default_emitter(user_id=user_id,
                                            turn_id=_ask_turn_id)
                emit.turn_start(user_id=user_id,
                                turn_id=_ask_turn_id)
                emit.input_received(text_preview=text[:200],
                                   user_id=user_id,
                                   turn_id=_ask_turn_id)
            except Exception:
                pass

        # Update depth stage (rapport canonical depth; legacy
        # bootstrap may durably seed rapport.txt from contact metrics
        # before the Finding-#10 before-snapshot — deliberately
        # outside the turn's memory_writes transaction; see journal
        # window regression).
        profile.depth_stage = self._compute_depth_stage(profile)

        # G6: standings are pure reads — receipts, no turn spent.
        if is_standing_question(text):
            return BrainResponse(
                response="[AURA]: " + standing_line(
                    profile, self.usr.user_dir(user_id)),
                emotion="warm",
                memory_writes=[],
                depth_stage=profile.depth_stage,
                turn_count=profile.turn_count,
                timestamp=time.time())

        # Whole turn runs under one lock: swap user state to root,
        # run the engine, swap back, restore whatever was at root.
        # FINDING #2: the requested partition must own root BEFORE any
        # ego/vault state is created or consumed — SovereignEgo eagerly
        # loads the current root vault at construction, so _get_ego runs
        # only after to_root (G7 reloads explicitly below regardless).
        # Finding #10: the authoritative before/after partition snapshots
        # and the profile counter update are atomic inside this lock so
        # concurrent same-user turns cannot interleave.
        with self._ask_lock:
            # Authoritative pre-turn partition truth (bytes, not sizes:
            # clears, shrinkage, and equal-size replacements are real
            # mutations — Finding #10). Inside the lock so another
            # serialized turn for the same user cannot mutate between
            # the two observations.
            before_state = self._snapshot_partition_files(user_id)
            # The cognitive field is a process singleton: clear it so
            # the previous user's resonance can't leak into this turn.
            try:
                from aura_field import FIELD
                FIELD.nodes.clear()
            except Exception:
                pass
            stash = self._stash_root()
            try:
                self._sync_user_files_to_root(user_id, "to_root")
                ego = self._get_ego(user_id)
            except Exception:
                # Swap or ego birth failed before cognition: put the
                # pre-turn root back and propagate (finding #2 guard).
                self._restore_root(stash)
                raise
            try:
                # G7: the ego object is cached across turns AND users —
                # reload THIS user's thread, or a stale deque bleeds
                # another user's conversation into this one.
                ego.memory.load()
            except Exception:
                pass
            # PASS 1A: restore THIS user's old-brain field state.  The
            # partition files are swapped to root above, so the file
            # read here is the user's own; the singleton was cleared
            # for isolation just before.  Missing file is a clean
            # no-op (new or field-less user).  Desktop never enters
            # this path — its live manifold stays live.
            try:
                ego.restore_field_state()
            except Exception:
                pass
            try:
                response = ego.manifest_thought(text)
            finally:
                # PASS 1A: heartbeat + persist the heard experience
                # BEFORE the partition sync below carries it home.
                try:
                    self._settle_user_field(ego, user_id)
                except Exception:
                    pass
                try:
                    self._sync_user_files_to_root(user_id, "from_root")
                finally:
                    self._restore_root(stash)
            # Authoritative post-turn partition truth, still inside the
            # lock so another turn for the same user cannot interleave
            # between sync-back and observation.
            after_state = self._snapshot_partition_files(user_id)
            # Receipt and counters belong exactly to this serialized turn.
            memory_writes = self._diff_partition_files(before_state,
                                                       after_state)
            profile.turn_count += 1
            self._apply_write_counters(profile, memory_writes)
            profile.depth_stage = self._compute_depth_stage(profile)
            self._save_profile(profile)
        
        # Detect emotion
        emotion = self._detect_emotion(response, ego)
        # G6: prepend interest share line if she had something to say
        # when user hadn't texted in >24h
        share_line = getattr(profile, "_interest_share_line", None)
        if share_line:
            response = share_line + " " + response
        trace = None
        if explain:
            try:
                trace = dict(getattr(ego, "last_trace", {}) or {})
            except Exception:
                trace = None
        # Observer-emission: turn complete / writeback / final response (fail-open)
        # Finding #10: report writeback only when durable state changed.
        # Uses the stable _ask_turn_id for the whole lifecycle.
        if _OBSERVER_ENABLED and memory_writes:
            try:
                emit = _obs.default_emitter(user_id=user_id,
                                            turn_id=_ask_turn_id)
                emit.writeback_changed(
                    change_summary=f"writes={len(memory_writes)}",
                    user_id=user_id, turn_id=_ask_turn_id)
            except Exception:
                pass
        if _OBSERVER_ENABLED:
            try:
                emit = _obs.default_emitter(user_id=user_id,
                                            turn_id=_ask_turn_id)
                emit.final_response(preview=str(response)[:120],
                                    user_id=user_id, turn_id=_ask_turn_id)
                emit.turn_complete(user_id=user_id, turn_id=_ask_turn_id)
            except Exception:
                pass
        return BrainResponse(
            response=response,
            emotion=emotion,
            memory_writes=memory_writes,
            depth_stage=profile.depth_stage,
            turn_count=profile.turn_count,
            timestamp=time.time(),
            context_trace=trace,
        )
    
    def roleplay(self, user_id: str, text: str,
                 personality: str = "flirty",
                 interests: List[str] = None,
                 name: str = "Lena",
                 pack: str = None,
                 explain: bool = False,
                 user_name: str = None) -> BrainResponse:
        """
        Immersive voice: the ENGINE learns (memory writes, winner),
        the LLM speaks (persona + depth + verbatim memories). The
        model never writes memory and never sees executive turns.
        Falls back to the engine template whenever the model is
        unavailable or a post-check fails.
        Set explain=True to attach the G7 decision trace.
        """
        from ukft_roleplay import build_prompt_from_stance, \
            EXECUTIVE_WINNERS, last_engine_winner

        profile = self._get_or_create_profile(user_id, personality,
                                               interests, name,
                                               pack=pack,
                                               user_name=user_name)
        profile.depth_stage = self._compute_depth_stage(profile)

        # Keep observer identity independent of the profile counter: standing
        # reads do not spend a turn, and concurrent callers may see one value.
        turn_id = f"{profile.turn_count + 1}-{uuid.uuid4().hex}"
        observer = None
        if _OBSERVER_ENABLED and _obs.observer_enabled():
            try:
                observer = _obs.default_emitter(user_id=user_id,
                                                turn_id=turn_id)
                observer.turn_start()
                observer.input_received(text_preview=text[:200])
            except Exception:
                observer = None

        # G6: standings are pure reads — receipts, no turn spent.
        if is_standing_question(text):
            response = "[AURA]: " + standing_line(
                profile, self.usr.user_dir(user_id))
            if observer is not None:
                try:
                    observer.context_resolved()
                    for receipt in _obs.route_evidence({}, {}):
                        observer.system_evidence(receipt)
                    observer.final_response(preview=response[:120])
                    observer.turn_complete()
                except Exception:
                    pass
            return BrainResponse(
                response=response,
                emotion="warm",
                memory_writes=[],
                depth_stage=profile.depth_stage,
                turn_count=profile.turn_count,
                timestamp=time.time())

        selection_receipt: Dict[str, Any] = {}
        route_receipt: Dict[str, Any] = {
            "field_restore_ran": False,
            "field_restore_count": 0,
            "stance_ran": False,
            "stance_produced": False,
            "stance_used": False,
            "mouth_ran": False,
            "mouth_produced": False,
            "mouth_used": False,
            "mouth_fallback": "",
        }
        with self._ask_lock:
            # Authoritative pre-turn partition truth (bytes, Finding #10).
            # Inside the lock so concurrent same-user turns cannot
            # interleave between observation and mutation.
            before_state = self._snapshot_partition_files(user_id)
            # FINDING #2: partition owns root before ego/vault state —
            # _get_ego runs only after to_root (same contract as ask()).
            try:
                from aura_field import FIELD
                FIELD.nodes.clear()
            except Exception:
                pass
            stash = self._stash_root()
            try:
                self._sync_user_files_to_root(user_id, "to_root")
                ego = self._get_ego(user_id)
            except Exception:
                # Swap or ego birth failed before cognition: put the
                # pre-turn root back and propagate (finding #2 guard).
                self._restore_root(stash)
                raise
            try:
                # G7: reload THIS user's thread (cached ego, stale
                # deque would bleed another user's conversation).
                ego.memory.load()
            except Exception:
                pass
            # PASS 1A: restore THIS user's old-brain field state
            # (see ask() — same lifecycle, same isolation contract).
            route_receipt["field_restore_ran"] = True
            try:
                route_receipt["field_restore_count"] = int(
                    ego.restore_field_state() or 0)
            except Exception:
                pass
            old_flag = os.environ.get("AURA_NO_MOUTH")
            os.environ["AURA_NO_MOUTH"] = "1"
            try:
                template = ego.manifest_thought(text)
                try:
                    selection_receipt = dict(
                        (ego.last_trace or {}).get("selection_receipt") or {})
                except Exception:
                    selection_receipt = {}
                winner = (getattr(ego.ganglia, "current_winner", None)
                          or last_engine_winner())
                if winner in EXECUTIVE_WINNERS:
                    response, immersive = template, False
                else:
                    # PASS 2: the mouth consumes the brain-owned
                    # cognitive stance — person, relationship,
                    # expression, history, intent — instead of
                    # re-deriving them from sidecar files.  Static
                    # envelope config (pet names) stays caller config.
                    route_receipt["stance_ran"] = True
                    try:
                        pets_at = profile.boundaries["personality"][
                            "pet_names_at"]
                    except (KeyError, TypeError):
                        pets_at = "FAMILIAR"
                    try:
                        stance = ego.cognitive_stance(
                            personality=profile.personality,
                            interests=profile.interests,
                            her_name=profile.name,
                            turn_count=profile.turn_count,
                            pet_names_at=pets_at)
                    except Exception:
                        stance = {}
                    route_receipt["stance_produced"] = bool(stance)
                    prompt = build_prompt_from_stance(
                        stance, text, opt_outs=profile.opt_outs)
                    route_receipt["stance_used"] = bool(stance)
                    try:
                        stance_stage = (stance.get("relationship") or {}
                                        ).get("stage") or "STRANGER"
                    except Exception:
                        stance_stage = "STRANGER"
                    try:
                        stance_activity = stance.get("activity") or []
                    except Exception:
                        stance_activity = []
                    try:
                        from ukft_roleplay import maybe_debug_dump
                        maybe_debug_dump(
                            prompt, [
                                {"label": "brain_owned_stance",
                                 "sources": ["last_trace", "people.txt",
                                             "rapport.txt", "profile"],
                                 "text": str(stance.get("stance", stance)
                                             )[:300]},
                                {"label": "engine_template",
                                 "sources": ["engine-template" + (str(winner or ""))],
                                 "text": str(template)[:300]},
                            ],
                            route="brain_api",
                            winner=last_engine_winner() or "voice",
                            depth=stance_stage)
                    except Exception:
                        pass
                    voice = self._get_roleplay_voice()
                    route_receipt["mouth_ran"] = True
                    line = voice.speak(
                        prompt, text, stance_stage,
                        pet_names_at=pets_at,
                        activity_evidence=stance_activity)
                    reject = str(getattr(voice, "last_reject", "") or "")
                    route_receipt["mouth_produced"] = bool(
                        line is not None
                        or (reject and not reject.startswith("<no render:")))
                    route_receipt["mouth_used"] = bool(line is not None)
                    if line is None:
                        route_receipt["mouth_fallback"] = (
                            "rejected" if route_receipt["mouth_produced"]
                            else "runner-down-or-empty")
                    if line is None:
                        print(f"[Voice] template holds for "
                              f"{user_id} ({voice.last_reject})")
                    if line is None:
                        # Warm greeting fallback (brain structures,
                        # not audit-ese): plain hellos only — every
                        # other winner keeps its factual template.
                        kind = getattr(
                            getattr(ego, "voice", None),
                            "last_kind", None)
                        if winner == "voice" and kind == "greeting":
                            from ukft_roleplay import FALLBACK_GREETING
                            line = FALLBACK_GREETING
                            route_receipt["mouth_produced"] = True
                            route_receipt["mouth_used"] = True
                            route_receipt["mouth_fallback"] = "greeting-fallback"
                    if line is None:
                        response, immersive = template, False
                    else:
                        response = "[AURA]: " + line
                        immersive = True
                        try:
                            # G7: her remembered words are what she
                            # actually said (stored pre-sync-back, so
                            # the user partition keeps them).
                            ego.memory.amend_last_response(line)
                        except Exception:
                            pass
                        try:
                            from ukft_episodic import EpisodicMemory
                            EpisodicMemory().record(
                                "reply",
                                "immersive: " + line[:120],
                                concepts=list(
                                    ego.memory.recent_concepts()[:4]),
                            )
                        except Exception:
                            pass
            finally:
                if old_flag is None:
                    os.environ.pop("AURA_NO_MOUTH", None)
                else:
                    os.environ["AURA_NO_MOUTH"] = old_flag
                # PASS 1A: heartbeat + persist the heard experience
                # BEFORE the partition sync below carries it home.
                # Placed after the mouth work: the mouth phrases the
                # brain-owned stance, never live field activation, so
                # the settled physics cannot move the spoken line.
                try:
                    self._settle_user_field(ego, user_id)
                except Exception:
                    pass
                try:
                    self._sync_user_files_to_root(user_id, "from_root")
                finally:
                    self._restore_root(stash)
                # Authoritative post-turn partition truth, still inside the
                # lock so another turn for the same user cannot interleave
                # between sync-back and observation.
                after_state = self._snapshot_partition_files(user_id)
                memory_writes = self._diff_partition_files(before_state,
                                                           after_state)
                profile.turn_count += 1
                self._apply_write_counters(profile, memory_writes)
                profile.depth_stage = self._compute_depth_stage(profile)
                self._save_profile(profile)

        emotion = self._detect_emotion(response, ego)
        try:
            from ukft_roleplay import to_bubbles
            spoken = response
            if spoken.startswith("[AURA]: "):
                spoken = spoken[len("[AURA]: "):]
            bubbles = to_bubbles(spoken) or [spoken]
        except Exception:
            bubbles = None
        trace = None
        if explain:
            try:
                trace = dict(getattr(ego, "last_trace", {}) or {})
            except Exception:
                trace = None
        if observer is not None:
            try:
                observer.context_resolved()
                receipts = _obs.route_evidence(selection_receipt,
                                               route_receipt)
                for receipt in receipts:
                    observer.system_evidence(receipt)
                selector = dict(selection_receipt.get("selector") or {})
                observer.winner_selected(
                    winner=str(selector.get("winner") or winner or ""),
                    confidence=float(selector.get("activation") or 0.0))
                if route_receipt.get("mouth_ran"):
                    observer.mouth_input()
                    if route_receipt.get("mouth_used"):
                        observer.grounding_accepted(source="roleplay-mouth")
                    elif route_receipt.get("mouth_produced"):
                        observer.grounding_rejected(
                            source="roleplay-mouth", reason="post-check")
                # Finding #10: report writeback only when durable
                # state changed — never a false "changed" claim.
                if memory_writes:
                    observer.writeback_changed(
                        change_summary=f"writes={len(memory_writes)}")
                observer.final_response(preview=str(response)[:120])
                observer.turn_complete()
            except Exception:
                pass
        return BrainResponse(
            response=response,
            emotion=emotion,
            memory_writes=memory_writes,
            depth_stage=profile.depth_stage,
            turn_count=profile.turn_count,
            timestamp=time.time(),
            bubbles=bubbles,
            context_trace=trace)

    def onboard(self, user_id: str, pack: str) -> UserProfile:
        """Create a user from a character pack without spending a
        turn (G4 !choose). Raises ValueError on unknown packs."""
        return self._get_or_create_profile(user_id, pack=pack)

    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile (for 'where do we stand' queries)."""
        return self._get_or_create_profile(user_id)
    
    def list_users(self) -> List[str]:
        """List all known users."""
        return self.usr.list_users()
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user and their profile."""
        with self._profile_lock:
            self._profiles.pop(user_id, None)
        return self.usr.delete_user(user_id)


# ─── Global Instance ──────────────────────────────────────────

_brain_module: Optional[BrainModule] = None
_brain_lock = threading.Lock()

def get_brain() -> BrainModule:
    global _brain_module
    with _brain_lock:
        if _brain_module is None:
            _brain_module = BrainModule()
        return _brain_module

def ask(user_id: str, text: str, **kwargs) -> BrainResponse:
    """Convenience function: ask the brain."""
    return get_brain().ask(user_id, text, **kwargs)


# ─── CLI for testing ──────────────────────────────────────────

if __name__ == "__main__":
    import sys
    brain = get_brain()
    
    if len(sys.argv) < 3:
        print("Usage: python ukft_brain_api.py <user_id> <message> [personality]")
        sys.exit(1)
    
    user_id = sys.argv[1]
    message = " ".join(sys.argv[2:])
    personality = sys.argv[3] if len(sys.argv) > 3 else "nerdy"
    
    result = brain.ask(user_id, message, personality=personality)
    print(json.dumps(asdict(result), indent=2))
