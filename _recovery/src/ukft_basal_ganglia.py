# ukft_basal_ganglia.py — AURA Basal Ganglia (Phase 2-D)
# ======================================================
# Response selection by competitive inhibition.  Every response layer
# (EXECUTE sweep, SovereignVoice, vault search, field fallback, dark
# fallback) is evaluated and offered as a candidate; the basal ganglia
# selects the winner with lateral inhibition instead of a hardcoded
# if/elif waterfall.
#
#   compete()   — each candidate's salience is suppressed by the strongest
#                 rival (inhibition_beta * max(other)), the highest
#                 remaining activation wins.  Hysteresis keeps the
#                 incumbent layer when a challenger's margin is noise.
#   modulate()  — context knobs:
#                   vault_support : temporal-lobe co-occurrence boost for
#                                   the vault candidate (2-C feeds 2-D)
#                   inhibited     : homeostasis/PFC suppression of the
#                                   background candidates (field, dark)
#   select()    — modulate + compete, returns (winner, salience, activation).
#   log_decision — appends a capped decision line to basal_ganglia_log.txt
#                  so the Architect can watch selection emerge.
# ======================================================

import os
import time

from aura_constants import BASAL_GANGLIA_LOG

INHIBITION_BETA = 0.5   # lateral inhibition strength (max-rival)
HYSTERESIS      = 0.05  # challenger margin below this keeps the incumbent
MAX_SUPPORT     = 0.3   # cap on the temporal vault_support boost
MAX_LOG_LINES   = 200   # decision log cap


class BasalGanglia:
    def __init__(self, log_path=BASAL_GANGLIA_LOG,
                 inhibition_beta=INHIBITION_BETA, hysteresis=HYSTERESIS):
        self.log_path        = log_path
        self.inhibition_beta = inhibition_beta
        self.hysteresis      = hysteresis
        self.current_winner  = None

    # ── COMPETITION ────────────────────────────────────────────────
    def compete(self, candidates):
        """
        Winner-take-all on modulated saliences.
        Returns (winner, activation) or (None, 0.0) when no candidate
        survives inhibition.
        """
        scored = [(n, max(0.0, min(1.0, s))) for n, s in candidates if s > 0]
        if not scored:
            self.current_winner = None
            return None, 0.0

        activations = {}
        for name, salience in scored:
            rivals = [s2 for n2, s2 in scored if n2 != name]
            suppression = self.inhibition_beta * (max(rivals) if rivals else 0.0)
            activations[name] = salience - suppression

        best = max(scored, key=lambda t: activations[t[0]])[0]

        # Hysteresis: a challenger needs a real margin to displace the
        # incumbent layer, or selection thrashes between messages.
        if (self.current_winner in activations
                and best != self.current_winner
                and activations[best] - activations[self.current_winner]
                < self.hysteresis):
            best = self.current_winner

        if activations[best] <= 0:
            self.current_winner = None
            return None, 0.0

        self.current_winner = best
        return best, activations[best]

    # ── CONTEXT MODULATION ─────────────────────────────────────────
    def modulate(self, candidates, context):
        """
        Apply context to candidate saliences.
          vault_support — added to the vault candidate (capped MAX_SUPPORT)
          inhibited     — halves the field and dark candidates
        """
        support   = max(0.0, min(MAX_SUPPORT, context.get("vault_support", 0.0)))
        inhibited = bool(context.get("inhibited", False))

        out = []
        for name, salience in candidates:
            s = salience
            if name == "vault":
                s += support
            if inhibited and name in ("field", "dark"):
                s *= 0.5
            out.append((name, max(0.0, min(1.0, s))))
        return out

    def select(self, candidates, context=None):
        """Modulate, compete, and return (winner, salience, activation)."""
        modulated = self.modulate(candidates, context or {})
        winner, activation = self.compete(modulated)
        salience = dict(modulated).get(winner, 0.0) if winner else 0.0
        return winner, salience, activation

    # ── OBSERVABILITY ──────────────────────────────────────────────
    def log_decision(self, query, winner, candidates, context=None):
        """Append one capped decision line to the log file."""
        context = context or {}
        cand = ", ".join(f"{n}={s:.2f}" for n, s in candidates)
        line = (
            f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
            f"QUERY: '{query[:60]}' | WINNER: {winner} | "
            f"CANDIDATES: {cand} | "
            f"SUPPORT: {context.get('vault_support', 0.0):.2f} | "
            f"INHIBITED: {bool(context.get('inhibited'))}\n"
        )
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line)
            with open(self.log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            if len(lines) > MAX_LOG_LINES:
                with open(self.log_path, "w", encoding="utf-8") as f:
                    f.writelines(lines[-MAX_LOG_LINES:])
        except Exception:
            pass

    def reset(self):
        """Clear the incumbent — used by tests and on re-instantiation."""
        self.current_winner = None
