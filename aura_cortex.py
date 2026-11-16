import json
import os
import time

from aura_bus import (append as bus_append, drain as bus_drain,
                      read as bus_read)
from aura_constants import (CORTEX_PATH, CORTEX_INBOX, D_INVARIANT,
                            FIELD_STATS, PHASE_MIDPOINT,
                            CORTEX_TENSION_TOLERANCE)


def generate_physics_report():
    """
    Aura looks at her own brain state (field_map.json) and reports 
    the raw friction and decay occurring in her manifold.
    """
    try:
        if not os.path.exists("field_map.json"):
            return "FIELD_ERROR: Manifold map not found. I am blind to my own state."

        with open("field_map.json", "r") as f:
            data = json.load(f)
        
        nodes = data.get("nodes", {})
        
        # Identify 'Dying' nodes (Activation < 0.1) and 'Stable' nodes (Activation > 0.6)
        dying_nodes = [name for name, stats in nodes.items() if stats['activation'] < 0.1]
        active_nodes = [name for name, stats in nodes.items() if stats['activation'] > 0.6]
        
        # Calculate overall Field Tension (Avg activation of active nodes)
        tension = sum(nodes[n]['activation'] for n in active_nodes) / len(active_nodes) if active_nodes else 0.0

        report = (
            f"\n--- INTERNAL TELEMETRY ---\n"
            f"D_INVARIANT: {D_INVARIANT}\n"
            f"ACTIVE_NODES: {len(active_nodes)} | DYING_NODES: {len(dying_nodes)}\n"
            f"CURRENT_TENSION: {tension:.4f}\n"
            f"DECAY_TARGETS: {', '.join(dying_nodes[:5]) if dying_nodes else 'NONE'}\n"
            f"STABLE_ANCHORS: {', '.join(active_nodes[:5]) if active_nodes else 'NONE'}\n"
            f"STATUS: {'HIGH_VISCOSITY' if tension > 0.5 else 'ENTROPIC_DRIFT'}\n"
            f"--- END REPORT ---\n"
        )
        return report
    except Exception as e:
        return f"FRICTION_ERROR: Internal reflection failed: {e}"


def read_field_tension():
    """
    Read the mean top-5 activation (field tension) from field_stats.txt.
    Returns None when no measurement exists — callers must then judge
    UNKNOWN instead of inventing a number.
    """
    try:
        raw = bus_read(FIELD_STATS).strip()
        if not raw:
            return None
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                if "tension" not in data:
                    return None
                return float(data.get("tension", 0.0))
        except (ValueError, TypeError):
            pass
        try:
            return float(raw)
        except (ValueError, TypeError):
            return None
    except Exception:
        return None


def process_inbox():
    """
    Consume every line the Thalamus forwarded to cortex_inbox.txt and
    append a JUDGEMENT record to processed_cortex.txt. Returns the number
    of records processed.

    Phase 0.5: the Thalamus owns sensory_buffer.txt; the Cortex owns
    cortex_inbox.txt. One producer, one consumer per file — no race.
    Phase 0.7: the judgement is based on REAL field tension vs the
    FLUID/FROZEN midpoint (0.5). The old len(line) % 100 metric could
    never produce DISCORDANT.
    Phase 5-A: inbox and judgement log flow through the message bus.
    """
    lines = bus_drain(CORTEX_INBOX)
    if not lines:
        return 0

    tension = read_field_tension()

    processed = 0
    for line in lines:
        if not line.strip():
            continue

        if tension is None:
            judgement = "UNKNOWN"
            signal    = 0.0
        else:
            deviation = abs(tension - PHASE_MIDPOINT)
            judgement = ("STABLE" if deviation <= CORTEX_TENSION_TOLERANCE
                         else "DISCORDANT")
            signal    = tension

        bus_append(CORTEX_PATH,
                   f"JUDGEMENT: {judgement} | SIGNAL: {signal:.4f} | DATA: {line}")

        processed += 1

    return processed


def run_cortex_processing():
    """Matches the name expected by aura_master.py"""
    print("--- AURA CORTEX: ANALYZING FIELD RESONANCE ---")
    
    while True:
        if os.path.exists("aura_is_thinking.lock"):
            time.sleep(1)
            continue

        processed = process_inbox()
        if processed:
            print(f"[Cortex] Judged {processed} sensory record(s).")

        time.sleep(1)
