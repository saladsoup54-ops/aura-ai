"""Observer-only telemetry emission for Cognitive Observatory.

FAIL-OPEN: emission never raises, never blocks, never changes
cognitive state. If writing fails, emission returns None silently.
Telemetry is observer-only; Aura operates identically if this
module is deleted or if every emission is disabled.

Design: event stream written to partition-isolated observer_trace/
under the active state root. Not in vault, episodes, people,
working memory, or brain files.
"""
from __future__ import annotations

import os
import time
import json
from typing import Optional, Dict, Any, List

# Fail-safe import of state root (observer must never crash brain)
try:
    import aura_state
    def _active_root():
        return aura_state.active_root()
    def _in_test():
        return aura_state.in_test_mode()
except Exception:
    def _active_root():
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    def _in_test():
        return False
ACTIVE_ROOT = None  # resolved dynamically
IN_TEST = False

# Mutable operator/test override. The environment switch is read at emission
# time so enabling/disabling telemetry never requires a process restart.
DISABLED = False


def observer_enabled() -> bool:
    """Current emission switch; observer state never enters cognition."""
    return not DISABLED and os.environ.get("AURA_OBSERVER_DISABLED", "") != "1"

# Storage sub-path: per-user partition isolation
TRACE_DIR = "observer_trace"

# Event schema fields (all events carry)
REQUIRED_EVENT_KEYS = {
    "turn_id", "user_id", "timestamp", "sequence",
    "subsystem", "event_type", "source", "destination",
    "human_summary", "advanced_raw",
}

# Event types matching cognitive boundaries (minimal, real)
EVENT_TYPES = {
    "turn_started",
    "input_received",
    "context_resolved",
    "memory_activated",
    "memory_selected",
    "memory_suppressed",
    "reasoning_output_produced",
    "reasoning_output_consumed",
    "system_output_consumed",
    "candidate_created",
    "candidate_scored",
    "candidate_inhibited",
    "winner_selected",
    "grounding_accepted",
    "grounding_rejected",
    "mouth_input",
    "final_response",
    "writeback_changed",
    "system_evidence",
    "turn_complete",
}

EVIDENCE_LEVELS = (
    "DORMANT", "RAN", "OUTPUT PRODUCED", "OUTPUT USED",
    "INFLUENCED DECISION",
)


def _safe_user_id(user_id: str) -> str:
    """Match the partition manager's filesystem-safe user key."""
    return "".join(c if c.isalnum() or c in "-_" else "_"
                   for c in str(user_id or "unknown")) or "unknown"


def _partition_dir(user_id: str) -> str:
    # Partition isolation: under <state_root>/users/<id>/observer_trace.
    # If the user partition exists, store inside it; else fallback to
    # <state_root>/observer_trace/<id> (observer-only, isolated).
    root = _active_root()
    safe_id = _safe_user_id(user_id)
    partition_path = os.path.join(root, "users", safe_id, TRACE_DIR)
    if os.path.isdir(os.path.dirname(partition_path)):
        return partition_path
    return os.path.join(root, TRACE_DIR, safe_id)


