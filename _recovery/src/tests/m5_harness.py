"""M5 causal-influence harness (TEST CODE ONLY).

Proves whether a subsystem's output can change or guard Aura's
selected response — the measuring instrument for brain integration
(M5), before any rewiring (M1-M4, M13, M14, M16).

SELECTION SEAM (from current code truth):
  aura_bridge.py SovereignEgo.manifest_thought builds `candidates`
  + `context = {"vault_support": ..., "inhibited": ...}`, then
  self.ganglia.select(candidates, context) -> winner -> winner
  branch -> response. The mouth/roleplay path (aura_master.py)
  runs AFTER selection and is excluded from the causal decision.

LAW:
  - This module is imported ONLY by tests. Production never imports
    it (a suite check asserts that).
  - Every entry point here hard-refuses outside AURA_TEST_MODE=1
    with a valid temp state root. There is no live "override brain"
    backdoor: production behaviour is byte-identical with or without
    this file.
  - Evidence vocabulary (never collapsed):
      RAN / OUTPUT PRODUCED / OUTPUT USED / INFLUENCED DECISION
"""

import os

try:
    import aura_state as _st
except Exception:  # pragma: no cover - repo always on sys.path in suites
    _st = None


def require_test_env():
    """Hard gate: refuse unless running inside the declared test sandbox.

    Raises UnsafeRootError (or RuntimeError fallback) when NOT in
    test mode, when no state root is declared, or when the root/CWD
    is inside the live organism tree.
    """
    if _st is None:
        if os.environ.get("AURA_TEST_MODE") != "1":
            raise RuntimeError(
                "m5_harness refuses: not in AURA_TEST_MODE=1 "
                "(no live override exists).")
        return os.getcwd()
    if not _st.in_test_mode():
        raise _st.UnsafeRootError(
            "m5_harness refuses: AURA_TEST_MODE != 1 "
            "(no live override exists).")
    return _st.require_test_root()


def run_selection(candidates, context, log_name="m5_probe_log.txt"):
    """One deterministic selection through the REAL BasalGanglia.

    Fresh ganglia instance per call: no hysteresis carryover, so
    baseline and perturbation start from identical selector state.
    Returns (winner, salience, activation).
    """
    require_test_env()
    from ukft_basal_ganglia import BasalGanglia
    ganglia = BasalGanglia(log_path=log_name)
    return ganglia.select(list(candidates), dict(context))


def make_receipt(subsystem, ran, output_produced, output_used,
                 baseline_value, perturbed_value,
                 baseline_winner, perturbed_winner,
                 guard_triggered=False, evidence=""):
    """Structured causal receipt (telemetry about the selection path;
    never raw private reasoning)."""
    influenced = bool(
        output_used
        and (baseline_winner != perturbed_winner or guard_triggered))
    return {
        "subsystem": subsystem,
        "ran": bool(ran),
        "output_produced": bool(output_produced),
        "output_used": bool(output_used),
        "baseline_value": baseline_value,
        "perturbed_value": perturbed_value,
        "baseline_winner": baseline_winner,
        "perturbed_winner": perturbed_winner,
        "guard_triggered": bool(guard_triggered),
        "influenced_decision": influenced,
        "evidence": evidence,
    }


def causal_probe(subsystem, baseline_candidates, baseline_context,
                 perturbed_candidates, perturbed_context,
                 baseline_value=None, perturbed_value=None,
                 output_used=True, guard_triggered=False, evidence="",
                 log_base="m5_base_log.txt", log_pert="m5_pert_log.txt"):
    """Baseline vs perturbed selection with identical selector state.

    The caller keeps every other subsystem output identical; only the
    one under test differs. Returns a causal receipt.
    """
    require_test_env()
    base_winner, _, _ = run_selection(
        baseline_candidates, baseline_context, log_base)
    pert_winner, _, _ = run_selection(
        perturbed_candidates, perturbed_context, log_pert)
    return make_receipt(
        subsystem=subsystem,
        ran=True,
        output_produced=True,
        output_used=output_used,
        baseline_value=baseline_value,
        perturbed_value=perturbed_value,
        baseline_winner=base_winner,
        perturbed_winner=pert_winner,
        guard_triggered=guard_triggered,
        evidence=evidence,
    )


# Evidence states — four distinct labels, never collapsed.
RAN_ONLY = "RAN"
OUTPUT_PRODUCED = "OUTPUT PRODUCED"
OUTPUT_USED_UNPROVEN = "OUTPUT USED (NOT YET PROVEN INFLUENTIAL)"
INFLUENCED_DECISION = "INFLUENCED DECISION"


def classify(ran, output_produced, output_used, influenced_decision):
    """Map evidence flags to the single M5 status label."""
    if influenced_decision:
        return INFLUENCED_DECISION
    if output_used:
        return OUTPUT_USED_UNPROVEN
    if output_produced:
        return OUTPUT_PRODUCED
    if ran:
        return RAN_ONLY
    return "NOT RUN"
