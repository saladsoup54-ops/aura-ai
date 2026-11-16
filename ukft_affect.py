# ukft_affect.py — AURA Affect Mapping (V7 F3)
# ==================================================
# Tone rendered from measured state — never performed feeling
# beyond measurement.  The register owns the voicebox (F1
# opener families); affect only plays it: epistemic hunger
# brightens, a warm field cools, a hot field quiets her to one
# short sentence.  No new words are ever added — the opener
# families ARE the tone, so grounding and verification are
# untouched by construction.
#
# Blindness is honest: when her state files are absent (fresh
# sandboxes, first boot) there is no tone to render and the
# register speaks in its default rotation — byte-identical to
# the pre-F3 voice.  Thresholds are borrowed from real lines:
# 0.70 is the homeostasis INHIBIT boundary, 0.50 the field's
# own FLUID/FROZEN phase boundary.
#
# No state of its own: every call re-reads the three stores,
# so there is nothing to cap, back up, or preflight.
# ==================================================

INHIBIT_TENSION = 0.70
WARM_TENSION = 0.50

FAMILIES = ("warm", "bright", "cool")


def read_state(self_path=None, stats_path=None, gaps_path=None):
    """
    Measured affect state, or None when blind.  Paths inject for
    tests; defaults read her live stores.  Never throws — a
    failed read is just another missing sense.
    """
    try:
        from aura_constants import FIELD_STATS, SELF_FILE
        from ukft_gaps import KnowledgeGaps
        from ukft_self import DriveState

        self_text = None
        try:
            from aura_bus import read as bus_read
            self_text = bus_read(self_path or SELF_FILE, default=None)
        except Exception:
            self_text = None
        stats_text = None
        try:
            from aura_bus import read as bus_read_stats
            stats_text = bus_read_stats(stats_path or FIELD_STATS,
                                        default=None)
        except Exception:
            stats_text = None
        if not self_text and not stats_text:
            # No self, no field sense: blind.  Speak plainly.
            return None
        state = {"tension": 0.0, "dominant": None, "gaps": 0}
        if stats_text:
            try:
                import json
                data = json.loads(stats_text) if stats_text.strip() \
                    else {}
                if isinstance(data, dict) and "tension" in data:
                    state["tension"] = float(data["tension"])
            except Exception:
                pass
        if self_text:
            try:
                drives = DriveState(
                    path=self_path or SELF_FILE)
                state["dominant"] = drives.dominant()
            except Exception:
                pass
        try:
            gaps = KnowledgeGaps(
                path=gaps_path) if gaps_path else KnowledgeGaps()
            top = gaps.top_gaps(3) or []
            state["gaps"] = len(top)
        except Exception:
            pass
        return state
    except Exception:
        return None


def tone_for(state):
    """
    Measured state -> (family, quiet).  family None means the
    default all-pool rotation (blind, or quiet which needs no
    opener at all).  Pure function — the gate F-B target.
    """
    if not state:
        return (None, False)
    try:
        tension = float(state.get("tension", 0.0) or 0.0)
    except Exception:
        tension = 0.0
    if tension >= INHIBIT_TENSION:
        return (None, True)
    if state.get("dominant") == "epistemic" and (state.get("gaps") or 0) > 0:
        return ("bright", False)
    if tension >= WARM_TENSION:
        return ("cool", False)
    return ("warm", False)