def _evidence(system: str, label: str, ran: bool = False,
              produced: bool = False, used: bool = False,
              influenced: bool = False, basis: str = "not-proven",
              source: str = "input", destination: str = "basal",
              details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Normalize one observer-only evidence receipt.

    The hierarchy is enforced here so a malformed caller cannot report USED
    without production, or influence without downstream use.
    """
    influenced = bool(influenced)
    used = bool(used or influenced)
    produced = bool(produced or used)
    ran = bool(ran or produced)
    if influenced:
        level = "INFLUENCED DECISION"
    elif used:
        level = "OUTPUT USED"
    elif produced:
        level = "OUTPUT PRODUCED"
    elif ran:
        level = "RAN"
    else:
        level = "DORMANT"
    return {
        "system": str(system),
        "label": str(label),
        "evidence_level": level,
        "ran": ran,
        "output_produced": produced,
        "output_used": used,
        "influenced_decision": influenced,
        "influence_basis": str(basis or "not-proven"),
        "source_stage": str(source),
        "destination_stage": str(destination),
        "details": dict(details or {}),
    }


def route_evidence(selection: Optional[Dict[str, Any]] = None,
                   route: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Build conservative M16 receipts from one completed roleplay turn.

    This consumes already-decided facts. It never calls cognition, reruns the
    selector, or infers influence from answer wording.
    """
    sel = dict(selection or {})
    rt = dict(route or {})
    selector = dict(sel.get("selector") or {})
    winner = str(selector.get("winner") or "")
    selector_ran = bool(selector)
    receipts: List[Dict[str, Any]] = []

    m1_in = int(sel.get("m1_input_count") or 0)
    m1_out = int(sel.get("m1_output_count") or 0)
    receipts.append(_evidence(
        "m1", "M1 relevance", selector_ran, m1_in > 0, m1_in > 0,
        basis="no-turn-counterfactual", source="memory", destination="m2",
        details={"input_count": m1_in, "output_count": m1_out}))

    m2_in = int(sel.get("m2_input_count") or 0)
    m2_out = int(sel.get("m2_output_count") or 0)
    receipts.append(_evidence(
        "m2", "M2 thread suppression", selector_ran, m2_in > 0, m2_in > 0,
        basis="no-turn-counterfactual", source="m1", destination="m4",
        details={"input_count": m2_in, "output_count": m2_out,
                 "suppressed": max(0, m2_in - m2_out)}))

    m3 = dict(sel.get("m3") or {})
    m3_ran = bool(sel.get("reasoning_attempted"))
    m3_produced = bool(m3.get("reasoning_present"))
    m3_kind = str(m3.get("reasoning_kind") or "none")
    m3_influenced = (
        (winner == "reasoning" and m3_kind in
         {"proof", "honest-gap", "belief-provisional"})
        or (winner == "vault" and
            m3_kind == "gap-yielded-to-memory")
    )
    m3_basis = "not-proven"
    if winner == "vault" and m3_kind == "gap-yielded-to-memory":
        m3_basis = "explicit-memory-exemption"
    elif m3_influenced:
        m3_basis = "selected-reasoning-candidate"
    receipts.append(_evidence(
        "m3", "M3 reasoning priority", m3_ran, m3_produced,
        m3_produced, m3_influenced, m3_basis,
        source="reasoning", destination="basal",
        details={"kind": m3_kind,
                 "priority_reason": m3.get("priority_reason")}))

    m4 = dict(sel.get("m4") or {})
    strong_context = (winner == "context" and bool(m4.get("applied"))
                      and float(m4.get("context_score") or 0.0) > 0.75)
    person_guard = bool(m4.get("voice_guard") and winner == "vault")
    owner_guard = bool(
        sel.get("m4_owner_filter_applied")
        and int(sel.get("m4_output_count") or 0)
        < int(sel.get("m4_input_count") or 0)
        and winner == "reasoning"
        and str((sel.get("m3") or {}).get("reasoning_kind")) == "honest-gap")
    m4_influenced = bool(strong_context or person_guard or owner_guard)
    m4_basis = ("m4-context-selected" if strong_context else
                "m4-current-person-guard" if person_guard or owner_guard else
                "not-proven")
    receipts.append(_evidence(
        "m4", "M4 context / current person", selector_ran, selector_ran,
        selector_ran, m4_influenced, m4_basis,
        source="conversation", destination="basal",
        details={"mode": m4.get("conversation_mode"),
                 "context_score": m4.get("context_score"),
                 "voice_guard": bool(m4.get("voice_guard")),
                 "owner_filter_applied": bool(
                     sel.get("m4_owner_filter_applied")),
                 "input_count": int(sel.get("m4_input_count") or 0),
                 "output_count": int(sel.get("m4_output_count") or 0)}))

    m13 = dict(sel.get("m13") or {})
    m13_ran = bool(m13.get("checked"))
    m13_influenced = bool(m13.get("guard_applied") and winner == "conflict")
    receipts.append(_evidence(
        "m13", "M13 contradiction gating", m13_ran, m13_ran, m13_ran,
        m13_influenced,
        "guard-selected-conflict" if m13_influenced else "not-proven",
        source="reasoning", destination="basal",
        details={"detected": bool(m13.get("contradiction_available")),
                 "query_relevant": bool(m13.get("query_relevant")),
                 "guard_applied": bool(m13.get("guard_applied")),
                 "reason": m13.get("reason")}))

    m14 = dict(sel.get("m14") or {})
    m14_ran = bool(m14.get("checked"))
    admitted = bool(m14.get("eligible") and winner == "reasoning")
    duplicate_guard = bool(m14.get("reason") == "g7-duplicate"
                           and winner == "context")
    m14_influenced = bool(admitted or duplicate_guard)
    m14_basis = ("episode-admission-selected" if admitted else
                 "g7-duplicate-guard" if duplicate_guard else
                 "not-proven")
    receipts.append(_evidence(
        "m14", "M14 episodic influence", m14_ran, m14_ran, m14_ran,
        m14_influenced, m14_basis,
        source="episodes", destination="basal",
        details={"eligible": bool(m14.get("eligible")),
                 "reason": m14.get("reason"),
                 "recall_kind": m14.get("recall_kind")}))

    restore_ran = bool(rt.get("field_restore_ran"))
    restore_count = int(rt.get("field_restore_count") or 0)
    field_used = restore_count > 0 and int(sel.get("field_active_count") or 0) > 0
    field_influenced = bool(field_used and winner == "field")
    receipts.append(_evidence(
        "old_brain_field", "Old-brain field restore", restore_ran,
        restore_count > 0, field_used, field_influenced,
        "field-selected-after-restore" if field_influenced else "not-proven",
        source="field_restore", destination="basal",
        details={"restored_nodes": restore_count,
                 "active_nodes": int(sel.get("field_active_count") or 0)}))

    hearing_ran = bool(sel.get("hearing_ran"))
    hearing_count = int(sel.get("hearing_admitted") or 0)
    receipts.append(_evidence(
        "hearing_bridge", "Pass 1 hearing writeback", hearing_ran,
        hearing_count > 0, False, False, "future-turn-only",
        source="input", destination="old_brain_field",
        details={"admitted_records": hearing_count}))

    branches = dict(sel.get("branches") or {})
    for system, label in (("people", "People branch"),
                          ("belief", "Belief branch"),
                          ("agenda", "Agenda branch"),
                          ("teach", "Teach branch")):
        produced = bool(branches.get(system))
        selected = bool(produced and winner == system)
        receipts.append(_evidence(
            system, label, selector_ran, produced, produced, False,
            "selected-but-no-dedicated-m5" if selected else "not-proven",
            source=system, destination="basal",
            details={"candidate_present": produced, "selected": selected}))

    receipts.append(_evidence(
        "basal", "Selected basal winner", selector_ran, bool(winner),
        bool(winner), bool(winner), "selected-winner",
        source="candidate_arena", destination="stance",
        details={"winner": winner, "salience": selector.get("salience"),
                 "activation": selector.get("activation")}))

    stance_ran = bool(rt.get("stance_ran"))
    stance_produced = bool(rt.get("stance_produced"))
    stance_used = bool(rt.get("stance_used"))
    receipts.append(_evidence(
        "stance", "Pass-2 cognitive stance", stance_ran, stance_produced,
        stance_used, False, "post-selection-grounding",
        source="basal", destination="mouth",
        details={"winner": winner}))

    mouth_ran = bool(rt.get("mouth_ran"))
    mouth_produced = bool(rt.get("mouth_produced"))
    mouth_used = bool(rt.get("mouth_used"))
    receipts.append(_evidence(
        "mouth", "Mouth phrasing", mouth_ran, mouth_produced, mouth_used,
        False, "final-phrasing-only",
        source="stance", destination="user",
        details={"fallback": str(rt.get("mouth_fallback") or "")}))
    return receipts


def _ensure_dir(path: str) -> bool:
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception:
        return False


class ObserverEmitter:
    """Safe emission interface. Zero side effects on cognition."""

    def __init__(self, user_id: Optional[str] = None, turn_id: Optional[str] = None):
        self.user_id = str(user_id) if user_id else "unknown"
        self.turn_id = str(turn_id) if turn_id else "0"
        self.seq = 0
        self._dir = _partition_dir(self.user_id)

    def _next_seq(self) -> int:
        self.seq += 1
        return self.seq

    def emit(self,
             event_type: str,
             subsystem: str,
             source: str,
             destination: Optional[str] = None,
             human_summary: str = "",
             advanced_raw: Optional[Dict[str, Any]] = None,
             turn_id: Optional[str] = None,
             user_id: Optional[str] = None) -> Optional[str]:
        """Write one event line. Returns event id or None on failure/disable."""
        if not observer_enabled():
            return None
        if event_type not in EVENT_TYPES:
            # Unknown event allowed (observes real architecture as-is)
            pass
        try:
            tid = turn_id if turn_id else self.turn_id
            uid = user_id if user_id else self.user_id
            seq = self._next_seq()
            ts = time.time()
            event = {
                "turn_id": str(tid),
                "user_id": str(uid),
                "timestamp": ts,
                "sequence": seq,
                "subsystem": str(subsystem),
                "event_type": str(event_type),
                "source": str(source),
                "destination": str(destination) if destination else None,
                "human_summary": str(human_summary) if human_summary else "",
                "advanced_raw": advanced_raw if advanced_raw is not None else {},
            }
            # Ensure trace dir exists (observer-only, never touches vault)
            d = _partition_dir(str(uid)) if uid != self.user_id else self._dir
            if not _ensure_dir(d):
                return None
            # Per-turn trace file (deterministic replay from recorded telem)
            filename = os.path.join(d, f"turn_{tid}.jsonl")
            with open(filename, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
                f.flush()
            # Fail-open: never raise to caller
            return f"{uid}:{tid}:{seq}"
        except Exception:
            # Telemetry failure must never stop reply, change score, etc.
            return None

    # Convenience emission at real cognitive boundaries
    def turn_start(self, user_id: str = "", turn_id: str = "") -> Optional[str]:
        return self.emit("turn_started", "master", "turn", "turn",
                         human_summary=f"Turn {turn_id or self.turn_id} started.")

    def input_received(self, text_preview: str = "", user_id: str = "", turn_id: str = "") -> Optional[str]:
        return self.emit("input_received", "input", "user", "understanding",
                         human_summary=f"Input received (preview: {text_preview[:40]}...)",
                         advanced_raw={"preview_len": len(text_preview)})

    def context_resolved(self, user_id: str = "", turn_id: str = "") -> Optional[str]:
        return self.emit("context_resolved", "context", "thread", "reasoning",
                         human_summary="Current thread / context assembled.")

    def memory_activated(self, memory_name: str = "", score: float = 0.0, user_id: str = "", turn_id: str = "") -> Optional[str]:
        return self.emit("memory_activated", "memory", "memory_field", "reasoning",
                         human_summary=f"Memory activated: {memory_name} (score {score}).",
                         advanced_raw={"memory": memory_name, "score": score})

    def memory_selected(self, memory_name: str = "", reason: str = "", user_id: str = "", turn_id: str = "") -> Optional[str]:
        return self.emit("memory_selected", "memory", "memory_field", "reasoning",
                         human_summary=f"Selected: {memory_name} — {reason}",
                         advanced_raw={"memory": memory_name, "reason": reason})

    def memory_suppressed(self, memory_name: str = "", reason: str = "", user_id: str = "", turn_id: str = "") -> Optional[str]:
        return self.emit("memory_suppressed", "memory", "memory_field", None,
                         human_summary=f"Suppressed: {memory_name} — {reason}",
                         advanced_raw={"memory": memory_name, "reason": reason})

    def reasoning_output_produced(self, source: str = "reasoning", destination: str = "decision", user_id: str = "", turn_id: str = "") -> Optional[str]:
        # Critical: emitted when reasoning PRODUCES output, separate from consumption
        return self.emit("reasoning_output_produced", "reasoning", source, destination,
                         human_summary=f"Reasoning produced output (source={source}, dest={destination}).")

    def reasoning_output_consumed(self, source: str = "reasoning", destination: str = "decision", user_id: str = "", turn_id: str = "") -> Optional[str]:
        return self.emit("reasoning_output_consumed", "reasoning", source, destination,
                         human_summary=f"Reasoning output consumed by {destination}.")

    def system_output_consumed(self, source: str = "", destination: str = "", user_id: str = "", turn_id: str = "") -> Optional[str]:
        return self.emit("system_output_consumed", "decision", source, destination,
                         human_summary=f"{source} output consumed by {destination}.")

    def candidate_created(self, candidate: str = "", score: float = 0.0, user_id: str = "", turn_id: str = "") -> Optional[str]:
        return self.emit("candidate_created", "decision", "arena", "arena",
                         human_summary=f"Candidate created: {candidate} (score {score}).",
                         advanced_raw={"candidate": candidate, "score": score})

    def candidate_scored(self, candidate: str = "", modifiers: str = "", user_id: str = "", turn_id: str = "") -> Optional[str]:
        return self.emit("candidate_scored", "decision", "arena", "arena",
                         human_summary=f"Candidate scored: {candidate} — {modifiers}.",
                         advanced_raw={"candidate": candidate, "modifiers": modifiers})

    def candidate_inhibited(self, candidate: str = "", reason: str = "", user_id: str = "", turn_id: str = "") -> Optional[str]:
        return self.emit("candidate_inhibited", "decision", "arena", None,
                         human_summary=f"Candidate inhibited: {candidate} — {reason}.",
                         advanced_raw={"candidate": candidate, "reason": reason})

    def winner_selected(self, winner: str = "", confidence: float = 0.0, user_id: str = "", turn_id: str = "") -> Optional[str]:
        return self.emit("winner_selected", "decision", "arena", "voice",
                         human_summary=f"Winner selected: {winner} (conf {confidence}).",
                         advanced_raw={"winner": winner, "confidence": confidence})

    def grounding_accepted(self, source: str = "grounding", user_id: str = "", turn_id: str = "") -> Optional[str]:
        return self.emit("grounding_accepted", "grounding", source, "voice",
                         human_summary="Grounding accepted.")

    def grounding_rejected(self, source: str = "grounding", reason: str = "", user_id: str = "", turn_id: str = "") -> Optional[str]:
        return self.emit("grounding_rejected", "grounding", source, None,
                         human_summary=f"Grounding rejected — {reason}.",
                         advanced_raw={"reason": reason})

    def mouth_input(self, user_id: str = "", turn_id: str = "") -> Optional[str]:
        return self.emit("mouth_input", "mouth", "voice", "voice",
                         human_summary="Mouth / voice input prepared.")

    def final_response(self, preview: str = "", user_id: str = "", turn_id: str = "") -> Optional[str]:
        return self.emit("final_response", "voice", "voice", "user",
                         human_summary=f"Final response (preview: {preview[:60]}...)",
                         advanced_raw={"preview_len": len(preview)})

    def writeback_changed(self, change_summary: str = "", user_id: str = "", turn_id: str = "") -> Optional[str]:
        # Writeback telemetry describes changes; does not cause them
        return self.emit("writeback_changed", "memory", "turn", "memory",
                         human_summary=f"Writeback changed: {change_summary}.",
                         advanced_raw={"summary": change_summary})

    def turn_complete(self, user_id: str = "", turn_id: str = "") -> Optional[str]:
        return self.emit("turn_complete", "master", "turn", "turn",
                          human_summary=f"Turn {turn_id or self.turn_id} complete.")

    def system_evidence(self, receipt: Dict[str, Any]) -> Optional[str]:
        """Emit one normalized M16 stage receipt."""
        raw = dict(receipt or {})
        system = str(raw.get("system") or "unknown")
        label = str(raw.get("label") or system)
        level = str(raw.get("evidence_level") or "DORMANT")
        return self.emit(
            "system_evidence", system,
            str(raw.get("source_stage") or system),
            str(raw.get("destination_stage") or "basal"),
            human_summary=f"{label}: {level}.", advanced_raw=raw)


# Global safe instance for import by cognitive modules
# Do not construct with live state; constructor is lazy/ lightweight.
def default_emitter(user_id: Optional[str] = None, turn_id: Optional[str] = None) -> ObserverEmitter:
    return ObserverEmitter(user_id=user_id, turn_id=turn_id)
